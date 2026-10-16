"""Phonetic spelling comparison for large-v3's English recognition evidence."""

import re
import unicodedata
from difflib import SequenceMatcher

VOWELS = dict(
    zip(
        "അആഇഈഉഊഋഎഏഐഒഓഔ",
        ["a", "aa", "i", "ii", "u", "uu", "ri", "e", "ee", "ai", "o", "oo", "au"],
    )
)
SIGNS = dict(
    zip(
        "ാിീുൂൃെേൈൊോൗ്",
        ["aa", "i", "ii", "u", "uu", "ri", "e", "ee", "ai", "o", "oo", "au", ""],
    )
)
CONSONANTS = dict(
    zip(
        "കഖഗഘങചഛജഝഞടഠഡഢണതഥദധനപഫബഭമയരലവശഷസഹളഴറ",
        [
            "k",
            "kh",
            "g",
            "gh",
            "ng",
            "ch",
            "chh",
            "j",
            "jh",
            "ny",
            "t",
            "th",
            "d",
            "dh",
            "n",
            "th",
            "th",
            "d",
            "dh",
            "n",
            "p",
            "ph",
            "b",
            "bh",
            "m",
            "y",
            "r",
            "l",
            "v",
            "sh",
            "sh",
            "s",
            "h",
            "l",
            "zh",
            "r",
        ],
    )
)
CHILLU = dict(zip("ൺൻർൽൾൿ", ["n", "n", "r", "l", "l", "k"]))


def romanize(text):
    result = []
    for index, char in enumerate(text):
        if char in VOWELS:
            result.append(VOWELS[char])
        elif char in CONSONANTS:
            result.append(CONSONANTS[char])
            if index + 1 == len(text) or text[index + 1] not in SIGNS:
                result.append("a")
        elif char in SIGNS:
            result.append(SIGNS[char])
        elif char in CHILLU:
            result.append(CHILLU[char])
        elif char == "ം":
            result.append("m")
        elif char == "ഃ":
            result.append("h")
        elif char.isspace():
            result.append(" ")
    return "".join(result)


def phonetic(text):
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    for before, after in [
        ("zh", "l"),
        ("sh", "s"),
        ("th", "t"),
        ("dh", "t"),
        ("kh", "k"),
        ("gh", "k"),
        ("ph", "p"),
        ("bh", "p"),
        ("ch", "c"),
        ("j", "c"),
        ("g", "k"),
        ("b", "p"),
        ("d", "t"),
    ]:
        text = text.replace(before, after)
    text = re.sub("[^a-z]", "", text)
    return re.sub(r"(.)\1+", r"\1", text)


def english_score(pair, candidate):
    target = phonetic(romanize(candidate["text"]))
    if not target:
        return 0
    best = 0
    utterances = pair.get("utterances", [])
    start = utterances[0]["start"] if utterances else None
    end = utterances[-1]["end"] if utterances else None
    for segment in pair.get("english_segments", []):
        # A neighboring announcement/word must not label this clip merely
        # because the recognizer's coarse timestamp overlaps its edge.
        if start is not None and min(end, segment["end"]) - max(
            start, segment["start"]
        ) < 0.65 * (end - start):
            continue
        if segment["end"] - segment["start"] > 12:
            continue
        text = segment["text"]
        tokens = text.split()
        # Compare the complete phrase, with only exact repeated halves removed.
        # Sliding windows over a multiword segment mislabeled adjacent clips.
        while (
            len(tokens) % 2 == 0
            and tokens[: len(tokens) // 2] == tokens[len(tokens) // 2 :]
        ):
            tokens = tokens[: len(tokens) // 2]
        weight = 0.95
        sample = phonetic(" ".join(tokens))
        if sample:
            best = max(
                best,
                weight * SequenceMatcher(None, target, sample, autojunk=False).ratio(),
            )
        # Only exact English meaning phrases count as gloss evidence, avoiding a
        # misleading fuzzy match between unrelated English and Malayalam words.
        gloss = re.sub(r"<[^>]+>", " ", candidate["meaning"]).lower()
        clean = re.sub("[^a-z ]", " ", text.lower()).strip()
        if len(clean) >= 4 and clean in [g.strip() for g in re.split("[,;()]", gloss)]:
            best = max(best, weight)
    return best
