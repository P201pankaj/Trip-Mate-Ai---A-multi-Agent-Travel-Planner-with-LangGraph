from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()


client = TavilyClient(

api_key = os.getenv("TAVILY_API_KEY")

)  

# client serch 
def tavily_search(query):
    responce = client.search(
        query= query,
        max_results= 5   # max search result 
    ) 

#clean the text data remmove meta data ander answer length
    results = []
    for i, r in enumerate(responce["results"],1):
        title = r.get("title","Unknown")
        url = r.get("url","")
        snippet = r.get("content","").strip()

        #keep only the first 300 characters to avoid wall-of text

        if len(snippet) > 300:
            snippet =snippet[:300].rsplit(" ",1)[0] +"..." 
        results.append(f"{i}. **{title}* \n {url}n {snippet}")

    return "\n\n".join(results)






















