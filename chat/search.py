import json
import re
from pathlib import Path


# Phrases that usually mean the user is asking about an older conversation,
# rather than asking for a stable personal fact.
CONVERSATION_CUES = re.compile(
    r"\b(previous|earlier|before|last time|recently|yesterday|"
    r"we discussed|we talked|talking about|discussing|mentioned|"
    r"conversation|chat|what was that|continue where|"
    r"what did we|which did we|where did we)\b",
    re.IGNORECASE,
)

STOP_WORDS = {
    "the", "and", "that", "this", "what", "which", "were", "have", "been",
    "from", "with", "about", "recently", "earlier", "before", "last", "time",
    "talking", "talked", "discussing", "discussed", "conversation", "chat",
    "did", "you", "i", "me", "my", "we", "our", "was", "are", "is", "do",
    "does", "for", "to", "of", "in", "on", "a", "an", "it", "there", "any",
}


def should_search_conversations(query: str) -> bool:
    return bool(query and CONVERSATION_CUES.search(query))


def search_conversations(folder: Path, query: str, limit: int = 5) -> list[dict]:
    """Search saved chats locally and return compact, ranked context snippets."""
    if not query or not query.strip():
        return []

    raw_tokens = re.findall(r"[a-zA-Z0-9_+#.-]{3,}", query.lower())
    tokens = {token for token in raw_tokens if token not in STOP_WORDS}
    if not tokens:
        return []

    results = []
    for path in folder.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception:
            continue

        if isinstance(data, list):
            title = path.stem
            messages = data
            updated_at = ""
        else:
            title = data.get("title") or path.stem
            messages = data.get("messages", [])
            updated_at = data.get("updated_at", "")

        title_text = str(title).lower()
        title_score = sum(3 for token in tokens if token in title_text)
        hits = []

        for index, message in enumerate(messages):
            content = message.get("content", "")
            if not isinstance(content, str) or not content.strip():
                continue

            haystack = content.lower()
            score = title_score + sum(2 for token in tokens if token in haystack)
            if score <= 0:
                continue

            # Include one neighboring message so a match retains conversational context.
            start = max(0, index - 1)
            end = min(len(messages), index + 2)
            snippet = []
            for nearby in messages[start:end]:
                nearby_content = nearby.get("content", "")
                if isinstance(nearby_content, str) and nearby_content.strip():
                    snippet.append({
                        "role": nearby.get("role", ""),
                        "content": nearby_content[:1400],
                    })

            hits.append((score, index, snippet))

        if hits:
            hits.sort(key=lambda item: (item[0], item[1]), reverse=True)
            results.append({
                "title": title,
                "updated_at": updated_at,
                "score": hits[0][0],
                "snippets": [item[2] for item in hits[:3]],
            })

    # Relevance first, then recency as a tie-breaker.
    results.sort(key=lambda item: (item["score"], item.get("updated_at", "")), reverse=True)
    return results[:limit]


def build_conversation_context(results: list[dict]) -> str:
    if not results:
        return ""

    lines = [
        "Relevant excerpts from the user's previous conversations:",
        "Use these only when they help answer the current question. Do not claim a memory if the excerpts do not support it.",
        "",
    ]

    for result in results:
        lines.append(f"Conversation: {result['title']}")
        for snippet in result["snippets"]:
            for message in snippet:
                role = message.get("role", "unknown")
                content = message.get("content", "").strip()
                lines.append(f"[{role}] {content}")
        lines.append("")

    return "\n".join(lines)
