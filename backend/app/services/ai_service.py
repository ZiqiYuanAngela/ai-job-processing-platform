from dataclasses import dataclass

from openai import OpenAI

from app.config import settings


@dataclass
class AIResult:
    content: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float


client = OpenAI(api_key=settings.openai_api_key)


def estimate_cost(
    input_tokens: int,
    output_tokens: int,
) -> float:
    # Replace these with the current prices for your selected model.
    input_cost_per_million = 0.40
    output_cost_per_million = 1.60

    input_cost = (
        input_tokens / 1_000_000
    ) * input_cost_per_million

    output_cost = (
        output_tokens / 1_000_000
    ) * output_cost_per_million

    return input_cost + output_cost


def generate_text(
    system_prompt: str,
    user_prompt: str,
) -> AIResult:
    response = client.responses.create(
        model=settings.openai_model,
        instructions=system_prompt,
        input=user_prompt,
    )

    usage = response.usage

    input_tokens = usage.input_tokens if usage else 0
    output_tokens = usage.output_tokens if usage else 0

    return AIResult(
        content=response.output_text,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated_cost_usd=estimate_cost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        ),
    )