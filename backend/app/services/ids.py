from uuid import uuid4


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def initials_from_name(name: str) -> str:
    parts = [part for part in name.strip().split() if part]
    if not parts:
        return "L"
    letters = "".join(part[0] for part in parts[:3]).upper()
    return letters[:10]
