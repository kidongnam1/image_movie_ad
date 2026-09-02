import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from classifiers.license_classifier import classify_license
from classifiers.claim_classifier import claim_risk
from dedupe.semantic_dedupe import is_near_duplicate, formula_family

assert classify_license("MIT").usage_class=="COMMERCIAL_OK"
assert classify_license("CC-BY-NC-SA-4.0").usage_class=="RESEARCH_ONLY"
assert claim_risk("This cures eczema permanently")=="PROHIBITED"
assert is_near_duplicate("If you're still doing [X], stop", "If you are still doing [X], stop", 0.75)
print("SELFTEST PASS")
