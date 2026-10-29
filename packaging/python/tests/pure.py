"""The same functions in pure Python: what the test compares with and the benchmark times."""


def distance(a, b):
    row = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        diag, row[0] = row[0], i
        for j in range(1, len(b) + 1):
            up = row[j]
            best = diag + (a[i - 1] != b[j - 1])
            if up + 1 < best: best = up + 1
            if row[j - 1] + 1 < best: best = row[j - 1] + 1
            row[j] = best
            diag = up
    return row[len(b)]


def closest(word, words):
    if not words: return None
    best, best_d = 0, None
    for i, w in enumerate(words):
        d = distance(word, w)
        if best_d is None or d < best_d: best, best_d = i, d
    return words[best]
