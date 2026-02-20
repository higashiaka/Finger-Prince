"""
Vector DB — ChromaDB integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Provides a simple ``VectorDB`` class that manages ChromaDB collections
(one per gallery), handles upsert, and exposes semantic search.

Persistence:
    Data is stored locally in ``./chroma_db/`` (relative to CWD).
    This directory is git-ignored and can grow large.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import chromadb
from chromadb.config import Settings

from engine.embedding import EmbeddingProvider


def _post_to_document(post: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    """
    Converts a raw post dict into (id, document_text, metadata) for ChromaDB.
    The document text is what gets embedded.
    """
    post_id = str(post.get("id", ""))
    gall_id = str(post.get("gall_id", ""))

    # Combine title + body for richer semantic content
    # Also include top-level comment text (stripped of replies)
    comment_texts = " ".join(
        c.get("text", "") for c in post.get("comments", [])[:10]
    )
    document = f"{post.get('title', '')} {post.get('body', '')} {comment_texts}".strip()

    # Deterministic ID: gall_id + post_id
    chroma_id = hashlib.md5(f"{gall_id}:{post_id}".encode()).hexdigest()

    metadata: dict[str, Any] = {
        "post_id": post_id,
        "gall_id": gall_id,
        "title": post.get("title", ""),
        "author": post.get("author", ""),
        "date": str(post.get("date", "")),
        "views": int(post.get("views", 0)),
        "upvotes": int(post.get("upvotes", 0)),
        "source_url": post.get("source_url", ""),
        # Store the full body as JSON so we can return it on search
        "_body": post.get("body", ""),
        "_comments_json": json.dumps(post.get("comments", [])[:20], ensure_ascii=False),
    }

    return chroma_id, document, metadata


class VectorDB:
    """Manages per-gallery ChromaDB collections."""

    def __init__(self, persist_dir: str = "./chroma_db") -> None:
        self._client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )

    def _collection(self, gall_id: str) -> chromadb.Collection:
        """Returns (or creates) a ChromaDB collection for a gallery."""
        safe_name = f"gall_{gall_id.replace('-', '_').lower()}"
        return self._client.get_or_create_collection(
            name=safe_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_posts(
        self,
        posts: list[dict[str, Any]],
        embedding_provider: EmbeddingProvider,
    ) -> None:
        """
        Embeds and upserts a batch of post dicts.
        Groups posts by gall_id so each lands in the right collection.
        """
        # Group by gallery
        by_gall: dict[str, list[dict[str, Any]]] = {}
        for post in posts:
            gall_id = str(post.get("gall_id", "unknown"))
            by_gall.setdefault(gall_id, []).append(post)

        for gall_id, gall_posts in by_gall.items():
            collection = self._collection(gall_id)

            ids, documents, metadatas = [], [], []
            for post in gall_posts:
                cid, doc, meta = _post_to_document(post)
                ids.append(cid)
                documents.append(doc)
                metadatas.append(meta)

            # Embed in one batch
            embeddings = embedding_provider.embed(documents)

            collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )

    def search(
        self,
        query: str,
        top_k: int = 5,
        embedding_provider: EmbeddingProvider | None = None,
        gall_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Performs cosine similarity search.

        If ``gall_id`` is given, searches only that collection.
        Otherwise searches all collections and merges results.

        Returns a list of post dicts enriched with a ``score`` field (0–1).
        """
        if embedding_provider is None:
            raise ValueError("embedding_provider is required for search")

        query_embedding = embedding_provider.embed([query])[0]

        target_collections: list[chromadb.Collection]
        if gall_id:
            target_collections = [self._collection(gall_id)]
        else:
            all_colls = self._client.list_collections()
            target_collections = [
                self._client.get_collection(c.name) for c in all_colls
            ]

        if not target_collections:
            return []

        results: list[dict[str, Any]] = []
        for collection in target_collections:
            try:
                res = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=min(top_k, collection.count()),
                    include=["metadatas", "distances"],
                )
            except Exception:
                continue

            for meta, dist in zip(
                res["metadatas"][0], res["distances"][0]
            ):
                # ChromaDB cosine distance → similarity score
                score = max(0.0, 1.0 - dist)
                comments = json.loads(meta.get("_comments_json", "[]"))
                results.append({
                    "id": meta.get("post_id", ""),
                    "gall_id": meta.get("gall_id", ""),
                    "title": meta.get("title", ""),
                    "body": meta.get("_body", ""),
                    "author": meta.get("author", ""),
                    "date": meta.get("date", ""),
                    "views": meta.get("views", 0),
                    "upvotes": meta.get("upvotes", 0),
                    "score": round(score, 4),
                    "comments": comments,
                    "source_url": meta.get("source_url", ""),
                })

        # Sort by score descending, return top_k
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:top_k]

    def delete_collection(self, gall_id: str) -> None:
        """Removes a gallery collection and all its data."""
        safe_name = f"gall_{gall_id.replace('-', '_').lower()}"
        try:
            self._client.delete_collection(safe_name)
        except Exception:
            pass  # Already absent — that's fine

    def list_collections(self) -> list[str]:
        """Returns list of indexed gallery IDs."""
        return [c.name.removeprefix("gall_") for c in self._client.list_collections()]
