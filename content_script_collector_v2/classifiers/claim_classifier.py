import re

HIGH_PATTERNS = [
    r"\b(cure|cures|treat|treats|heal|heals|reverse|eliminate|guarantee|guaranteed)\b",
    r"\b\d+\s*(day|days|hour|hours|week|weeks)\b.*\b(remove|erase|disappear|gone|cure)\b",
]
PROHIBITED_PATTERNS = [
    r"\b(cancer|eczema|psoriasis|acne)\b.{0,80}\b(cure|cures|treat|treats|heal|heals|eliminate|eliminates)\b",
    r"\b(cure|cures|treat|treats|heal|heals|eliminate|eliminates)\b.{0,80}\b(cancer|eczema|psoriasis|acne)\b",
]

def claim_risk(text: str) -> str:
    t = (text or "").lower()
    if any(re.search(p, t, re.I) for p in PROHIBITED_PATTERNS):
        return "PROHIBITED"
    if any(re.search(p, t, re.I) for p in HIGH_PATTERNS):
        return "HIGH"
    if any(w in t for w in ["clinically proven", "instant results", "100%", "permanent"]):
        return "MEDIUM"
    return "LOW"
