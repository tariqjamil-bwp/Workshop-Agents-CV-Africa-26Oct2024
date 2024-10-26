from pydantic import BaseModel, Field
from typing import Union, Any, Optional, List, Dict

import requests
from sympy import sympify
import os
import json
from duckduckgo_search import DDGS
from jinja2 import Template
########################################################################################################################
# Pydantic Models

class CurrencyConversionRequest(BaseModel):
    amount: float
    source_curr: str = Field(default="USD", description="Source currency code (e.g., 'USD').")
    target_curr: str = Field(default="GBP", description="Target currency code (e.g., 'EUR').")


class WeatherRequest(BaseModel):
    location: str = Field(..., description="Location name for weather information.")


class NewsRequest(BaseModel):
    topic: str
    max_results: int = Field(default=4, description="Maximum number of news results to return.")


class ToolSpecification(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Dict[str, str]]  # A dictionary mapping parameter names to their details

########################################################################################################################

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
        result = sympify(expression)
        print(result)
        return float(result)
    except Exception as e:
        print(f"Error: {e}")
        return "NaN"

########################################################################################################################

def currency_converter(amount: float, source_curr: str = "USD", target_curr: str = "GBP") -> str:
    """
    Converts an amount from a source currency to a target currency.
    
    Args:
        amount (float): The amount in the source currency.
        source_curr (str): The source currency code (e.g., 'USD').
        target_curr (str): The target currency code (e.g., 'EUR').
    
    Returns:
        str: A formatted string with the converted amount.
    """
    print(' -> currency_converter Tool Called --\n')
    # A free API for currency conversion
    url = f"https://api.exchangerate-api.com/v4/latest/{source_curr}"
    
    response = requests.get(url)
    data = response.json()
    
    # Checking if the target currency is available
    if target_curr not in data["rates"]:
        return f"Error: Target currency '{target_curr}' not available in the exchange rates."
    
    conv = data["rates"][target_curr] * amount
    print('-> TOOL-CURRENCY_CONVERTER CALLED')
    return f'{amount:.2f} {source_curr} is equivalent to: {conv:.2f} {target_curr}'

########################################################################################################################

def ddg_search(query: str, max_results: int = 4, timeout: Optional[int] = 10) -> str:
    """
    Search the web for a query and return the results.
    
    Args:
        query (str): The query to search for.
        max_results (int): The maximum number of results to return (default=4).
        timeout (Optional[int]): Optional timeout for the request (default=10 seconds).
    
    Returns:
        str: A JSON string containing the search results.
    """
    print(' -> ddg_search Tool Called --\n')
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    ddgs = DDGS(headers=headers, timeout=timeout)
    results = ddgs.text(keywords=query, max_results=int(max_results)) 
    return json.dumps(results, indent=2)

########################################################################################################################

def get_news(topic: str, max_results: int = 4) -> str:
    """
    Search the web for the latest news based on a query and return the results.
    
    Args:
        topic (str): The query to search for news.
        max_results (int): The maximum number of news results to return (default=4).
    
    Returns:
        str: A JSON string containing the news results.
    """
    print(' -> get_news Tool Called --\n')
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    ddgs = DDGS(headers=headers, timeout=60)
    results = ddgs.news(keywords=topic, max_results=int(max_results))
    return json.dumps(results, indent=2)

########################################################################################################################

def get_weather(location: str) -> str:
    """
    Get the current weather for a specified location. This includes temperature, humidity, AQI, rain, snow, current time and data etc.
    
    Args:
        location (str): The location name for weather information.
    
    Returns:
        str: A JSON string containing the weather information.
    """
    print(' -> get_weather Tool Called --\n')
    
    if not location:
        return "Location cannot be empty. Please provide a valid location."
    
    api_key = os.environ.get("WEATHER_API_KEY")
    if not api_key:
        return "Missing API key. Please set WEATHER_API_KEY environment variable."
    
    API_params = {
        "key": api_key,
        "q": location.strip(),
        "aqi": "yes",
        "alerts": "no",
    }
    print('*')
    try:
        response = requests.get("http://api.weatherapi.com/v1/current.json", params=API_params)
        print('**')
    
        response.raise_for_status()  # Ensure valid response
    except requests.exceptions.RequestException as e:
        return f"Error fetching weather data: {str(e)}"
    
    if response.status_code != 200:
        return f"Error: Unable to fetch weather data for {location}. Status code: {response.status_code}"
    
    try:
        str_response: str = json.dumps(response.json())
        print('***')
    
    except ValueError:
        return "Error: Unable to parse weather data."
    #print(str_response)
    return str_response

########################################################################################################################

import json
from typing import List, Dict
from jinja2 import Template

def get_tool_specifications(tools: Dict[str, callable], llm) -> List[dict]:
    """
    Generate tool specifications for the provided tools and return them as JSON objects.
    """

    # Template for the tool specifications in JSON format
    body = """
    You are a helpful assistant familiar with OpenAI tool specifications, which have the following JSON format:

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

    Generate an OpenAI Tools Specification compatible JSON string for the following tool:
    Tool Name: {{ tool_name }}
    Tool Description: {{ tool_doc }}
    
    Please respond only with the JSON string, without any additional text.
    """

    # List to hold parsed JSON specifications
    spec = []

    # Iterate over each tool
    for tool_name, tool_func in tools.items():
        prompt = Template(body).render(tool_name=tool_name, tool_doc=tool_func.__doc__.strip())
        response = llm(message=prompt)
        
        # Convert the response string to a JSON object
        try:
            json_response = json.loads(response.strip())
            spec.append(json_response)  # Add JSON object to spec list
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON for tool '{tool_name}': {e}")
            continue  # Skip this tool if there's an error

    return spec

########################################################################################################################

from colorama import Fore, Style
import re
# Custom color print function
def cprint(message: str, *args, **kwargs):
    """Prints colored output based on the label followed by a colon."""
    # Define the color mapping for labels
    color_mapping = {
        "Agent": Fore.BLUE+Style.BRIGHT,
        "Thought": Fore.CYAN,
        "Action": Fore.YELLOW,
        "Pause": Fore.MAGENTA,
        "Observation": Fore.GREEN,
        "Answer": Fore.BLUE,
    }
    
    # Split the message into lines and process each line
    lines = message.splitlines()
    last_color = Style.RESET_ALL  # Start with reset color

    for line in lines:
        # Check if line has a label followed by a colon
        label_match = re.match(r"(\w+):", line)
        if label_match:
            label = label_match.group(1)
            color = color_mapping.get(label, Style.RESET_ALL)  # Get the color for the label
            last_color = color  # Update last color
            print(f"{color}{line}{Style.RESET_ALL}", *args, **kwargs)  # Print the line with the label color
        else:
            # If no label, print with the last color used
            print(f"{last_color}{line}{Style.RESET_ALL}", *args, **kwargs)


########################################################################################################################

# Example Usage:
if __name__ == "__main__":
    import os
    os.system('clear')
    # Example: Search for web results
    print(get_weather("Abuja, Nigeria"))

    search_results = ddg_search("what day is today in USA?")
    print("Search_results\n", 14 * '-')
    print(search_results)

    # Example: Search for news
    news_results = get_news("AI breakthroughs")
    print("News_results\n", 14 * '-')
    print(news_results)
    
    conversion = currency_converter(100.0, 'USD', 'EUR')
    print("Conversion:\n", conversion)

    print(calculate("sqrt(3)*exp(4)+5"))
