from pathlib import Path
import re

from assignment_chat.semantic_search import (get_collection,)

BASE_DIR = Path(__file__).resolve().parent
DOCUMENTS_DIR = (
    BASE_DIR
    / "data"
    / "documents"
)
def split_text(
    text: str,
    chunk_size: int = 800,
    overlap: int = 120,
) -> list[str]:
    #Splits text into overlapping chunks before embeddings are created.
    if overlap >= chunk_size:
        raise ValueError(
            "Overlap must be smaller than chunk size."
        )
    normalized_text = re.sub(r"\s+"," ",text,).strip()
    if not normalized_text:
        return []

    chunks = []
    start = 0
    while start < len(
        normalized_text
    ):
        end = start + chunk_size
        chunk = normalized_text[
            start:end
        ].strip()
        if chunk:
            chunks.append(
                chunk
            )
        if end >= len(
            normalized_text
        ):
            break
        start = end - overlap
    return chunks


def get_document_files() -> list[Path]:
    #Returns all supported source files.
    files = list(DOCUMENTS_DIR.glob("*.md"))
    files.extend(DOCUMENTS_DIR.glob("*.txt"))
    return sorted(files)
def clear_collection(
    collection,
) -> None:
    # Removes existing records before rebuilding the collection.
    existing_records = collection.get()
    existing_ids = existing_records.get("ids",[],)
    if existing_ids:
        collection.delete(
            ids=existing_ids
        )

def build_embeddings() -> None:
    # Reads the city-guide documents, chunks their text, and adds them to the persistent ChromaDB collection.

    if not DOCUMENTS_DIR.exists():
        raise FileNotFoundError(
            f"Document directory does not exist: {DOCUMENTS_DIR}"
        )
    files = get_document_files()
    if not files:
        raise FileNotFoundError(
            f"No Markdown or text files were found in {DOCUMENTS_DIR}"
        )
    collection = get_collection()
    documents = []
    ids = []
    metadatas = []

    for file_path in files:
        text = file_path.read_text(
            encoding="utf-8"
        )
        chunks = split_text(
            text=text,
            chunk_size=800,
            overlap=120,
        )
        for chunk_index, chunk in enumerate(
            chunks
        ):
            document_id = (
                f"{file_path.stem}-"
                f"{chunk_index}"
            )

            ids.append(document_id)
            documents.append(chunk)
            metadatas.append(
                {
                    "source": file_path.name,
                    "city": file_path.stem.replace(
                        "_",
                        " ",
                    ).title(),
                    "chunk_index": chunk_index,
                }
            )
    if not documents:
        raise ValueError(
            "The source documents did not contain any usable text."
        )
    clear_collection(collection)
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
    )
    print(
        f"Stored {len(documents)} chunks "
        f"from {len(files)} documents."
    )
    print("Persistent ChromaDB location:")
    print(
        BASE_DIR
        / "data"
        / "chroma_db"
    )
    
if __name__ == "__main__":
    build_embeddings()