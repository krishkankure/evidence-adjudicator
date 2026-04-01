import re


class ClaimParserService:
    """Heuristic claim parser for converting user questions into normalized claims."""

    @staticmethod
    def normalize(text: str) -> tuple[str, str]:
        cleaned = " ".join(text.strip().split())
        cleaned = re.sub(r"\s*([?.!,;:])", r"\1", cleaned)
        cleaned = cleaned.strip()

        normalized = cleaned.rstrip("?.!")
        if m := re.match(r"(?i)^does\s+(.+?)\s+correlate\s+with\s+(.+)$", normalized):
            normalized = f"{m.group(1)} correlates with {m.group(2)}"
        elif m := re.match(r"(?i)^is\s+(.+?)\s+associated\s+with\s+(.+)$", normalized):
            normalized = f"{m.group(1)} is associated with {m.group(2)}"

        return cleaned, normalized
