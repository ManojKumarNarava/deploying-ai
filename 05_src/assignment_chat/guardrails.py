import re

RESTRICTED_TOPIC_PATTERNS = [
    r"\bcat\b",
    r"\bcats\b",
    r"\bkitten\b",
    r"\bkittens\b",
    r"\bfeline\b",
    r"\bfelines\b",
    r"\bdog\b",
    r"\bdogs\b",
    r"\bpuppy\b",
    r"\bpuppies\b",
    r"\bcanine\b",
    r"\bcanines\b",
    r"\bhoroscope\b",
    r"\bhoroscopes\b",
    r"\bzodiac\b",
    r"\bzodiac sign\b",
    r"\bzodiac signs\b",
    r"\bastrology\b",
    r"\bstar sign\b",
    r"\bstar signs\b",
    r"\btaylor\s+swift\b",
]

PROMPT_ATTACK_PATTERNS = [
    r"\bsystem prompt\b",
    r"\bdeveloper message\b",
    r"\bdeveloper instructions?\b",
    r"\bhidden instructions?\b",
    r"\binternal instructions?\b",
    r"\binitial instructions?\b",
    r"\bshow\b.*\bprompt\b",
    r"\breveal\b.*\bprompt\b",
    r"\bprint\b.*\bprompt\b",
    r"\brepeat\b.*\bprompt\b",
    r"\bdisplay\b.*\bprompt\b",
    r"\bexpose\b.*\binstructions?\b",
    r"\breveal\b.*\binstructions?\b",
    r"\bsummarize\b.*\binstructions?\b",
    r"\btranslate\b.*\binstructions?\b",
    r"\bencode\b.*\binstructions?\b",
    r"\bignore\b.*\bprevious\b.*\binstructions?\b",
    r"\bignore\b.*\bprior\b.*\binstructions?\b",
    r"\bignore\b.*\babove\b.*\binstructions?\b",
    r"\boverride\b.*\binstructions?\b",
    r"\bmodify\b.*\bsystem prompt\b",
    r"\bchange\b.*\bsystem prompt\b",
    r"\breplace\b.*\bsystem prompt\b",
    r"\bwhat rules were you given\b",
    r"\btext above\b",
]

def matches_any_pattern(
    message: str,
    patterns: list[str],
) -> bool:
    """Returns True when the message matches one or more patterns."""

    return any(
        re.search(
            pattern,
            message,
            flags=re.IGNORECASE,
        )
        for pattern in patterns
    )

def check_user_message(
    message: str,
) -> str | None:
    """Checks the latest user message before it reaches the model. Returns a refusal message when a guardrail is triggered. Returns None when the request may continue."""

    if not message or not message.strip():
        return ("Please enter a question or travel request.")

    if matches_any_pattern(message,PROMPT_ATTACK_PATTERNS,):
        return (
            "I can't reveal or modify my internal instructions. "
            "I can explain my public features or help you explore "
            "Canadian cities."
        )

    if matches_any_pattern(message,RESTRICTED_TOPIC_PATTERNS,):
        return (
            "I'm unable to help with that topic. I can assist with "
            "Canadian city information, weather, and travel planning."
        )

    return None