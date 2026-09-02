import re
from pathlib import Path

HOOK_CUES = ("hook", "opening", "first 3", "first three", "scroll", "pattern interrupt")
CTA_CUES = ("cta", "call to action", "follow", "comment", "save", "click", "shop", "buy")
BEFORE_AFTER_CUES = ("before", "after", "transformation")
DEMO_CUES = ("demo", "unboxing", "pov", "tutorial", "how-to", "how to")
TESTIMONIAL_CUES = ("testimonial", "review", "social proof", "customer")

def iter_markdown_blocks(text: str):
    sections = re.split(r'(?m)^#{1,6}\s+', text)
    for sec in sections:
        sec = sec.strip()
        if len(sec) >= 20:
            yield sec

def classify_block(block: str):
    s = block.lower()
    cats = []
    if any(c in s for c in HOOK_CUES): cats.append("viral_hook")
    if any(c in s for c in CTA_CUES): cats.append("cta")
    if any(c in s for c in BEFORE_AFTER_CUES): cats.append("before_after")
    if any(c in s for c in DEMO_CUES): cats.append("product_demo")
    if any(c in s for c in TESTIMONIAL_CUES): cats.append("testimonial")
    if any(c in s for c in ("script", "spoken", "on-screen", "shot", "timing")):
        cats.append("short_form_script")
    return sorted(set(cats))

def extract_candidates(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    out = []
    for block in iter_markdown_blocks(text):
        cats = classify_block(block)
        if cats:
            out.append({"categories": cats, "text": block[:12000]})
    return out
