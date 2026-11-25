"""Bounded async supervisor-worker workflow with durable progress checkpoints."""
import asyncio
import time
import uuid
from .state_store import checkpoint
from .telemetry import emit
from .schemas import WorkflowRequest, AgentResult

MAX_RETRIES = 2
WORKER_TIMEOUT_SECONDS = 12
MAX_CONCURRENT_WORKERS = 3
WORKER_NAMES = ('EvidenceWorker', 'ConsistencyWorker', 'RiskWorker')

async def _worker(name, request, worker_fn, run_id, shared_state, semaphore):
    async with semaphore:
        worker_started = time.perf_counter()
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                emit(run_id, name, 'worker_started', {'attempt': attempt})
                result = await asyncio.wait_for(
                    asyncio.to_thread(worker_fn, request), timeout=WORKER_TIMEOUT_SECONDS
                )
                validated = AgentResult(
                    agent=name, status='completed', attempts=attempt,
                    duration_seconds=round(time.perf_counter() - worker_started, 4), **result
                ).model_dump()
                shared_state['workers'][name] = validated
                checkpoint(run_id, request.application_id, 'running', shared_state)
                emit(run_id, name, 'worker_completed', {
                    'attempt': attempt, 'evidence_count': validated['evidence_count'],
                    'flag_count': len(validated['flags'])
                })
                return validated
            except Exception as exc:
                # Do not put document values or full exception payloads in the audit log.
                emit(run_id, name, 'worker_retry', {
                    'attempt': attempt, 'error_type': type(exc).__name__,
                    'retry_limit': MAX_RETRIES
                })
                if attempt == MAX_RETRIES:
                    failed = AgentResult(
                        agent=name, status='failed',
                        summary='Worker failed after bounded retries; manual review required.',
                        flags=[f'Worker execution failed ({type(exc).__name__}).'],
                        attempts=attempt, duration_seconds=round(time.perf_counter() - worker_started, 4)
                    ).model_dump()
                    shared_state['workers'][name] = failed
                    checkpoint(run_id, request.application_id, 'running', shared_state)
                    emit(run_id, name, 'worker_failed', {'attempts': attempt})
                    return failed
                await asyncio.sleep(0.25 * (2 ** (attempt - 1)))

def evidence_worker(req):
    docs = req.extracted
    count = sum(len(values) for values in docs.values())
    return {
        'summary': f'Extracted evidence found in {len(docs)} document(s), across {count} field values.',
        'evidence_count': count, 'flags': []
    }

def consistency_worker(req):
    mismatches = [f.get('field', 'Unknown') for f in req.findings if f.get('status') == 'Mismatch']
    missing = [f.get('field', 'Unknown') for f in req.findings if f.get('status') == 'Not Available']
    flags = [f'Mismatch: {field}' for field in mismatches]
    flags += [f'Missing evidence: {field}' for field in missing]
    return {
        'summary': f'{len(mismatches)} mismatch(es), {len(missing)} field(s) not available in every document.',
        'evidence_count': len(req.findings), 'flags': flags
    }

def risk_worker(req):
    anomalies = req.anomalies
    return {
        'summary': f'{len(anomalies)} anomaly item(s) require officer attention.',
        'evidence_count': len(anomalies),
        'flags': [f"Officer review: {item.get('field', 'Unknown')}" for item in anomalies]
    }

async def run_workflow(application_id, extracted, findings, anomalies):
    req = WorkflowRequest(
        application_id=application_id, extracted=extracted,
        findings=findings, anomalies=anomalies
    )
    run_id = str(uuid.uuid4())
    state = {
        'application_id': application_id, 'workers': {},
        'human_approval_required': True, 'decision': 'NOT_DECIDED',
        'workflow_status': 'running', 'max_concurrent_workers': MAX_CONCURRENT_WORKERS,
        'retry_limit': MAX_RETRIES, 'worker_timeout_seconds': WORKER_TIMEOUT_SECONDS
    }
    started = time.perf_counter()
    checkpoint(run_id, application_id, 'running', state)
    emit(run_id, 'Supervisor', 'workflow_started', {
        'workers': list(WORKER_NAMES), 'max_concurrency': MAX_CONCURRENT_WORKERS
    })
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_WORKERS)
    tasks = [
        _worker('EvidenceWorker', req, evidence_worker, run_id, state, semaphore),
        _worker('ConsistencyWorker', req, consistency_worker, run_id, state, semaphore),
        _worker('RiskWorker', req, risk_worker, run_id, state, semaphore),
    ]
    await asyncio.gather(*tasks, return_exceptions=True)
    # Defensive completion guard: every worker must have an explicit result.
    for name in WORKER_NAMES:
        if name not in state['workers']:
            state['workers'][name] = AgentResult(
                agent=name, status='failed',
                summary='Worker returned no result; manual review required.',
                flags=['Missing worker result.']
            ).model_dump()
    state['supervisor_summary'] = ' '.join(
        state['workers'][name].get('summary', '') for name in WORKER_NAMES
    )
    state['flags'] = [
        flag for name in WORKER_NAMES for flag in state['workers'][name].get('flags', [])
    ]
    state['failed_workers'] = [
        name for name in WORKER_NAMES if state['workers'][name]['status'] != 'completed'
    ]
    state['duration_seconds'] = round(time.perf_counter() - started, 3)
    state['llm_tokens'] = None
    state['estimated_llm_cost'] = 'Not applicable (deterministic Python workers; no LLM call in this workflow)'
    state['completion_condition'] = 'All three workers returned a validated result; failed workers remain visible.'
    state['workflow_status'] = 'completed' if not state['failed_workers'] else 'completed_with_errors'
    state['human_approval_required'] = True
    state['decision'] = 'NOT_DECIDED'
    checkpoint(run_id, application_id, state['workflow_status'], state)
    emit(run_id, 'Supervisor', 'workflow_completed', {
        'duration_seconds': state['duration_seconds'],
        'failed_workers': len(state['failed_workers']),
        'decision': 'NOT_DECIDED'
    })
    return {'run_id': run_id, 'state': state}

def run_workflow_sync(*args):
    return asyncio.run(run_workflow(*args))
