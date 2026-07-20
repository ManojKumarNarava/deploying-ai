from assignment_chat.main import get_assignment_chat_agent
from langchain_core.messages import HumanMessage, AIMessage
import gradio as gr
from assignment_chat.guardrails import check_user_message
from dotenv import load_dotenv
import os

from utils.logger import get_logger

_logs = get_logger(__name__)
# load_dotenv(".env")
# load_dotenv(".secrets")

agent = get_assignment_chat_agent()

def assignment_chat(message: str, history: list[dict]) -> str:
    #Converts Gradio history into LangChain messages and invokes the Assignment Chat agent.
    guardrail_response = check_user_message(message)
    if guardrail_response:
        return guardrail_response

    langchain_messages = []
    llm_calls = 0
    _logs.debug(f"History: {history}")

    for msg in history:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "user":
            langchain_messages.append(
                HumanMessage(content=content)
            )
        elif role == "assistant":
            langchain_messages.append(
                AIMessage(content=content)
            )
            llm_calls += 1

    langchain_messages.append(HumanMessage(content=message))
    state = {
        "messages": langchain_messages,
        "llm_calls": llm_calls,
    }
    try:
        response = agent.invoke(state)

        return response["messages"][-1].content

    except Exception:
        _logs.exception("The Assignment Chat agent failed.")

        return (
            "I encountered a technical problem while processing your "
            "request. Please try again."
        )

chat = gr.ChatInterface(
    fn=assignment_chat,
    title="Travel Guide",
    description=(
        "A friendly Canadian city assistant that can check weather, "
        "search a city-guide knowledge base and create itineraries."),
    examples=[
        "What is the current weather in Toronto?",
        "What attractions are available in Montreal?",
        "Create a two-day Vancouver itinerary focused on nature.",],
)

if __name__ == "__main__":
    _logs.info(
        "Starting Assignment Chat Application..."
    )

    chat.launch()