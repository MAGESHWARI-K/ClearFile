from .orchestrator import run_workflow_sync
from .telemetry import read_events
if __name__=='__main__':
    result=run_workflow_sync('CF-DEMO-001',{'payslip':{'Name':'Demo User','Monthly Salary':'50000'},'bank':{'Name':'Demo User','Monthly Salary':'48000'}},[{'field':'Name','status':'Match'},{'field':'Monthly Salary','status':'Mismatch'}],[{'field':'Monthly Salary'}])
    print('Run ID:',result['run_id'])
    print('Workflow state:',result['state'])
    print('Recent trace events:',read_events(10))
