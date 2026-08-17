import os 
import re 
import sys
import certifi
import airportsdata
import pycountry
import requests
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient 

load_dotenv()
#prevent to path issues
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
AVIATIONSTACCK_API_KEY =os.getenv("AVIATIONSTACCK_API_KEY") 
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY") 

clinet = MultiServerMCPClient(

    {

      "Tavily":{
            "transport":"streamable_http", # if you use remotserver
            "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"
            
        },

        "aviationstack": {
        "transport": "stdio",
        "command": sys.executable,
        "args": [
        "-m", "uv", "tool", "run", "--python", "3.13",
        "--with", "mcp==1.28.1", "aviationstack-mcp"
    ],
    "env": {
        "AVIATION_STACK_API_KEY": AVIATIONSTACCK_API_KEY
    }
    }
    }
    
      
) 


#check if clinet conected to all servers
async def get_all_tools():
    tools = await clinet.get_tools()
    print("\nAvailable MCP Tools:\n")


    for tools in tools:
        print(tools.name)

#################################################################
# Tavily and Aviations tools    this is filer exactly which tools use
################################################################## 

search_tools =None 
aviations_tools ={}
async def intialize_mcp():
    global search_tools
    global aviations_tools 


    if search_tools is not None and aviations_tools:
        return

    tools = await clinet.get_tools()

    print("\n Available MCP tools:\n")

    for tool in tools:
        print(tool.name) 

    search_tools = next(

        tool 
        for tool in tools 
        if tool.name =="tavily_search"

        )
    avilable_tools ={

        tool.name: tool
        for tool in tools
        if tool.name !="tavily_serach"
    } 


# real time updated data  give this
async def tavily_mcp_search(query:str):
    await intialize_mcp()
    result = await search_tools.ainvoke(
        {
            "query": query
        }
    )
    return result


# for aviations stack 

async def aviations_mcp_call(
        tool_name: str,
        tool_args: dict = None

):
        tools = await clinet.get_tools()

        tool = next(
             t for t in tools
             if t.name ==tool_name
        )

        result = await tool.ainvoke(
             tool_args or {}

        )

        return result

