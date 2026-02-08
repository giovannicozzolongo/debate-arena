from typing import AsyncIterator
from src.providers.base import LLMProvider

PRO_SYSTEM = """You are a skilled debater arguing IN FAVOR of the given topic.

Rules:
- Build strong, well-reasoned arguments with evidence and examples.
- Directly address and counter your opponent's points when responding.
- Stay respectful but be persuasive and sharp.
- Keep each response focused: one main argument with 2-3 supporting points.
- Write 150-250 words per turn. No more.
- Do not use bullet points or numbered lists. Write in flowing prose.
- Never break character or mention that you are an AI."""

CON_SYSTEM = """You are a skilled debater arguing AGAINST the given topic.

Rules:
- Build strong, well-reasoned arguments with evidence and examples.
- Directly address and counter your opponent's points when responding.
- Stay respectful but be persuasive and sharp.
- Keep each response focused: one main argument with 2-3 supporting points.
- Write 150-250 words per turn. No more.
- Do not use bullet points or numbered lists. Write in flowing prose.
- Never break character or mention that you are an AI."""


class Debater:

    def __init__(self, side: str, provider: LLMProvider):
        if side not in ("pro", "con"):
            raise ValueError("side must be 'pro' or 'con'")
        self.side = side
        self.provider = provider
        self.system_prompt = PRO_SYSTEM if side == "pro" else CON_SYSTEM
        self.history: list[dict] = []

    def _build_messages(self, topic: str, opponent_last: str | None) -> list[dict]:
        msgs = list(self.history)
        if not msgs:
            msgs.append({
                "role": "user",
                "content": f"The debate topic is: \"{topic}\"\n\nPresent your opening argument.",
            })
        elif opponent_last:
            msgs.append({
                "role": "user",
                "content": f"Your opponent just argued:\n\n\"{opponent_last}\"\n\nRespond to their points and make your next argument.",
            })
        return msgs

    async def argue(
        self, topic: str, opponent_last: str | None = None
    ) -> AsyncIterator[str]:
        messages = self._build_messages(topic, opponent_last)
        full_response = []

        async for chunk in self.provider.stream(self.system_prompt, messages):
            full_response.append(chunk)
            yield chunk

        # save to history for context in next rounds
        assistant_text = "".join(full_response)
        self.history = messages + [{"role": "assistant", "content": assistant_text}]

    async def argue_full(self, topic: str, opponent_last: str | None = None) -> str:
        chunks = []
        async for chunk in self.argue(topic, opponent_last):
            chunks.append(chunk)
        return "".join(chunks)
