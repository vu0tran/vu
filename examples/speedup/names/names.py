"""Fuzzy name matching with jellyfish's pure-Python functions (jellyfish 1.3.0, _jellyfish.py, MIT
license, (c) 2015 James Turk: LICENSE.jellyfish), as they are, with type hints added and the
deprecation warning taken out; and closest_names, which uses them the way record-matching code does."""
from collections import defaultdict


def _jaro_winkler(s1, s2, long_tolerance, winklerize):
    s1_len = len(s1)
    s2_len = len(s2)

    if not s1_len or not s2_len:
        return 0.0

    min_len = min(s1_len, s2_len)
    search_range = max(s1_len, s2_len)
    search_range = (search_range // 2) - 1
    if search_range < 0:
        search_range = 0

    s1_flags = [False] * s1_len
    s2_flags = [False] * s2_len

    # looking only within search range, count & flag matched pairs
    common_chars = 0
    for i, s1_ch in enumerate(s1):
        low = max(0, i - search_range)
        hi = min(i + search_range, s2_len - 1)
        for j in range(low, hi + 1):
            if not s2_flags[j] and s2[j] == s1_ch:
                s1_flags[i] = s2_flags[j] = True
                common_chars += 1
                break

    # short circuit if no characters match
    if not common_chars:
        return 0.0

    # count transpositions
    k = trans_count = 0
    for i, s1_f in enumerate(s1_flags):
        if s1_f:
            for j in range(k, s2_len):
                if s2_flags[j]:
                    k = j + 1
                    break
            if s1[i] != s2[j]:
                trans_count += 1
    trans_count //= 2

    # adjust for similarities in nonmatched characters
    common_chars = float(common_chars)
    weight = (
        (
            common_chars / s1_len
            + common_chars / s2_len
            + (common_chars - trans_count) / common_chars
        )
    ) / 3

    # winkler modification: continue to boost if strings are similar
    if winklerize and weight > 0.7:
        # adjust for up to first 4 chars in common
        j = min(min_len, 4)
        i = 0
        while i < j and s1[i] == s2[i]:
            i += 1
        if i:
            weight += i * 0.1 * (1.0 - weight)

        # optionally adjust for long strings
        # after agreeing beginning chars, at least two or more must agree and
        # agreed characters must be > half of remaining characters
        if (
            long_tolerance
            and min_len > 4
            and common_chars > i + 1
            and 2 * common_chars >= min_len + i
        ):
            weight += (1.0 - weight) * (
                float(common_chars - i - 1) / float(s1_len + s2_len - i * 2 + 2)
            )

    return weight


def jaro_winkler_similarity(s1: str, s2: str, long_tolerance: bool = False) -> float:
    return _jaro_winkler(s1, s2, long_tolerance, True)  # noqa


def damerau_levenshtein_distance(s1: str, s2: str) -> int:
    len1 = len(s1)
    len2 = len(s2)
    infinite = len1 + len2

    # character array
    da = defaultdict(int)

    # distance matrix
    score = [[0] * (len2 + 2) for x in range(len1 + 2)]

    score[0][0] = infinite
    for i in range(0, len1 + 1):
        score[i + 1][0] = infinite
        score[i + 1][1] = i
    for i in range(0, len2 + 1):
        score[0][i + 1] = infinite
        score[1][i + 1] = i

    for i in range(1, len1 + 1):
        db = 0
        for j in range(1, len2 + 1):
            i1 = da[s2[j - 1]]
            j1 = db
            cost = 1
            if s1[i - 1] == s2[j - 1]:
                cost = 0
                db = j

            score[i + 1][j + 1] = min(
                score[i][j] + cost,
                score[i + 1][j] + 1,
                score[i][j + 1] + 1,
                score[i1][j1] + (i - i1 - 1) + 1 + (j - j1 - 1),
            )
        da[s1[i - 1]] = i

    return score[len1 + 1][len2 + 1]


def closest_names(name: str, names: list[str], limit: int = 5) -> list[str]:
    """The names most like name (Jaro-Winkler), best first; ties keep the list's order."""
    scored = [(jaro_winkler_similarity(name.lower(), n.lower()), n) for n in names]
    scored.sort(key=lambda p: p[0], reverse=True)
    return [n for _, n in scored[:limit]]
