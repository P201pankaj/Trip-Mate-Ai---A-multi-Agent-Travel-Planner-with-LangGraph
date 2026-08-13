import os
import asyncio  # mluti event loop run at time
import certifi # handel windows path issues 
from dotenv import load_dotenv 
from langchain_mcp_adapters.client import MultiServerMCPClient 


#prevent to path issues
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where() 

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")  

clinet = MultiServerMCPClient(

    {

      "Tavily":{
            "transport":"streamable_http", # if you use remotserver
            "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"
            
      },


    }
      
)



#check if clinet conected to all servers
async def get_all_tools():
    tools = await clinet.get_tools()
    print("\nAvailable MCP Tools:\n")


    for tools in tools:
        print(tools.name)

# this return tavily_search tool object

tavily_serch_tools =None 
async def get_tavily_search_tool():
    global tavily_serch_tools
    if tavily_serch_tools is not None:
        return 


    tools = await clinet.get_tools()
    print("nAvailable MCP tools:")

    for tool in tools:
        print(tool.name)

    # next next tools
    tavily_serch_tools = next(
        tool
        for tool in tools
        if tool.name=="tavily_search"
    )


# this function can be use to call the tavily_serch tools whith a query in backend.py

async def tavily_mcp_search(query:str):
    await get_tavily_search_tool()
    result = await tavily_serch_tools.ainvoke(
        {
            "query": query
        }
    )
    return result
    



