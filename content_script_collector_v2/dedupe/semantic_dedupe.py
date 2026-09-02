import hashlib
import re
from difflib import SequenceMatcher

def normalize_text(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"\{[^}]+\}|\[[^\]]+\]", "[x]", text)
    text = re.sub(r"[^a-z0-9가-힣\[\]\s]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def exact_key(text: str) -> str:
    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()

def formula_family(text: str) -> str:
    n = normalize_text(text)
    tokens = [t for t in n.split() if t != "[x]"]
    return " ".join(tokens[:6]) or "unknown"

def is_near_duplicate(a: str, b: str, threshold: float = 0.88) -> bool:
    return similarity(a, b) >= threshold
