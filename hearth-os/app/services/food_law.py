from __future__ import annotations

import re

# House food law. This is kitchen logistics, not a medical protocol.
BANNED_INGREDIENT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"kerrygold", re.I), "kerrygold"),
    (re.compile(r"\bketo\b", re.I), "keto"),
    (re.compile(r"vegetable\s+oil", re.I), "vegetable_oil"),
    (re.compile(r"canola\s+oil", re.I), "vegetable_oil"),
    (re.compile(r"soybean\s+oil", re.I), "vegetable_oil"),
    (re.compile(r"\bcrisco\b", re.I), "vegetable_oil"),
    (re.compile(r"organ\s*meat", re.I), "organ"),
    (re.compile(r"\boffal\b", re.I), "organ"),
    (re.compile(r"\bsweetbread", re.I), "organ"),
    (re.compile(r"\btripe\b", re.I), "organ"),
    (re.compile(r"\bgizzard", re.I), "organ"),
    (re.compile(r"\bliver\b", re.I), "organ"),
    (re.compile(r"\bkidney\b", re.I), "organ"),
    (re.compile(r"\bbeef\s+heart\b", re.I), "organ"),
    (re.compile(r"\bchicken\s+heart", re.I), "organ"),
    (re.compile(r"\bheart\s+meat\b", re.I), "organ"),
]

STAPLE_RICE_KEY = "jasmine_rice"
RICE_KEYS = frozenset({"jasmine_rice"})

HOUSE_LAW_REPLY = "House law forbids that ingredient."

SYMPTOM_WORDS = (
    "flu",
    "vomit",
    "headache",
    "cancer",
    "diarrhea",
    "nausea",
    "migraine",
    "constipat",
    "diagnosis",
    "stomach",
)


def is_banned(text: str) -> tuple[bool, str]:
    blob = text or ""
    for pattern, reason in BANNED_INGREDIENT_PATTERNS:
        if pattern.search(blob):
            return True, reason
    return False, ""


def contains_symptom_word(text: str) -> bool:
    lower = (text or "").lower()
    return any(word in lower for word in SYMPTOM_WORDS)
