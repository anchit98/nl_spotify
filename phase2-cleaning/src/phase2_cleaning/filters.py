import re
import emoji
from langdetect import detect, LangDetectException

# PII regex patterns
EMAIL_REGEX = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
PHONE_REGEX = re.compile(r"\b(?:\+?1[-.\s]?)?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
URL_REGEX = re.compile(r"https?://\S+|www\.\S+")

TOPIC_KEYWORDS = {
    "struggle_discovery": [
        "discover", "finding", "new music", "explore", "hard to find", "can't find",
        "search", "looking for", "unfamiliar"
    ],
    "recommendation_frustrations": [
        "recommend", "suggest", "algorithm", "mix", "discover weekly", "release radar",
        "frustrat", "bad", "terrible", "sucks", "awful", "irrelevant", "not what i like",
        "wrong genre", "don't like"
    ],
    "listening_behaviors": [
        "playlist", "listen to", "listening", "mood", "vibe", "background", "focus",
        "workout", "study", "party", "relax", "gym", "drive", "commute"
    ],
    "repeated_listening": [
        "repeat", "same songs", "same artists", "again and again", "loop", "over and over",
        "tired of the same", "keep playing the same", "always the same", "repetitive"
    ],
    "user_segments": [
        "premium", "free", "student", "family", "kids", "teens", "older", "casual",
        "power user", "audiophile", "subscription", "ads", "paying"
    ],
    "unmet_needs": [
        "feature request", "wish", "missing", "need", "want", "lack", "please add",
        "why can't", "should have", "bring back", "would be nice"
    ]
}

def mask_pii(text: str) -> str:
    text = EMAIL_REGEX.sub("[EMAIL]", text)
    text = PHONE_REGEX.sub("[PHONE]", text)
    text = URL_REGEX.sub("[URL]", text)
    return text

def has_emoji(text: str) -> bool:
    return emoji.emoji_count(text) > 0

def is_english(text: str) -> bool:
    try:
        return detect(text) == "en"
    except LangDetectException:
        return False

def get_matched_topics(text: str) -> list[str]:
    text_lower = text.lower()
    matched = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            matched.append(topic)
    return matched

def clean_text(text: str) -> str:
    # Basic whitespace cleanup
    text = re.sub(r"\s+", " ", text).strip()
    return mask_pii(text)
