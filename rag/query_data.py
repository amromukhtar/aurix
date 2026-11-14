from langchain_chroma import Chroma
from .get_embedding_function import get_embedding_function
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CHROMA_PATH = BASE_DIR / "chroma"


def query_rag(query_text: str):
    print("💭 Checking knowledge base...")
    # Prepare the DB.
    db = Chroma(
        persist_directory=str(CHROMA_PATH), embedding_function=get_embedding_function()
    )

    # Search the DB.
    results = db.similarity_search_with_score(query_text, k=5)

    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    return context_text
