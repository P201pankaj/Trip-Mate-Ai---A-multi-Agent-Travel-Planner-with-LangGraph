import os 
import certifi  # prevent path issues
from dotenv import load_dotenv

load_dotenv()

#prevent to path issues
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where() 

from typing import TypedDict, Annotated
import operator # combine new and old message list 
#LangGraph can use the thread_id to know which conversation/checkpoint belongs to which thread.
#identify which user ask each user have uuid 
import uuid # Universally Unique Identifier.

import psycopg  # support for postgress opetions insert,update,delete

from psycopg.rows import dict_row # allows rows to be represented more like dictionaries:

#StateGraph is used to build a stateful workflow/graph.
from langgraph.graph import StateGraph, START, END 
from langgraph.checkpoint.postgres import PostgresSaver 
from langchain_core.messages import (
   AnyMessage,
   HumanMessage,
   AIMessage,
   SystemMessage
)
from langchain_groq import ChatGroq 
from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights 

def get_database_url():
    get_database_url= os.getenv("DATABASE_URL")

    if not get_database_url:
        raise ValueError(

            "DATABASE_URL is missing. please add your rdender postggreSql external database URL to .env"
        )
# Secure Sockets Layer 
#Its purpose is to secure communication between two systems over a network.
#SSL/TLS encrypts the connection:

    '''
Python Application
        │
        │  SSL/TLS Encrypted Connection
        ▼
PostgreSQL Database

SSL/TLS encrypts the data transferred between
the Python application and PostgreSQL database.
'''

    if "sslmode=" not in get_database_url:
        separtor ="&" if "?" in get_database_url else "?"
        database_url =f"{get_database_url}{separtor}sslmode= require"

    return database_url 



GROQ_API_KEY = os.getenv("GROQ_API_KEY") 
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing. please add it to your .env file.")  


#LLM DEFINE 

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key= GROQ_API_KEY
)

# state memory
# Every node can read information from the state and return updates to the state.

class TravelState(TypedDict):

    #This stores the conversation/message history.
    #Annotated merge the message in list format 
    messages: Annotated[list[AnyMessage],operator.add]

    #This stores the user's original travel reques
    user_query: str

    #This stores the results produced by your flight search tool/agent.
    flight_results: str
    #This stores hotel search results.
    hotel_results:str

    #This stores the final travel plan generated from all the information collected by your agents.
    #The itinerary node can take information already stored in the state and ask the LLM to create one complete plan
    itinerary: str

    #how many times llm calls
    llm_calls: int   


# flight agent 

def flight_agent(state: TravelState):
    query = state["user_query"]
    flight_data = search_flights(query)

    return {
        "flight_results": flight_data,
         "message":[
             AIMessage(content="flight information fetched.")
         ],

         "llm_calls": state.get("llm_calls",0)+1


    }

# hotel agent

def hotel_agent(state: TravelState):
    query = f"Best hotels for{state['user_query']}"
    hotel_results = tavily_search(query)

    return{
        "hotel_results": hotel_results,
                 "message":[
                     AIMessage(content="hotel informations fetched.")
                 ],
        
                 "llm_calls": state.get("llm_calls",0)+1
    }

# Itinerary Agent
def Itinerary_agent(state: TravelState):
    prompt =f"""
Create a complete travel intinerary.

User query:
{
    state['user_query']
}

Flight Resultes:
{
    state['flight_results']
} 
Hotel Results:
{
    state['hotel_results']
}

Make the itinerary practical, budget-aware, and to follow
""" 
    response = llm.invoke([
        SystemMessage(content="you are an expert travel planner."),
        HumanMessage(content=prompt)
    ])

    return{

        "itinerary": response.content,
        "messages": [response], 
        "llm_calls": state.get("llm_calls",0) + 1

    } 


# final responce agent 

def final_agent(state: TravelState):
    final_prompt =f""" 
Generate the final travel responce for the user 

User Request:
{
    state["user_query"]
}

Flights:
{
    state["flight_results"]
}

Hotels:
{
    state["hotel_results"]
}

Itinerary:
{
    state["itinerary"]
}

Format the final answer beautifully using these sections:

1. Trip Summary
2. Flight Information
3. Hotel Suggestions
4. Day-by-Day Itinerary
5. Estimated Budget
6. Final Recommendations

Important:
- Be clear and practical.
- Mention that live flight API may not provide ticket prices if pricing is unavailable.
- Keep the response useful for real travel planning.
"""
    responce =llm.invoke(
        [ SystemMessage(content="you are a professional AI travel booking assistance"),
          HumanMessage(content=final_prompt)

        ]
    )

    return {
        "messages":[responce],
        "llm_calls": state.get("llm_calls",0)+1
    }  

# builde graph

graph = StateGraph(TravelState)

graph.add_node("flight_agent", flight_agent)
graph.add_node("hotel_agent",hotel_agent)
graph.add_node("itinerary_agent",Itinerary_agent)
graph.add_node("final_agent",final_agent)  

# connections 
graph.add_edge(START,"flight_agent")
graph.add_edge("flight_agent","hotel_agent")
graph.add_edge("hotel_agent","itinerary_agent")
graph.add_edge("itinerary_agent","final_agent")
graph.add_edge("final_agent", END) 



# PostgreSQL Checkpointer
# =========================
DATABASE_URL = get_database_url()

_conn = psycopg.connect(
    DATABASE_URL,
    autocommit=True,
    row_factory=dict_row
)

checkpointer = PostgresSaver(_conn)
checkpointer.setup()

travel_graph = graph.compile(checkpointer=checkpointer) 


# Function for FastAPI
# =========================

def run_travel_agent(user_input: str, thread_id: str | None = None):
    if not thread_id:
        thread_id = f"user_{uuid.uuid4().hex}"

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    result = travel_graph.invoke(
        {
            "messages": [
                HumanMessage(content=user_input)
            ],
            "user_query": user_input,
            "flight_results": "",
            "hotel_results": "",
            "itinerary": "",
            "llm_calls": 0
        },
        config=config
    )

    final_answer = result["messages"][-1].content

    return {
        "thread_id": thread_id,
        "answer": final_answer,
        "flight_results": result.get("flight_results", ""),
        "hotel_results": result.get("hotel_results", ""),
        "itinerary": result.get("itinerary", ""),
        "llm_calls": result.get("llm_calls", 0),
    }
