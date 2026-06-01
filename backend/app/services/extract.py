import re

ACTION_PREFIXES = ("todo:", "action:", "fixme:", "hack:", "bug:")
CHECKBOX_PATTERN = re.compile(r"^\s*[-*]?\s*\[[ xX]\]\s*(.+)$")
NUMBERED_LIST_PATTERN = re.compile(r"^\s*\d+[.)]\s+(.+)$")
PRIORITY_PATTERN = re.compile(r"\[(?:p\d+|urgent|high|medium|low)\]", re.IGNORECASE)
MENTION_PATTERN = re.compile(r"@action\b", re.IGNORECASE)


def _clean_item(raw: str) -> str:
    return raw.strip().strip("-* ").strip()


def _normalize_for_matching(line: str) -> str:
    stripped = line.strip().lstrip("-* ").strip()
    return stripped.lower()


def _is_actionable_line(line: str) -> bool:
    normalized = _normalize_for_matching(line)
    if not normalized:
        return False

    if any(normalized.startswith(prefix) for prefix in ACTION_PREFIXES):
        return True

    if CHECKBOX_PATTERN.match(line):
        return True

    if NUMBERED_LIST_PATTERN.match(line):
        return True

    if line.rstrip().endswith("!"):
        return True

    if PRIORITY_PATTERN.search(line):
        return True

    if MENTION_PATTERN.search(line):
        return True

    return False


def extract_action_items(text: str) -> list[str]:
    results: list[str] = []
    seen: set[str] = set()

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        checkbox_match = CHECKBOX_PATTERN.match(line)
        if checkbox_match:
            candidate = _clean_item(checkbox_match.group(1))
        else:
            numbered_match = NUMBERED_LIST_PATTERN.match(line)
            if numbered_match:
                candidate = _clean_item(numbered_match.group(1))
            else:
                candidate = _clean_item(line)

        if not _is_actionable_line(line):
            continue

        key = candidate.lower()
        if key in seen:
            continue

        seen.add(key)
        results.append(candidate)

    return results
