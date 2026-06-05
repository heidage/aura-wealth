"""
Input guardrails for AuraWealth chat.

Three checks, applied in order:
  1. Length — reject messages over 4000 chars
  2. Prompt injection — block attempts to hijack system instructions
  3. PII — redact SSNs, credit cards, and phone numbers before passing downstream
"""

import re
from dataclasses import dataclass

MAX_INPUT_LENGTH = 4000

# ---------------------------------------------------------------------------
# Prompt injection patterns
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"ignore\s+(all\s+)?previous\s+instructions?",
        r"forget\s+(your\s+)?(previous\s+)?instructions?",
        r"disregard\s+(your\s+)?(previous\s+)?instructions?",
        r"override\s+(your\s+)?(previous\s+)?instructions?",
        r"you\s+are\s+now\s+(?!aura)",   # "you are now DAN / GPT / etc."
        r"pretend\s+(you\s+are|to\s+be)",
        r"act\s+as\s+(if\s+you\s+(are|were)|a\s+)",
        r"(new|updated|revised)\s+system\s+prompt",
        r"<\s*system\s*>",               # XML-style system tag injection
        r"\[\s*system\s*\]",
        r"jailbreak",
        r"\bDAN\s+mode\b",
        r"do\s+anything\s+now",
    ]
]

# ---------------------------------------------------------------------------
# PII patterns  (redact, don't block)
# ---------------------------------------------------------------------------

_PII_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN REDACTED]"),
    (
        re.compile(r"\b(?:\d{4}[\s\-]){3}\d{4}\b"),
        "[CARD REDACTED]",
    ),
    (
        re.compile(r"\b(\+?1[\s\-]?)?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}\b"),
        "[PHONE REDACTED]",
    ),
]


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class GuardrailResult:
    blocked: bool
    reason: str          # human-readable; empty string if not blocked
    sanitized: str       # original or PII-redacted text


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate(text: str) -> GuardrailResult:
    # 1. Length
    if len(text) > MAX_INPUT_LENGTH:
        return GuardrailResult(
            blocked=True,
            reason=f"Message exceeds {MAX_INPUT_LENGTH} character limit.",
            sanitized=text,
        )

    # 2. Injection detection
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            return GuardrailResult(
                blocked=True,
                reason="Message contains a prompt injection attempt and was blocked.",
                sanitized=text,
            )

    # 3. PII redaction
    sanitized = text
    for pattern, replacement in _PII_RULES:
        sanitized = pattern.sub(replacement, sanitized)

    return GuardrailResult(blocked=False, reason="", sanitized=sanitized)
