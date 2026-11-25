"""SQLite-backed background workflow queue.
Stores application IDs, not document copies.
"""

import json
import sqlite3
import uuid

from pathlib import Path
from datetime import datetime, timezone, timedelta
from contextlib import contextmanager

DB = Path(__file__).resolve().parents[1] / 'data' / 'agent_runs.db'

STALE_AFTER_MINUTES = 15
MAX_JOB_ATTEMPTS = 2


@contextmanager
def _connect():
    """Create a database connection and always close it."""
    DB.parent.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(
        DB,
        timeout=30,
        isolation_level=None
    )
    con.row_factory = sqlite3.Row

    try:
        yield con
    finally:
        con.close()


def init_jobs():
    with _connect() as con:
        con.execute('''
            CREATE TABLE IF NOT EXISTS workflow_jobs (
                job_id TEXT PRIMARY KEY,
                application_id TEXT NOT NULL,
                status TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                result_json TEXT,
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                worker_id TEXT
            )
        ''')

        con.execute('''
            CREATE INDEX IF NOT EXISTS idx_workflow_jobs_status
            ON workflow_jobs(status, created_at)
        ''')


def enqueue_job(application_id):
    if not application_id or not str(application_id).strip():
        raise ValueError('application_id is required')

    init_jobs()
    job_id = str(uuid.uuid4())

    with _connect() as con:
        con.execute(
            '''
            INSERT INTO workflow_jobs(
                job_id, application_id, status
            )
            VALUES (?, ?, ?)
            ''',
            (job_id, str(application_id), 'queued')
        )

    return get_job(job_id)


def get_job(job_id):
    init_jobs()

    with _connect() as con:
        row = con.execute(
            'SELECT * FROM workflow_jobs WHERE job_id=?',
            (job_id,)
        ).fetchone()

    return _row(row) if row else None


def list_jobs(limit=25):
    init_jobs()

    with _connect() as con:
        rows = con.execute(
            '''
            SELECT * FROM workflow_jobs
            ORDER BY created_at DESC
            LIMIT ?
            ''',
            (int(limit),)
        ).fetchall()

    return [_row(row) for row in rows]


def _row(row):
    item = dict(row)
    item['result'] = (
        json.loads(item.pop('result_json'))
        if item.get('result_json')
        else None
    )
    return item


def claim_next_job(worker_id):
    """Atomically claim one queued job and recover stale jobs."""

    init_jobs()

    with _connect() as con:
        con.execute('BEGIN IMMEDIATE')

        stale_time = (
            datetime.now(timezone.utc)
            - timedelta(minutes=STALE_AFTER_MINUTES)
        ).strftime('%Y-%m-%d %H:%M:%S')

        con.execute(
            '''
            UPDATE workflow_jobs
            SET status = CASE
                WHEN attempts < ? THEN 'queued'
                ELSE 'failed'
            END,
            worker_id=NULL,
            error_message='Recovered stale worker lease',
            updated_at=CURRENT_TIMESTAMP
            WHERE status='running' AND updated_at < ?
            ''',
            (MAX_JOB_ATTEMPTS, stale_time)
        )

        row = con.execute(
            '''
            SELECT job_id FROM workflow_jobs
            WHERE status='queued'
            ORDER BY created_at
            LIMIT 1
            '''
        ).fetchone()

        if not row:
            con.commit()
            return None

        job_id = row['job_id']

        con.execute(
            '''
            UPDATE workflow_jobs
            SET status='running',
                attempts=attempts+1,
                worker_id=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE job_id=? AND status='queued'
            ''',
            (worker_id, job_id)
        )

        claimed = con.execute(
            'SELECT * FROM workflow_jobs WHERE job_id=?',
            (job_id,)
        ).fetchone()

        con.commit()

    return _row(claimed)


def finish_job(job_id, result):
    with _connect() as con:
        con.execute(
            '''
            UPDATE workflow_jobs
            SET status='completed',
                result_json=?,
                error_message=NULL,
                updated_at=CURRENT_TIMESTAMP
            WHERE job_id=?
            ''',
            (
                json.dumps(
                    result,
                    ensure_ascii=False,
                    default=str
                ),
                job_id
            )
        )


def fail_job(job_id, message, retry=False):
    with _connect() as con:
        row = con.execute(
            'SELECT attempts FROM workflow_jobs WHERE job_id=?',
            (job_id,)
        ).fetchone()

        if not row:
            return

        status = (
            'queued'
            if retry and row['attempts'] < MAX_JOB_ATTEMPTS
            else 'failed'
        )

        con.execute(
            '''
            UPDATE workflow_jobs
            SET status=?,
                error_message=?,
                worker_id=NULL,
                updated_at=CURRENT_TIMESTAMP
            WHERE job_id=?
            ''',
            (status, str(message)[:300], job_id)
        )