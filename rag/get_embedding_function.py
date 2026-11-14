# DEPRECATED: from langchain_community.embeddings.ollama import OllamaEmbeddings
# NEW VERSION:
from langchain_ollama import OllamaEmbeddings

def get_embedding_function():
    # nomic-embed-text is highly recommended for Ollama
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    return embeddings
