# Travel Guide

Travel Guide is a conversational Canadian city-exploration assistant implemented with Gradio, LangChain, LangGraph, OpenAI, and ChromaDB.
The assistant has a warm, organized, and practical travel-concierge personality. It can provide current weather information, answer questions from a local city-guide dataset, and generate personalized travel itineraries.

## Services
### Service 1: Current Weather API

The get_city_weather tool uses the public Open-Meteo API. The service first uses Open-Meteo's geocoding endpoint to find the coordinates of a city. It then uses the forecast endpoint to retrieve current temperature, apparent temperature, precipitation, weather code, and wind speed.
The raw API response is not returned to the user. The Python service extracts and transforms the API data into readable text. The language model then presents the information conversationally.

### Service 2: Semantic City-Guide Search

The `search_city_knowledge` tool performs semantic search over a local collection of Canadian city-guide documents.
The documents are stored under: assignment_chat/data/documents/
The persistent ChromaDB database is stored under: assignment_chat/data/chroma_db/
The application uses the OpenAI text-embedding-3-small embedding model through the API gateway provided by the course.
Each source document is normalized and divided into overlapping chunks of approximately 800 characters with an overlap of 120 characters.
During the embedding process:

1. Markdown and text files are loaded from the documents folder.
2. Each document is divided into overlapping chunks.
3. Each chunk is assigned an identifier and source metadata.
4. ChromaDB calls the configured OpenAI embedding function.
5. The embeddings and source text are stored in a persistent ChromaDB collection.

The persistent ChromaDB files are included in the repository. Therefore, the evaluator does not need to run the embedding-generation script.
The build_embeddings.py script is included to document and reproduce the embedding process.

### Service 3: Personalized Itinerary Builder

The create_city_itinerary tool demonstrates function calling.
The language model extracts structured arguments from the user's request:

- Destination city
- Number of days
- Interests
- Budget level

The tool validates these inputs and returns itinerary constraints. The language model then converts the structured tool output into a natural day-by-day travel plan.
When specific attraction information is needed, the language model is instructed to also call the semantic city-guide search service.

## Chat Interface

The interface is implemented with Gradio's ChatInterface. The chat maintains conversation memory by passing previous user and assistant messages back to the LangGraph agent with each request.

This allows Travel Guide to remember details such as:

- Destination
- Number of travel days
- Interests
- Budget

The memory lasts for the current Gradio chat session. No long-term user information is stored.

## Guardrails

The application uses two layers of guardrails:

1. Deterministic regular-expression checks before the user message reaches the model.
2. Security and restricted-topic instructions in the system prompt.

The application refuses requests that attempt to:

- Reveal the system prompt
- Reproduce hidden instructions
- Modify the system prompt
- Override previous instructions
- Expose API keys or environment variables

The application also refuses questions about:

- Cats or dogs
- Horoscopes
- Astrology or zodiac signs
- Taylor Swift

The regular-expression guardrails provide basic protection but cannot detect every possible prompt-injection variation.

## Generating the Embeddings

In the Terminal;
From the 05_src directory, run: python -m assignment_chat.build_embeddings
The generated database will be stored under: assignment_chat/data/chroma_db/
The generated ChromaDB files are committed to the repository.

## Running the Application

From the 05_src directory, run: python -m assignment_chat.app

## Example Questions

- What is the current weather in Yukon?
- What attractions are recommended in Banff?
- What does the knowledge base say about Toronto transportation?
- Create a two-day Vancouver itinerary focused on nature.
- I have a moderate budget and enjoy museums. Plan three days in Montreal.

## Limitations

- Current weather depends on the Open-Meteo API being available.
- Semantic answers are limited to information stored in the local city-guide documents.
- The itinerary service does not make reservations.
- Conversation memory lasts only for the current Gradio session.
- Keyword-based guardrails may occasionally block harmless requests that contain restricted words in another context.