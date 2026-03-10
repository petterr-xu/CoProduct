def clean_text(value: str) -> str:
    return " ".join(value.strip().split())


def truncate_text(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[:limit]

