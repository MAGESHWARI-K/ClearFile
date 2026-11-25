"""Run persisted background workflow jobs: python -m agentic.job_worker --workers 2"""
import argparse, os, socket, threading, time
from .job_queue import claim_next_job, finish_job, fail_job
from .orchestrator import run_workflow_sync
from .telemetry import emit
from utils.storage import get_application

def worker_loop(stop_event, worker_number, poll_seconds):
    worker_id = f'{socket.gethostname()}-{os.getpid()}-{worker_number}'
    while not stop_event.is_set():
        job = claim_next_job(worker_id)
        if not job:
            stop_event.wait(poll_seconds); continue
        emit(job['job_id'], 'BackgroundQueue', 'job_claimed', {'worker_id': worker_id, 'attempt': job['attempts']})
        try:
            app = get_application(job['application_id'])
            if not app:
                raise ValueError('Application not found in local ClearFile database')
            result = run_workflow_sync(job['application_id'], app['extracted'], app['findings'], app['anomalies'])
            finish_job(job['job_id'], result)
            emit(job['job_id'], 'BackgroundQueue', 'job_completed', {'run_id': result['run_id']})
        except Exception as exc:
            fail_job(job['job_id'], type(exc).__name__, retry=True)
            emit(job['job_id'], 'BackgroundQueue', 'job_failed', {'error_type': type(exc).__name__})

def main():
    parser = argparse.ArgumentParser(description='ClearFile background workflow worker')
    parser.add_argument('--workers', type=int, default=1, choices=range(1, 5))
    parser.add_argument('--poll', type=float, default=2.0)
    parser.add_argument('--once', action='store_true', help='Process at most one job and exit')
    args = parser.parse_args()
    if args.once:
        stop = threading.Event(); worker_loop_once(stop, 1); return
    stop = threading.Event(); threads=[]
    for number in range(1, args.workers + 1):
        thread = threading.Thread(target=worker_loop, args=(stop, number, args.poll), daemon=True)
        thread.start(); threads.append(thread)
    print(f'ClearFile queue worker running ({args.workers} worker(s)). Press Ctrl+C to stop.')
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        stop.set()
        for thread in threads: thread.join(timeout=5)
        print('Worker stopped safely.')

def worker_loop_once(stop, number):
    worker_id = f'{socket.gethostname()}-{os.getpid()}-{number}'
    job = claim_next_job(worker_id)
    if not job:
        print('No queued jobs.'); return
    try:
        app = get_application(job['application_id'])
        if not app: raise ValueError('Application not found')
        result = run_workflow_sync(job['application_id'], app['extracted'], app['findings'], app['anomalies'])
        finish_job(job['job_id'], result); print('Completed job:', job['job_id'])
    except Exception as exc:
        fail_job(job['job_id'], type(exc).__name__, retry=True); print('Job failed:', type(exc).__name__)

if __name__ == '__main__': main()
