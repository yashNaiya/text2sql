"""Step 4: RAG example retrieval (FAISS), filtered by role.

Embeds the QUESTION only. SQL, tables and tags stay as metadata. Examples whose
SQL the role is not allowed to run are removed before they can reach the prompt,
so table/column names the role must not see never leak through few-shot examples.
"""
import json
import warnings
from pathlib import Path

import faiss
import numpy as np

from db_setup import get_full_schema
from rbac import get_permissions
from sql_guard import check

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_PATH = ROOT / "data" / "examples.json"
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class SentenceTransformerEmbedder:
    name = "sentence-transformers"

    def __init__(self, model_name: str = DEFAULT_MODEL):
        from sentence_transformers import SentenceTransformer
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def fit(self, texts):  # nothing to fit
        return self

    def encode(self, texts):
        v = self.model.encode(list(texts), normalize_embeddings=True, convert_to_numpy=True)
        return np.ascontiguousarray(v, dtype="float32")


class TfidfEmbedder:
    """Dry-run stand-in used only when the real model can't be downloaded.
    Not for reporting results: it matches words, not meaning."""
    name = "tfidf-DRYRUN"

    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)

    def fit(self, texts):
        self.vec.fit(list(texts))
        return self

    def encode(self, texts):
        return np.ascontiguousarray(self.vec.transform(list(texts)).toarray(), dtype="float32")


def make_embedder(kind: str = "st"):
    """kind: 'st' (strict), 'tfidf' (dry run), 'auto' (st, else tfidf with a warning)."""
    if kind == "tfidf":
        return TfidfEmbedder()
    if kind == "st":
        return SentenceTransformerEmbedder()
    try:
        return SentenceTransformerEmbedder()
    except Exception as e:  # noqa: BLE001
        warnings.warn(f"Could not load {DEFAULT_MODEL} ({type(e).__name__}); "
                      "falling back to TF-IDF. Results are NOT representative.")
        return TfidfEmbedder()


class ExampleRetriever:
    def __init__(self, embedder, examples_path: Path = EXAMPLES_PATH):
        self.examples = json.loads(Path(examples_path).read_text(encoding="utf-8"))
        self.embedder = embedder.fit([e["question"] for e in self.examples])
        vecs = self.embedder.encode([e["question"] for e in self.examples])
        self.index = faiss.IndexFlatIP(vecs.shape[1])  # cosine on normalised vectors
        self.index.add(vecs)
        self._full = {t: [c for c, _ in cols] for t, cols in get_full_schema().items()}
        self._allowed_cache = {}

    def _allowed_ids(self, role: str) -> set:
        if role not in self._allowed_cache:
            perms = get_permissions(role, self._full)
            self._allowed_cache[role] = {e["id"] for e in self.examples
                                         if check(e["sql"], perms, self._full).ok}
        return self._allowed_cache[role]

    def retrieve(self, question: str, role: str, k: int = 3) -> list:
        allowed = self._allowed_ids(role)
        q = self.embedder.encode([question])
        scores, idx = self.index.search(q, len(self.examples))  # tiny store: rank everything
        out = []
        for s, i in zip(scores[0], idx[0]):
            ex = self.examples[i]
            if ex["id"] in allowed:
                out.append({**ex, "score": float(s)})
                if len(out) == k:
                    break
        return out
