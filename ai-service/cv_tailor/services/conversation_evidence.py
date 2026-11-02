"""One bounded selection shared by generation, tools, and verification."""
LIMIT = 12_000
MARKER = "[Earlier user text truncated]\n"


def select_user_evidence(history: list[dict]) -> str:
    turns = [str(item["content"]) for item in history if item.get("role") == "user"]
    selected = []
    remaining = LIMIT
    for text in reversed(turns):
        cost = len(text) + bool(selected)
        if cost > remaining:
            if not selected and remaining > len(MARKER):
                selected.append(MARKER + text[-(remaining - len(MARKER)):])
            break
        selected.append(text)
        remaining -= cost
    return "\n".join(reversed(selected))
