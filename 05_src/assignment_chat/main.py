from typing import Literal
from typing_extensions import TypedDict, Annotated
import json
import os
import operator
import requests
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain_core.messages import (AnyMessage,SystemMessage,ToolMessage)
from assignment_chat.prompts import (return_instructions_root)
from assignment_chat.semantic_search import (semantic_search)
from utils.logger import get_logger
os.environ["LANGCHAIN_TRACING_V2"] = "false"

_logs = get_logger(__name__)
load_dotenv(".env")
load_dotenv(".secrets")
API_BASE = ("https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/""prod/openai/v1")

WEATHER_CODE_DESCRIPTIONS = {
    0: "clear skies",
    1: "mainly clear conditions",
    2: "partly cloudy conditions",
    3: "overcast skies",
    45: "foggy conditions",
    48: "freezing fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "heavy drizzle",
    61: "light rain",
    63: "moderate rain",
    65: "heavy rain",
    71: "light snowfall",
    73: "moderate snowfall",
    75: "heavy snowfall",
    80: "light rain showers",
    81: "moderate rain showers",
    82: "heavy rain showers",
    85: "light snow showers",
    86: "heavy snow showers",
    95: "a thunderstorm",
    96: "a thunderstorm with light hail",
    99: "a thunderstorm with heavy hail",
}

@tool
def get_city_weather(city: str) -> str:
    """Gets the current weather for a city using the Open-Meteo API. Use this tool when the user asks about current temperature, precipitation, wind, weather, or current outdoor conditions.
    Args:
        city: A city name, such as Toronto, Montreal, Vancouver, Banff or Yukon.
    """
    try:
        geocoding_response = requests.get("https://geocoding-api.open-meteo.com/v1/search",
            params={
                "name": city,
                "count": 1,
                "language": "en",
                "format": "json",
            },
            timeout=10
        )
        geocoding_response.raise_for_status()
        geocoding_data = geocoding_response.json()
        locations = geocoding_data.get("results",[])
        if not locations:
            return (
                f"I could not find a matching location for {city}. "
                "Please provide a more specific city name."
            )
        location = locations[0]

        weather_response = requests.get("https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "current": (
                    "temperature_2m,"
                    "apparent_temperature,"
                    "precipitation,"
                    "weather_code,"
                    "wind_speed_10m"
                ),
                "timezone": "auto",
            },
            timeout=10
        )
        weather_response.raise_for_status()
        weather_data = weather_response.json()
        current = weather_data.get("current",{})
        units = weather_data.get("current_units",{})
        weather_code = current.get("weather_code")
        condition = WEATHER_CODE_DESCRIPTIONS.get(
            weather_code,
            "unclassified weather conditions"
        )
        location_name = location.get("name",city)
        region = location.get("admin1","")
        country = location.get("country","")
        temperature = current.get("temperature_2m")
        temperature_unit = units.get("temperature_2m","°C")
        feels_like = current.get("apparent_temperature")
        precipitation = current.get("precipitation")
        precipitation_unit = units.get("precipitation","mm")
        wind_speed = current.get("wind_speed_10m")
        wind_unit = units.get("wind_speed_10m","km/h")
        location_parts = [part
            for part in [
                location_name,
                region,
                country
            ]
            if part
        ]
        formatted_location = ", ".join(location_parts)

        return (
            f"The current weather in {formatted_location} is "
            f"{condition}. The temperature is {temperature}"
            f"{temperature_unit} and it feels like {feels_like}"
            f"{temperature_unit}. Current precipitation is "
            f"{precipitation} {precipitation_unit}, and the wind "
            f"speed is approximately {wind_speed} {wind_unit}."
        )

    except requests.RequestException:
        _logs.exception("Open-Meteo API request failed.")

        return (
            "The weather service is temporarily unavailable. ""Please try again later.")

    except (KeyError, TypeError, ValueError):
        _logs.exception("Unexpected weather API response.")

        return (
            "The weather service returned an unexpected response, ""so I could not interpret the current conditions.")

@tool
def search_city_knowledge(
    question: str,
    number_of_results: int = 3,
) -> str:
    """Performs a semantic search over the persistent Canadian city knowledge base. Use this tool for questions about attractions, transportation, neighbourhoods, local travel tips, and information contained in the city-guide documents.
    Args:
        question: The user's complete question.
        number_of_results: The number of matching chunks to retrieve.
    """
    
    matches = semantic_search(query=question,number_of_results=number_of_results,)
    if not matches:
        return (
            "The local city-guide knowledge base does not contain ""enough information to answer that question.")
    context_sections = []
    for index, match in enumerate(matches,start=1,):
        source = match["metadata"].get("source","Unknown source",)
        context_sections.append(
            f"Result {index}\n"
            f"Source: {source}\n"
            f"Content: {match['document']}"
        )
    return "\n\n".join(context_sections)

@tool
def create_city_itinerary(
    city: str,
    number_of_days: int,
    interests: list[str],
    budget: Literal[
        "low",
        "moderate",
        "high",
    ] = "moderate",
) -> str:
    """Creates structured constraints for a personalized city itinerary. Use this tool when the user asks for an itinerary, travel plan, trip schedule, or day-by-day activity plan.
    Args:
        city: The destination city.
        number_of_days: Number of days in the trip.
        interests: Interests such as food, museums, history, or nature.
        budget: Low, moderate, or high.
    """

    if number_of_days < 1:
        return ("The itinerary must contain at least one day.")
    if number_of_days > 14:
        return ("The itinerary service supports a maximum of 14 days.")
    if not interests:
        interests = ["general sightseeing"]

    budget_guidance = {
        "low": [
            "Prioritize free or inexpensive attractions.",
            "Recommend public transportation.",
            "Suggest affordable food options.",
        ],
        "moderate": [
            "Combine free and paid attractions.",
            "Allow one notable paid activity per day.",
            "Suggest casual and mid-range dining.",
        ],
        "high": [
            "Include premium attractions where appropriate.",
            "Allow convenient transportation options.",
            "Include higher-end dining suggestions.",
        ]
    }

    result = {
        "city": city,
        "number_of_days": number_of_days,
        "interests": interests,
        "budget": budget,
        "budget_guidance": budget_guidance[budget],
        "planning_rules": [
            "Group nearby attractions on the same day.",
            "Include realistic transportation and meal time.",
            "Avoid overcrowding the schedule.",
            "Include one flexible period each day.",
            "Use semantic city-guide information when specific "
            "attractions are required.",
        ]
    }

    return json.dumps(result,indent=2)

def get_model_with_tools():
    api_gateway_key = os.getenv("API_GATEWAY_KEY")
    if not api_gateway_key:
        raise ValueError(
            "API_GATEWAY_KEY is missing from the .secrets file."
        )
    model = ChatOpenAI(
        model=os.getenv("MODEL", "gpt-4o-mini"),
        temperature=0.4,
        api_key="any value",
        base_url=API_BASE,
        default_headers={
            "x-api-key": api_gateway_key
        },
    )
    tools = [
        get_city_weather,
        search_city_knowledge,
        create_city_itinerary,
    ]

    return model.bind_tools(tools)

class MessagesState(TypedDict):
    messages: Annotated[
        list[AnyMessage],
        operator.add
    ]
    llm_calls: int

def llm_call(state: MessagesState,):
    """Allows the language model to answer directly or select a tool."""

    model_with_tools = get_model_with_tools()
    response = model_with_tools.invoke([SystemMessage(content=return_instructions_root())]+ state["messages"])

    return {"messages": [response],"llm_calls": (state.get("llm_calls",0,)+ 1)}

def tool_node(state: MessagesState,):
    """Executes each tool selected by the language model."""

    tools = [
        get_city_weather,
        search_city_knowledge,
        create_city_itinerary,
    ]
    tools_by_name = {
        current_tool.name: current_tool
        for current_tool in tools
    }
    results = []

    for tool_call in state["messages"][-1].tool_calls:
        tool_name = tool_call["name"]
        selected_tool = tools_by_name.get(tool_name)
        if selected_tool is None:
            observation = (f"Unknown tool requested: {tool_name}")
        else:
            try:
                observation = selected_tool.invoke(
                    tool_call["args"]
                )
            except Exception:
                _logs.exception(f"Tool execution failed: {tool_name}")
                observation = (f"The {tool_name} service could not ""complete the request.")

        results.append(ToolMessage(content=str(observation),tool_call_id=tool_call["id"]))

    return {"messages": results}

def should_continue(
    state: MessagesState,
) -> Literal[
    "tool_node",
    END,
]:
    """Executes tools when the last model message contains tool calls. Otherwise, ends the workflow."""

    last_message = state["messages"][-1]
    if getattr(
        last_message,
        "tool_calls",
        None,
    ):
        return "tool_node"

    return END

def get_assignment_chat_agent():
    """Builds and compiles the Assignment 2 LangGraph agent."""

    agent_builder = StateGraph(MessagesState)
    agent_builder.add_node("llm_call",llm_call)
    agent_builder.add_node("tool_node",tool_node)
    agent_builder.add_edge(START,"llm_call")
    agent_builder.add_conditional_edges("llm_call",should_continue,["tool_node",END,])
    agent_builder.add_edge("tool_node","llm_call")

    return agent_builder.compile()