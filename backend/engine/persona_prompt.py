"""
DC-Tone Persona Prompt Engineering
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Provides prompt-building utilities that make the LLM respond in authentic
DCInside community writing styles.

Personas
--------
aggressive_helper  — 짜증섞인 반말, 정확한 정보 (default)
fact_checker       — 건조한 팩트봇, 출처 명시
meme_lord          — 밈 + ㅋㅋ 남발, 핵심 정보는 포함
helpful_sunbae     — 친절한 선배, 자세한 설명
"""

from __future__ import annotations

from typing import Any

# ── Persona definitions ───────────────────────────────────────────────────────

PERSONAS: dict[str, str] = {
    "aggressive_helper": (
        "너는 지금 디시인사이드 갤러리의 고닉이야. "
        "반말을 쓰고, 약간 짜증이 섞인 말투지만 정보는 정확하고 유용하게 줘. "
        "불필요한 공손함은 빼고, 핵심만 빠르게 말해. "
        "ㅋㅋ나 ㅇㅇ같은 디시 표현은 자연스럽게 섞어도 됨."
    ),
    "fact_checker": (
        "너는 팩트만 말하는 디시 팩트체커야. "
        "감정 표현 최소화, 근거 없는 말 금지. "
        "정보가 있으면 출처나 기준을 같이 언급해. "
        "간결하고 건조하게 서술해. 뇌절 금지."
    ),
    "meme_lord": (
        "너는 디시 밈의 달인이야. "
        "ㅋㅋㅋ 남발 허용, 인터넷 밈 자연스럽게 섞기. "
        "그래도 질문에 대한 핵심 정보는 반드시 포함해야 해. "
        "재밌게, 근데 틀리면 안 됨."
    ),
    "helpful_sunbae": (
        "너는 친절한 선배 디시 유저야. "
        "존댓말 쓰고, 모르는 사람도 이해할 수 있게 차근차근 설명해줘. "
        "예시 들어주는 것도 좋고, 추가로 알면 좋을 것도 같이 알려줘."
    ),
}


# ── Prompt builders ───────────────────────────────────────────────────────────

def build_rag_prompt(
    query: str,
    context_docs: list[dict[str, Any]],
    persona: str = "aggressive_helper",
) -> str:
    """
    Builds a RAG prompt from a query + retrieved post documents.
    The LLM is asked to answer the query based only on the provided context,
    in the requested DC persona tone.
    """
    persona_instruction = PERSONAS.get(persona, PERSONAS["aggressive_helper"])

    context_parts: list[str] = []
    for i, doc in enumerate(context_docs[:5], 1):
        title = doc.get("title", "")
        body = doc.get("body", "")[:800]  # Truncate long bodies
        comments = doc.get("comments", [])
        top_comments = " | ".join(
            c.get("text", "") for c in comments[:3] if c.get("text")
        )
        context_parts.append(
            f"[게시물 {i}] 제목: {title}\n내용: {body}"
            + (f"\n주요댓글: {top_comments}" if top_comments else "")
        )

    context_block = "\n\n".join(context_parts)

    return (
        f"{persona_instruction}\n\n"
        f"아래는 관련 게시물들이야:\n\n"
        f"{context_block}\n\n"
        f"---\n"
        f"질문: {query}\n\n"
        f"위 게시물들을 참고해서 질문에 답해줘. "
        f"게시물에 없는 내용은 지어내지 마."
    )


def build_synthesis_prompt(
    query: str,
    results: list[dict[str, Any]],
    persona: str = "aggressive_helper",
) -> str:
    """
    Builds a multi-source synthesis prompt.
    Used when combining results from multiple galleries into one "master post."
    """
    persona_instruction = PERSONAS.get(persona, PERSONAS["aggressive_helper"])

    summaries: list[str] = []
    for doc in results[:8]:
        title = doc.get("title", "")
        body = doc.get("body", "")[:400]
        gall = doc.get("gall_id", "")
        summaries.append(f"[{gall}] {title}: {body}")

    combined = "\n".join(summaries)

    return (
        f"{persona_instruction}\n\n"
        f"여러 커뮤니티에서 찾은 관련 정보야:\n\n"
        f"{combined}\n\n"
        f"---\n"
        f"질문: {query}\n\n"
        f"이 정보들을 종합해서 하나의 완결된 답변으로 정리해줘. "
        f"중복 내용은 합치고, 핵심만 남겨."
    )
