# app/rag.py
from pathlib import Path
from typing import List, Tuple
import re

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# PDF loaders (try PyMuPDF first, fallback to PyPDF2)
try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None
from pypdf import PdfReader

# ---- Embeddings + Chroma setup ----
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBED = SentenceTransformer(EMBED_MODEL)

BASE_DIR = Path(__file__).resolve().parents[1]
CHROMA_DIR = str(BASE_DIR / "data" / "chroma")
DOCS_DIR = BASE_DIR / "data" / "docs"

client = chromadb.PersistentClient(path=CHROMA_DIR, settings=Settings(allow_reset=False))
collection = client.get_or_create_collection(name="docs")

# ---- Helpers ----
def _clean(t: str) -> str:
    t = t.replace("\x00", " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t

# def load_pdf(path: str) -> str:
#     reader = PdfReader(path)
#     text = ""
#     for page in reader.pages:
#         page_text = page.extract_text()
#         if page_text:
#             text += page_text + "\n"
#     return text.strip()

def load_text(path: Path) -> str:
    return _clean(path.read_text(encoding="utf-8", errors="ignore"))

def split_chunks(
    text: str,
    max_chars: int = 900,
    overlap: int = 150,
    max_chunks: int = 500
) -> List[str]:
    chunks = []
    i = 0
    L = len(text)

    while i < L and len(chunks) < max_chunks:
        end = min(i + max_chars, L)
        chunk = text[i:end].strip()
        if chunk:
            chunks.append(chunk)
        i = end - overlap if end - overlap > i else end

    return chunks


# ---- Indexing ----
def index_folder(docs_dir: Path | None = None) -> Tuple[int, int]:
    d = docs_dir or DOCS_DIR
    d.mkdir(parents=True, exist_ok=True)

    files = [
        f for f in d.rglob("*")
        if f.is_file() and f.suffix.lower() in {".txt", ".md"}
    ]

    total_files = 0
    total_chunks = 0

    for f in files:
        try:
            text = load_text(f)
            text = _clean(text)

            MAX_DOC_CHARS = 200_000  # 200k is MORE than enough

            if len(text) > MAX_DOC_CHARS:
                print(f"[trim] {f.name} from {len(text):,} → {MAX_DOC_CHARS}")
                text = text[:MAX_DOC_CHARS]


            chunks = split_chunks(text)
            if not chunks:
                print(f"[skip] no chunks created: {f.name}")
                continue

            if len(chunks) > 500:
                print(f"[warn] {f.name} produced {len(chunks)} chunks, trimming")
                chunks = chunks[:500]


            vecs = EMBED.encode(
                chunks,
                normalize_embeddings=True,
                show_progress_bar=False
            ).tolist()

            ids = [f"{f.stem}-{i}" for i in range(len(chunks))]
            metas = [
                {"source": f.name, "path": str(f), "chunk": i}
                for i in range(len(chunks))
            ]

            collection.upsert(
                documents=chunks,
                embeddings=vecs,
                metadatas=metas,
                ids=ids
            )

            total_files += 1
            total_chunks += len(chunks)

        except Exception as e:
            import traceback
            print(f"[index error] {f}")
            traceback.print_exc()

    return total_files, total_chunks


# ---- Retrieval ----
def retrieve(query: str, k: int = 4) -> List[dict]:
    qv = EMBED.encode([query], normalize_embeddings=True).tolist()
    res = collection.query(query_embeddings=qv, n_results=k, include=["documents", "metadatas", "distances"])
    docs = []
    for i in range(len(res["ids"][0])):
        docs.append({
            "text": res["documents"][0][i],
            "meta": res["metadatas"][0][i],
            "score": res["distances"][0][i]
        })
    return docs

def build_context(docs: List[dict]) -> str:
    parts = []
    for d in docs:
        src = d["meta"].get("source")
        parts.append(f"[{src}] {d['text']}")
    return "\n\n".join(parts)
