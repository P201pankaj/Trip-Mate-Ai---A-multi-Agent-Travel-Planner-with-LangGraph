from mcp.server.fastmcp import FastMCP 
import requests
import os
from dotenv import load_dotenv 

load_dotenv()

mcp = FastMCP("Wether MCP Server")

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY") 

@mcp.tools  # this use mc client know without this they local custom funons
def get_current_weather(city:str):
    response = requests.get( 

        "https://api.openweathermap.org/data/2.5/wether",

        params= {
            "q": city,
            "appid": OPENWEATHER_API_KEY,
             "units": "metric"
        }
    )




 
    data = response.json() 

    if response.status_code !=200:
        return data 


    return{
       "city":data["name"],
       "temperature_c": data["main"]["temp"],
       "feels_like_c": data["main"]["feels_like"],
       "humidity": data["main"]["humidity"],
       "condition": data["wethar"][0]["description"],
       "wind_spped":data["wind"]["speed"]

    }   

@mcp.tools 
def get_forcast(city: str):
    url =(
           "https://api.openweathermap.org/data/2.5/wether"
    )

    params= {
                "q": city,
                "appid": OPENWEATHER_API_KEY,
                 "units": "metric"
            } 

    responce =requests.get(

        url,
        params= params
    )

    data = responce.json()

    forcast =[]

    #retrun first forest entries 

    for item in data["list"][:5]:
        forcast.append(
            {
                "datetime": item["dt_text"],
                "temperature": item["main"]["temp"],
                "weather": item["weather"][0]["description"]
            }
        )
    return{
        "city": city,
        "forcast":forcast
    }

if __name__ == "__main__":
    mcp.run()

       
    


