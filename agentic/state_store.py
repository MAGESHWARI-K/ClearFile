"""SQLite checkpoint store for resumable ClearFile agent runs."""
import json
import sqlite3
from contextlib import closing
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / 'data' / 'agent_runs.db'
DB.parent.mkdir(exist_ok=True)


def _connect():
    return sqlite3.connect(DB, timeout=30)


def init():
    with closing(_connect()) as connection:
        with connection:
            connection.execute(
                'CREATE TABLE IF NOT EXISTS runs ('
                'run_id TEXT PRIMARY KEY, app_id TEXT, status TEXT, '
                'state_json TEXT, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)'
            )


def checkpoint(run_id, app_id, status, state):
    init()
    with closing(_connect()) as connection:
        with connection:
            connection.execute(
                'INSERT INTO runs(run_id,app_id,status,state_json) VALUES(?,?,?,?) '
                'ON CONFLICT(run_id) DO UPDATE SET status=excluded.status, '
                'state_json=excluded.state_json, updated_at=CURRENT_TIMESTAMP',
                (run_id, app_id, status, json.dumps(state, default=str)),
            )


def load_run(run_id):
    init()
    with closing(_connect()) as connection:
        row = connection.execute(
            'SELECT run_id,app_id,status,state_json,updated_at FROM runs WHERE run_id=?',
            (run_id,),
        ).fetchone()
    if not row:
        return None
    return {
        'run_id': row[0], 'app_id': row[1], 'status': row[2],
        'state': json.loads(row[3]), 'updated_at': row[4],
    }


def recent_runs(limit=20):
    init()
    with closing(_connect()) as connection:
        rows = connection.execute(
            'SELECT run_id,app_id,status,updated_at FROM runs '
            'ORDER BY updated_at DESC LIMIT ?', (limit,),
        ).fetchall()
    return [
        {'run_id': row[0], 'app_id': row[1], 'status': row[2], 'updated_at': row[3]}
        for row in rows
    ]
