import sqlite3, json
from pathlib import Path
DB_PATH = Path(__file__).resolve().parents[1] / 'data' / 'clearfile.db'
DB_PATH.parent.mkdir(exist_ok=True)

def _dump(value): return json.dumps(value, ensure_ascii=False, default=str)
def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute('''CREATE TABLE IF NOT EXISTS applications (application_id TEXT PRIMARY KEY, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP, documents TEXT, extracted TEXT, findings TEXT, anomalies TEXT, memo TEXT, review_status TEXT DEFAULT 'Pending review', review_notes TEXT DEFAULT '')''')

def save_application(application_id, documents, extracted, findings, anomalies, memo):
    init_db()
    with sqlite3.connect(DB_PATH) as c:
        c.execute('''INSERT INTO applications(application_id,documents,extracted,findings,anomalies,memo) VALUES(?,?,?,?,?,?) ON CONFLICT(application_id) DO UPDATE SET updated_at=CURRENT_TIMESTAMP, documents=excluded.documents, extracted=excluded.extracted, findings=excluded.findings, anomalies=excluded.anomalies, memo=excluded.memo''', (application_id,_dump(documents),_dump(extracted),_dump(findings),_dump(anomalies),memo))

def get_all_applications():
    init_db()
    with sqlite3.connect(DB_PATH) as c:
        c.row_factory=sqlite3.Row
        rows=c.execute('SELECT * FROM applications ORDER BY updated_at DESC').fetchall()
    result=[]
    for r in rows:
        d=dict(r)
        for k in ('documents','extracted','findings','anomalies'): d[k]=json.loads(d[k] or '{}')
        result.append(d)
    return result

def get_application(app_id):
    return next((a for a in get_all_applications() if a['application_id']==app_id), None)

def save_review(app_id, status, notes):
    with sqlite3.connect(DB_PATH) as c:
        c.execute('UPDATE applications SET review_status=?, review_notes=?, updated_at=CURRENT_TIMESTAMP WHERE application_id=?',(status,notes,app_id))
