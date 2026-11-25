import unittest
import tempfile
from unittest.mock import patch
from pathlib import Path
import agentic.job_queue as job_queue
from pydantic import ValidationError
from agentic.schemas import WorkflowRequest, AgentResult
from agentic.orchestrator import run_workflow_sync
from agentic.state_store import load_run
from agentic.job_queue import enqueue_job, get_job, claim_next_job, fail_job

class AgenticWorkflowTests(unittest.TestCase):
    def test_supervisor_runs_workers_and_checkpoints(self):
        result = run_workflow_sync('TEST-001', {'payslip': {'Name': 'Demo'}}, [{'field': 'Name', 'status': 'Match'}], [])
        state = result['state']
        self.assertEqual(set(state['workers']), {'EvidenceWorker', 'ConsistencyWorker', 'RiskWorker'})
        self.assertTrue(state['human_approval_required'])
        self.assertEqual(state['decision'], 'NOT_DECIDED')
        self.assertEqual(load_run(result['run_id'])['status'], 'completed')
        self.assertEqual(state['failed_workers'], [])

    def test_mismatch_and_missing_evidence_are_flagged(self):
        findings = [
            {'field': 'Name', 'status': 'Mismatch'},
            {'field': 'IFSC', 'status': 'Not Available'}
        ]
        result = run_workflow_sync('TEST-002', {}, findings, [{'field': 'Name'}])
        flags = result['state']['flags']
        self.assertIn('Mismatch: Name', flags)
        self.assertIn('Missing evidence: IFSC', flags)
        self.assertIn('Officer review: Name', flags)

    def test_empty_application_id_is_rejected(self):
        with self.assertRaises(ValidationError):
            WorkflowRequest(application_id='', extracted={}, findings=[], anomalies=[])

    def test_agent_result_default_flags_are_independent(self):
        first = AgentResult(agent='A', status='completed', summary='ok')
        second = AgentResult(agent='B', status='completed', summary='ok')
        first.flags.append('only first')
        self.assertEqual(second.flags, [])

    def test_human_decision_never_auto_changes(self):
        result = run_workflow_sync('TEST-003', {}, [{'field': 'Salary', 'status': 'Mismatch'}], [])
        self.assertEqual(result['state']['decision'], 'NOT_DECIDED')
        self.assertTrue(result['state']['human_approval_required'])

    def test_worker_failure_is_visible_after_bounded_retries(self):
        with patch('agentic.orchestrator.evidence_worker', side_effect=RuntimeError('simulated failure')):
            result = run_workflow_sync('TEST-004', {}, [], [])
        state = result['state']
        self.assertIn('EvidenceWorker', state['failed_workers'])
        self.assertEqual(state['workers']['EvidenceWorker']['status'], 'failed')
        self.assertEqual(state['workers']['EvidenceWorker']['attempts'], 2)
        self.assertEqual(state['decision'], 'NOT_DECIDED')

    def test_worker_latency_is_recorded(self):
        result = run_workflow_sync('TEST-005', {'doc': {'Name': 'Demo'}}, [], [])
        for worker in result['state']['workers'].values():
            self.assertGreaterEqual(worker['duration_seconds'], 0)
            self.assertGreaterEqual(worker['attempts'], 1)

    def test_background_job_queue_claim_and_retry(self):
        original_db = job_queue.DB
        with tempfile.TemporaryDirectory() as temp_dir:
            job_queue.DB = Path(temp_dir) / 'queue_test.db'
            try:
                job = enqueue_job('QUEUE-TEST-001')
                self.assertEqual(job['status'], 'queued')
                claimed = claim_next_job('unit-test-worker')
                self.assertEqual(claimed['job_id'], job['job_id'])
                self.assertEqual(claimed['status'], 'running')
                fail_job(job['job_id'], 'TestFailure', retry=True)
                self.assertEqual(get_job(job['job_id'])['status'], 'queued')
            finally:
                job_queue.DB = original_db

if __name__ == '__main__':
    unittest.main(verbosity=2)
