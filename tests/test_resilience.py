"""Additional reliability tests for ClearFile's local agent workflow prototype."""
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import agentic.job_queue as jq
from agentic.job_queue import enqueue_job, claim_next_job, fail_job, finish_job, get_job
from agentic.orchestrator import run_workflow_sync


class QueueReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original_db = jq.DB
        jq.DB = Path(self.temp.name) / 'queue.db'

    def tearDown(self):
        jq.DB = self.original_db
        self.temp.cleanup()

    def test_job_reaches_completed_and_persists_result(self):
        job = enqueue_job('APP-COMPLETE')
        claimed = claim_next_job('worker-a')
        self.assertEqual(claimed['status'], 'running')
        finish_job(job['job_id'], {'run_id': 'RUN-1', 'decision': 'NOT_DECIDED'})
        saved = get_job(job['job_id'])
        self.assertEqual(saved['status'], 'completed')
        self.assertEqual(saved['result']['decision'], 'NOT_DECIDED')

    def test_retry_limit_moves_job_to_failed(self):
        job = enqueue_job('APP-RETRY')
        first = claim_next_job('worker-a')
        self.assertEqual(first['attempts'], 1)
        fail_job(job['job_id'], 'temporary', retry=True)
        second = claim_next_job('worker-b')
        self.assertEqual(second['attempts'], 2)
        fail_job(job['job_id'], 'still failing', retry=True)
        self.assertEqual(get_job(job['job_id'])['status'], 'failed')

    def test_stale_running_job_is_recovered(self):
        job = enqueue_job('APP-STALE')
        claim_next_job('worker-abandoned')
        with jq._connect() as con:
            con.execute("UPDATE workflow_jobs SET updated_at='2000-01-01 00:00:00' WHERE job_id=?", (job['job_id'],))
        recovered = claim_next_job('worker-recovery')
        self.assertEqual(recovered['job_id'], job['job_id'])
        self.assertEqual(recovered['status'], 'running')
        self.assertEqual(recovered['attempts'], 2)

    def test_two_workers_cannot_claim_same_job(self):
        job = enqueue_job('APP-ATOMIC')
        barrier = threading.Barrier(3)
        claims = []
        def claim(name):
            barrier.wait()
            claims.append(claim_next_job(name))
        threads = [threading.Thread(target=claim, args=(f'w{i}',)) for i in range(2)]
        for t in threads: t.start()
        barrier.wait()
        for t in threads: t.join()
        winners = [x for x in claims if x]
        self.assertEqual(len(winners), 1)
        self.assertEqual(winners[0]['job_id'], job['job_id'])


class WorkflowReliabilityTests(unittest.TestCase):
    def test_failed_worker_does_not_block_other_workers(self):
        with patch('agentic.orchestrator.evidence_worker', side_effect=RuntimeError('controlled')):
            result = run_workflow_sync('APP-PARTIAL-FAIL', {'doc': {'Name': 'Fictional'}}, [], [])
        workers = result['state']['workers']
        self.assertEqual(workers['EvidenceWorker']['status'], 'failed')
        self.assertEqual(workers['ConsistencyWorker']['status'], 'completed')
        self.assertEqual(workers['RiskWorker']['status'], 'completed')
        self.assertEqual(result['state']['workflow_status'], 'completed_with_errors')
        self.assertEqual(result['state']['decision'], 'NOT_DECIDED')

    def test_completion_guard_and_human_gate_are_preserved(self):
        result = run_workflow_sync('APP-GATE', {}, [], [])
        state = result['state']
        self.assertEqual(len(state['workers']), 3)
        self.assertTrue(state['human_approval_required'])
        self.assertEqual(state['decision'], 'NOT_DECIDED')
        self.assertIn('All three workers', state['completion_condition'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
