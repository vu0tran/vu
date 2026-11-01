"""A "did you mean?" helper, as CLIs write it: Python's difflib.get_close_matches with type hints."""
import difflib


def close_matches(word: str, possibilities: list[str], n: int = 3, cutoff: float = 0.6) -> list[str]:
    return difflib.get_close_matches(word, possibilities, n, cutoff)
