import difflib

def did_you_mean(word: str, words: list[str]) -> list[str]:
    return difflib.get_close_matches(word, words, 3, 0.6)
