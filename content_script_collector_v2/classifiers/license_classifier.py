from dataclasses import dataclass

@dataclass
class LicenseDecision:
    usage_class: str
    reason: str
    attribution_required: bool = False
    share_alike: bool = False
    noncommercial_only: bool = False

COMMERCIAL_PERMISSIVE = {
    "MIT", "APACHE-2.0", "BSD-2-CLAUSE", "BSD-3-CLAUSE", "ISC", "CC0-1.0"
}

def classify_license(spdx: str | None, repo_usage_override: str | None = None) -> LicenseDecision:
    if repo_usage_override in {"COMMERCIAL_OK","TRANSFORM_ONLY","RESEARCH_ONLY","BLOCKED"}:
        if repo_usage_override == "RESEARCH_ONLY":
            return LicenseDecision("RESEARCH_ONLY", "Repository override: research/benchmark only.")
        return LicenseDecision(repo_usage_override, "Repository collection specification override.")

    s = (spdx or "").strip().upper()
    if s in COMMERCIAL_PERMISSIVE:
        return LicenseDecision("COMMERCIAL_OK", f"Permissive license: {s}",
                               attribution_required=(s != "CC0-1.0"))
    if "BY-NC" in s or "NONCOMMERCIAL" in s:
        return LicenseDecision("RESEARCH_ONLY", f"Non-commercial restriction detected: {s}",
                               attribution_required=True, noncommercial_only=True)
    if "CC-BY-SA" in s or "CC BY-SA" in s:
        return LicenseDecision("TRANSFORM_ONLY", f"Share-alike license requires careful downstream compliance: {s}",
                               attribution_required=True, share_alike=True)
    if not s or s in {"NOASSERTION","OTHER","UNKNOWN","MIXED"}:
        return LicenseDecision("UNKNOWN", "License is missing, mixed, or not machine-verifiable.")
    return LicenseDecision("TRANSFORM_ONLY", f"License requires manual review before commercial reuse: {s}")
