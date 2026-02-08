import pytest
from unittest.mock import AsyncMock
from src.agents.debater import Debater
from src.agents.judge import Judge


class FakeProvider:
    """Fake LLM that returns canned responses."""

    def __init__(self, response="This is a test argument."):
        self.response = response
        self.calls = []

    async def stream(self, system_prompt, messages, temperature=0.8):
        self.calls.append({"system": system_prompt, "messages": messages})
        for word in self.response.split():
            yield word + " "

    async def generate(self, system_prompt, messages, temperature=0.8):
        self.calls.append({"system": system_prompt, "messages": messages})
        return self.response


@pytest.mark.asyncio
async def test_debater_pro_opening():
    provider = FakeProvider("Strong opening argument here.")
    debater = Debater("pro", provider)
    result = await debater.argue_full("pineapple on pizza")
    assert "Strong" in result
    assert len(provider.calls) == 1
    assert "opening" in provider.calls[0]["messages"][0]["content"].lower()


@pytest.mark.asyncio
async def test_debater_con_response():
    provider = FakeProvider("Counter argument response.")
    debater = Debater("con", provider)
    result = await debater.argue_full("pineapple on pizza", opponent_last="I love pineapple")
    assert "Counter" in result


@pytest.mark.asyncio
async def test_debater_invalid_side():
    with pytest.raises(ValueError):
        Debater("neutral", FakeProvider())


@pytest.mark.asyncio
async def test_debater_history_builds():
    provider = FakeProvider("Argument text.")
    debater = Debater("pro", provider)

    await debater.argue_full("topic")
    assert len(debater.history) == 2  # user + assistant

    await debater.argue_full("topic", "opponent said stuff")
    assert len(debater.history) == 4  # prev context + new exchange


@pytest.mark.asyncio
async def test_judge_evaluate():
    provider = FakeProvider("## Verdict\n**Winner: PRO**\n**Score: 8/10 vs 6/10**")
    judge = Judge(provider)
    rounds = [
        {"round": 1, "pro": "Pro argument", "con": "Con argument"},
    ]
    verdict = await judge.evaluate("test topic", rounds)
    assert "Winner" in verdict
    assert len(provider.calls) == 1


@pytest.mark.asyncio
async def test_judge_transcript_format():
    provider = FakeProvider("verdict")
    judge = Judge(provider)
    rounds = [
        {"round": 1, "pro": "aaa", "con": "bbb"},
        {"round": 2, "pro": "ccc", "con": "ddd"},
    ]
    await judge.evaluate("cats vs dogs", rounds)
    prompt_content = provider.calls[0]["messages"][0]["content"]
    assert "cats vs dogs" in prompt_content
    assert "Round 1" in prompt_content
    assert "Round 2" in prompt_content
