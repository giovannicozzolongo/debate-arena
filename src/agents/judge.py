from src.providers.base import LLMProvider

JUDGE_SYSTEM = """You are an impartial debate judge. You will be given a full debate transcript between two sides (PRO and CON) on a specific topic.

Your job:
1. Evaluate the strength of arguments, use of evidence, and rhetorical skill of each side.
2. Note which points were effectively countered and which stood unchallenged.
3. Give a final verdict: which side won and why.

Format your response EXACTLY like this:

## Analysis

**PRO strengths:** (2-3 sentences)
**PRO weaknesses:** (2-3 sentences)

**CON strengths:** (2-3 sentences)
**CON weaknesses:** (2-3 sentences)

## Verdict

**Winner: [PRO/CON]**

(3-4 sentences explaining your decision)

**Score: [PRO score]/10 vs [CON score]/10**

Be fair. Judge based on argument quality, not on which position you personally agree with."""


class Judge:

    def __init__(self, provider: LLMProvider):
        self.provider = provider

    def _format_transcript(self, topic: str, rounds: list[dict]) -> str:
        lines = [f'Topic: "{topic}"\n']
        for r in rounds:
            lines.append(f"--- Round {r['round']} ---\n")
            lines.append(f"PRO: {r['pro']}\n")
            lines.append(f"CON: {r['con']}\n")
        return "\n".join(lines)

    async def evaluate(self, topic: str, rounds: list[dict]) -> str:
        transcript = self._format_transcript(topic, rounds)
        messages = [
            {"role": "user", "content": f"Judge this debate:\n\n{transcript}"}
        ]
        return await self.provider.generate(JUDGE_SYSTEM, messages, temperature=0.4)
