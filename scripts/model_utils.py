"""GitHub Models request helpers."""


def supports_custom_temperature(model: str) -> bool:
    return not model.startswith("gpt-5")


def build_token_kwargs(model: str, max_tokens: int) -> dict:
    if model.startswith(("gpt-5", "o1", "o3", "o4")):
        return {"max_completion_tokens": max_tokens}
    return {"max_tokens": max_tokens}


def build_chat_kwargs(
    model: str, max_tokens: int, temperature: float | None = None
) -> dict:
    kwargs = build_token_kwargs(model, max_tokens)
    if temperature is not None and supports_custom_temperature(model):
        kwargs["temperature"] = temperature
    return kwargs
