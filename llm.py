"""LLM handler."""


def llm_json(prompt: str, schema: dict) -> dict:
    """Return a JSON object generated from ``prompt`` according to ``schema``.

    This module does not provide an LLM client or transport configuration, so
    callers must supply an implementation before invoking this function.
    """
    raise NotImplementedError("LLM client is not configured")
    raise NotImplementedError("P2.4")
