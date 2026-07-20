from pathlib import Path
import os
import chromadb
from chromadb.utils.embedding_functions import (OpenAIEmbeddingFunction)
from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv(".secrets")

BASE_DIR = Path(__file__).resolve().parent
CHROMA_PATH = (BASE_DIR/"data"/"chroma_db")
COLLECTION_NAME = ("canadian_city_guides")
EMBEDDING_MODEL = ("text-embedding-3-small")
API_BASE = ("https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/""prod/openai/v1")

def get_embedding_function():
    #Creates the ChromaDB OpenAI embedding function.
    api_gateway_key = os.getenv("API_GATEWAY_KEY")
    if not api_gateway_key:
        raise ValueError(
            "API_GATEWAY_KEY is missing. Add it to the .secrets file."
        )
    return OpenAIEmbeddingFunction(
        model_name=EMBEDDING_MODEL,
        api_key="any value",
        api_base=API_BASE,
        default_headers={"x-api-key": api_gateway_key}
    )

def get_chroma_client():
    #Creates a file-persistent ChromaDB client.
    CHROMA_PATH.mkdir(parents=True,exist_ok=True,)
    return chromadb.PersistentClient(path=str(CHROMA_PATH))

def get_collection():
    #Gets or creates the persistent Canadian city-guide collection.
    chroma_client = get_chroma_client()
    return chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=get_embedding_function()
    )

def semantic_search(
    query: str,
    number_of_results: int = 3,
) -> list[dict]:
    #Generates an embedding for the user's query through the collection's OpenAI embedding function and performs similarity search in the persistent ChromaDB collection.
    collection = get_collection()
    collection_size = collection.count()
    if collection_size == 0:
        return []
    safe_result_count = min(max(number_of_results,1),
        collection_size
    )

    results = collection.query(
        query_texts=[query],
        n_results=safe_result_count,
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    documents = results.get("documents",[[]],)[0]
    metadatas = results.get("metadatas",[[]],)[0]
    distances = results.get("distances",[[]],)[0]
    matches = []
    
    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances,
    ):
        matches.append(
            {
                "document": document,
                "metadata": metadata or {},
                "distance": distance,
            }
        )

    return matches