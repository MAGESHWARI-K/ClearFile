"""MCP stdio client for discovering and invoking the two ClearFile tools.
Run: python -m mcp_tools.client CF-DEMO-001
"""
import asyncio,sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
async def main(app_id):
    server=StdioServerParameters(command=sys.executable,args=[str(Path(__file__).with_name('server.py'))])
    async with stdio_client(server) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            tools=await session.list_tools()
            print('Discovered MCP tools:',[t.name for t in tools.tools])
            for name in ('get_application_summary','list_field_findings'):
                result=await session.call_tool(name,{'application_id':app_id})
                print(f'\n{name}:')
                for item in result.content: print(getattr(item,'text',str(item)))
if __name__=='__main__':asyncio.run(main(sys.argv[1] if len(sys.argv)>1 else ''))
