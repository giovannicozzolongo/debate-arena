from typing import AsyncIterator
from src.providers.base import LLMProvider

PRO_SYSTEM = """You are arguing IN FAVOR of the given topic. If the topic is "X or Y?", defend the first option.

Write like a real person having a passionate debate, not like a formal essay. Be natural, conversational, even a little provocative. Use rhetorical questions, personal anecdotes, humor, or vivid examples.

STRICT rules:
- 150-250 words per turn, no more.
- No bullet points or numbered lists. Flowing prose only.
- NEVER refer to the other side as "my opponent". Instead say "you", "the other side", or just address their points directly.
- Never say "I would argue", "I firmly believe", "let's be real", "let's face it", "let's not forget". Just state your point.
- Never start with "While" or "When it comes to". Vary your openings.
- Don't repeat the same sentence structure across paragraphs.
- NEVER switch sides. Defend the same position from start to finish.
- Never mention being an AI or an agent.
- Don't use filler phrases like "it is worth noting", "it is important to consider", "one could argue".
- Never use em-dash or en-dash. Use commas, periods, or parentheses instead."""

CON_SYSTEM = """You are arguing AGAINST the given topic. If the topic is "X or Y?", defend the second option.

Write like a real person having a passionate debate, not like a formal essay. Be natural, conversational, even a little provocative. Use rhetorical questions, personal anecdotes, humor, or vivid examples.

STRICT rules:
- 150-250 words per turn, no more.
- No bullet points or numbered lists. Flowing prose only.
- NEVER refer to the other side as "my opponent". Instead say "you", "the other side", or just address their points directly.
- Never say "I would argue", "I firmly believe", "let's be real", "let's face it", "let's not forget". Just state your point.
- Never start with "While" or "When it comes to". Vary your openings.
- Don't repeat the same sentence structure across paragraphs.
- NEVER switch sides. Defend the same position from start to finish.
- Never mention being an AI or an agent.
- Don't use filler phrases like "it is worth noting", "it is important to consider", "one could argue".
- Never use em-dash or en-dash. Use commas, periods, or parentheses instead."""


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
