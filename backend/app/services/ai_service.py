"""
Step 7 (from the doc): AI/ML comes AFTER the core API works, and starts as a
lightweight, rule-based analyzer rather than a trained model.

analyze_consent_text() looks at consent-related text and returns:
- risk level
- reason
- a recommended action

Swap this out for a real NLP/LLM call later without changing the route.
"""

HIGH_RISK_KEYWORDS = ["sell", "third party", "third-party", "indefinitely", "unlimited", "share your information"]
MEDIUM_RISK_KEYWORDS = ["selected third parties", "partners", "affiliates", "may share"]


def analyze_consent_text(text: str) -> dict:
    lowered = text.lower()

    if any(kw in lowered for kw in HIGH_RISK_KEYWORDS):
        return {
            "risk": "High",
            "reason": "Text suggests broad or indefinite sharing/selling of personal data.",
            "recommendation": "Reject or request narrower, purpose-limited data sharing terms.",
        }

    if any(kw in lowered for kw in MEDIUM_RISK_KEYWORDS):
        return {
            "risk": "Medium",
            "reason": "Third-party data sharing is mentioned but appears scoped.",
            "recommendation": "Review the scope of data sharing before granting consent.",
        }

    return {
        "risk": "Low",
        "reason": "No broad third-party sharing or high-risk language detected.",
        "recommendation": "Consent appears reasonably clear; proceed with standard review.",
    }
