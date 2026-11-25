"""MCP server exposing two safe, read-only ClearFile evidence tools."""
from mcp.server.fastmcp import FastMCP
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from utils.storage import get_application
mcp=FastMCP('ClearFile Evidence Tools')
@mcp.tool()
def get_application_summary(application_id: str) -> dict:
    """Return counts and officer status for a saved fictional/demo application."""
    app=get_application(application_id)
    if not app:return {'found':False,'message':'Application not found'}
    return {'found':True,'application_id':app['application_id'],'document_count':len(app['documents']),'field_count':len(app['findings']),'anomaly_count':len(app['anomalies']),'review_status':app['review_status']}
@mcp.tool()
def list_field_findings(application_id: str) -> list:
    """Return field comparison statuses; does not approve or reject applications."""
    app=get_application(application_id)
    if not app:return []
    return [{'field':x.get('field'),'status':x.get('status'),'missing_documents':x.get('missing_documents',[])} for x in app['findings']]
if __name__=='__main__':mcp.run()
