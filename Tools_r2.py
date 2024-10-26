
from ast import Dict
import requests
from bs4 import BeautifulSoup
#from dotenv import load_dotenv
#x = load_dotenv()
#print("Environment variables loaded successfully") if x else print("Error: Failed to load environment variables.")
###################################################################################################################
from sympy import sympify  # pip install sympy
from typing import Union

def calculate(expression: str) -> Union[float, str]:
    """
    Evaluates a mathematical expression using sympy and returns the result as a float.
    
    Args:
        expression (str): A string representing a mathematical expression.
    
    Returns:
        Union[float, str]: Result of the evaluation as a float, or "NaN" if an error occurs.
    """
    print(' -> calculate Tool Called --\n')
    try:
        # sympify safely converts the string expression to a SymPy expression
        result = sympify(expression)  # evalf() ensures a floating-point result
        return float(result)
    except Exception as e:
        print(f"Error: {e}")
        return "NaN"

###################################################################################################################
import requests
from typing import Any

def currency_converter(amount:Any, source_curr:str="USD", target_curr:str="GBP"):
    """
    Converts an amount from a source currency to a target currency.
    :param amount: The amount in the source currency.
    :param source_curr: The source currency code (e.g., 'USD').
    :param target_curr: The target currency code (e.g., 'EUR').
    :return: A formatted string with the converted amount.
    '''Example: currency_converter(100, 'USD', 'EUR')
    '100.00 USD is equivalent to: 80.00 EUR' '''
    """
    print(' -> currency_converter Tool Called --\n')
    # A free API for currency conversion
    url = f"https://api.exchangerate-api.com/v4/latest/{source_curr}"
    
    response = requests.get(url)
    data = response.json()
    
    # Checking if the target currency is available
    if target_curr not in data["rates"]:
        return f"Error: Target currency '{target_curr}' not available in the exchange rates."
    amount = float(amount)
    # Calculating the conversion
    conv = data["rates"][target_curr] * amount

    print('-> TOOL-CURRENCY_CONVERTER CALLED')
    return conv
    #return f'{amount:.2f} {source_curr} is equivalent to: {conv:.2f} {target_curr}'
####################################################################################################################
import json
from duckduckgo_search import DDGS
from typing import Optional, Any
# Default headers for requests
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# DuckDuckGo search function
def ddg_search(query: str, max_results = "4", headers: Optional[Any] = None, timeout: Optional[int] = 10) -> str:
    """
    Search the web for a query and return the results.
    :param query: The query to search for.
    :param max_results: The maximum number of results to return (default=10).
    :param headers: Optional headers for the request. If not provided, defaults to DEFAULT_HEADERS.
    :param timeout: Optional timeout for the request (default=10 seconds).
    :return: A JSON string containing the search results.
    """
    print(' -> ddg_search Tool Called --\n')
    headers = headers or DEFAULT_HEADERS
    ddgs = DDGS(headers=headers, timeout=timeout)
    results = ddgs.text(keywords=query, max_results=int(max_results)) 
    return json.dumps(results, indent=2)
####################################################################################################################
# DuckDuckGo news function
def get_news(topic: str, max_results = "4") -> str:
    """
    Search the web for the latest news based on a query and return the results.
    :param topic: The query to search for news.
    :param max_results: The maximum number of news results to return (default=10).
    :return: A JSON string containing the news results.
    """
    print(' -> get_news Tool Called --\n')
    headers = DEFAULT_HEADERS
    ddgs = DDGS(headers=headers, timeout=60)
    results = ddgs.news(keywords=topic, max_results=int(max_results))
    return json.dumps(results, indent=2)
####################################################################################################################
import os
import requests
from json import dumps

def get_weather(location: str) -> str:
    """Get the current weather (Temperature, AQI, Humidity, current Date & Time, rain, snow, etc) for a specified location.
    :param location: The location name for weather information.
    :return: A JSON string containing the weather information.
    """
    print(' -> get_weather Tool Called --\n')
    #print(location, type(location))
    
    if not location:
        return "Location cannot be empty. Please provide a valid location."
    
    api_key = os.environ.get("WEATHER_API_KEY")
    if not api_key:
        return "Missing API key. Please set WEATHER_API_KEY environment variable."
    
    API_params = {
        "key": api_key,
        "q": location,
        "aqi": "yes",
        "alerts": "no",
    }
    
    try:
        response = requests.get(
            "http://api.weatherapi.com/v1/current.json",
            params=API_params
        )
        response.raise_for_status()  # Ensure valid response
    except requests.exceptions.RequestException as e:
        return f"Error fetching weather data: {str(e)}"
    
    if response.status_code != 200:
        return f"Error: Unable to fetch weather data for {location}. Status code: {response.status_code}"
    
    try:
        str_response: str = dumps(response.json())
    except ValueError:
        return "Error: Unable to parse weather data."
    #print(str_response)
    return str_response

####################################################################################################################
from jinja2 import Template
def get_tool_specifications(tools: dict, llm):
    body='''
    You are a helpful assistant. I will give you the Python function definition, and your task is to extract key information (function name, description, parameters, and parameter types) and generate a tool specification for it. The tool specification should follow this format:

    {
    "type": "function",
    "function": {
        "name": "<function_name>",
        "description": "<function_description>",
        "parameters": {
        "type": "object",
        "properties": {
            "<parameter_name>": {
            "type": "<parameter_type>",
            "description": "<parameter_description>"
            }
        },
        "required": ["<parameter_name>"]
        }
    }
    }

    Generate a list of tool specifictaion(s) for the following:
    Tool Name: {{ tool_name }}:
    Tool Description: {{ tool_func.__doc__.strip() }}
    DO NOT CREATE ANY EXTRA INFORMATION.
    '''
    spec = []
    for tool in tools:
        prompt =  Template(body).render(tools=tools)
        resp=llm(message=prompt)
        spec.append(resp)
    return spec


####################################################################################################################

# Example Usage:
if __name__ == "__main__":
    import os
    os.system('clear')
    # Example: Search for web results
    print(get_weather("Abuja, Nigeria"))

    search_results = ddg_search("what daye is today in USA?")
    print("Search_results\n",14*'-')
    print(search_results)

    # Example: Search for news
    news_results= get_news("AI breakthroughs")
    print("News_results\n",14*'-')
    print(news_results)
    
    conversion =  currency_converter(100, 'USD', 'EUR')
    print("Conversion:\n",conversion)
    
