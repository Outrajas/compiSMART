from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.constants import CHUNK_SIZE, CHUNK_OVERLAP
from app.core.logger import logger

# Load model once (singleton)
_model = None

def get_embedding_model():
    global _model
    if _model is None:
        logger.info("Loading embedding model BAAI/bge-small-en-v1.5")
        _model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    return _model

def generate_embedding(text: str) -> list[float]:
    """Convert text to a vector (384 dimensions)."""
    model = get_embedding_model()
    embedding = model.encode(text, normalize_embeddings=True).tolist()
    return embedding

def chunk_transcript(transcript: str) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    texts = splitter.split_text(transcript)
    chunks = [{"chunk_id": i, "text": text} for i, text in enumerate(texts)]
    return chunks