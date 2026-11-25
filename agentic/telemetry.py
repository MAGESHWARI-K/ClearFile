"""Structured local event log and approximate usage telemetry."""
import json, logging, time
from pathlib import Path
LOG=Path(__file__).resolve().parents[1]/'data'/'agent_workflow.jsonl'
LOG.parent.mkdir(exist_ok=True)
def emit(run_id, agent, event, details=None):
    row={'timestamp':time.strftime('%Y-%m-%dT%H:%M:%S'),'run_id':run_id,'agent':agent,'event':event,'details':details or {}}
    with LOG.open('a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False,default=str)+'\n')
    return row
def read_events(limit=100):
    if not LOG.exists():return []
    return [json.loads(x) for x in LOG.read_text(encoding='utf-8').splitlines()[-limit:] if x.strip()]
