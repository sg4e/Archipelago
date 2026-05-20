from __future__ import annotations


def parse_ping_lines(contents: str, already_registered: set[str] | None = None) -> list[str]:
    already_registered = {item.casefold() for item in (already_registered or set())}
    seen: set[str] = set()
    pings: list[str] = []
    for raw_line in contents.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        if line.startswith("\\#"):
            line = line[1:]
        folded = line.casefold()
        if folded in seen or folded in already_registered:
            continue
        seen.add(folded)
        pings.append(line)
    return sorted(pings, key=str.casefold)

