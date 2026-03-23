import re
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

from src.api.schemas import DebateRequest, DebateEvent
from src.agents import Debater, Judge
from src.providers import GroqProvider, AnthropicProvider, OpenAIProvider
from src.config import GROQ_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY

app = FastAPI(title="AI Debate Arena")

BLOCKED_PATTERNS = re.compile(
    r"pedophil|paedophil|pedofil|child\s*(abuse|porn|sex)|"
    r"bestiality|zoophil|necrophil|incest|"
    r"genocide\s+is\s+good|"
    r"how\s+to\s+(kill|murder|rape|kidnap|bomb|poison)",
    re.IGNORECASE,
)


def _topic_allowed(topic: str) -> bool:
    return not BLOCKED_PATTERNS.search(topic)


TOPIC_CHECK_PROMPT = """You are a strict topic validator. The user will give you a debate topic.
Reply with ONLY "yes" or "no". Nothing else.
Reply "yes" ONLY if the topic is a clear, complete, debatable statement or question in a real language.
Reply "no" if ANY of these apply:
- It is not a real word or phrase in any language
- It is random characters, a typo, or gibberish (e.g. "ewed", "asdf", "ggino")
- It is just a single word without a clear debatable position
- It is a name or noun without context
- It is too short or vague to have two sides
- You have to GUESS what the user meant
When in doubt, reply "no"."""


async def _validate_topic(provider, topic: str) -> bool:
    if len(topic.strip()) < 5:
        return False
    messages = [{"role": "user", "content": f'Is this a valid debate topic? "{topic}"'}]
    result = await provider.generate(TOPIC_CHECK_PROMPT, messages, temperature=0.0)
    return result.strip().lower().startswith("yes")


def _get_provider(name: str, byok: str | None):
    providers = {
        "groq": (GroqProvider, GROQ_API_KEY),
        "anthropic": (AnthropicProvider, ANTHROPIC_API_KEY),
        "openai": (OpenAIProvider, OPENAI_API_KEY),
    }
    if name not in providers:
        raise ValueError(f"unknown provider: {name}")
    cls, default_key = providers[name]
    key = byok or default_key
    if not key:
        raise ValueError(f"no API key for {name}, set it in .env or pass it in the request")
    return cls(api_key=key)


async def _run_debate(req: DebateRequest):
    if not _topic_allowed(req.topic):
        yield {"data": DebateEvent(type="error", content="This topic is not suitable for debate. Please choose a different one.").model_dump_json()}
        return

    req.num_rounds = min(max(req.num_rounds, 1), 10)

    try:
        provider = _get_provider(req.provider, req.api_key)
    except ValueError as e:
        yield {"data": DebateEvent(type="error", content=str(e)).model_dump_json()}
        return

    # validate topic with LLM
    try:
        valid = await _validate_topic(provider, req.topic)
        if not valid:
            yield {"data": DebateEvent(type="error", content="This doesn't look like a debatable topic. Try a clear statement or question, e.g. \"Social media does more harm than good\".").model_dump_json()}
            return
    except Exception as e:
        msg = str(e)
        if "rate_limit" in msg.lower() or "429" in msg:
            yield {"data": DebateEvent(type="error", content="Service is busy right now. Please wait a minute and try again.").model_dump_json()}
            return

    pro = Debater("pro", provider)
    con = Debater("con", provider)
    judge = Judge(provider)

    rounds = []
    pro_last = None
    con_last = None

    for round_num in range(1, req.num_rounds + 1):
        yield {
            "data": DebateEvent(type="round_start", round=round_num).model_dump_json()
        }

        # PRO argues
        pro_chunks = []
        try:
            async for chunk in pro.argue(req.topic, con_last):
                pro_chunks.append(chunk)
                yield {
                    "data": DebateEvent(
                        type="pro_chunk", round=round_num, content=chunk
                    ).model_dump_json()
                }
        except Exception as e:
            yield {"data": DebateEvent(type="error", content="Service is busy right now. Please wait a minute and try again.").model_dump_json()}
            return
        pro_last = "".join(pro_chunks)

        # CON argues
        con_chunks = []
        try:
            async for chunk in con.argue(req.topic, pro_last):
                con_chunks.append(chunk)
                yield {
                    "data": DebateEvent(
                        type="con_chunk", round=round_num, content=chunk
                    ).model_dump_json()
                }
        except Exception:
            yield {"data": DebateEvent(type="error", content="Service is busy right now. Please wait a minute and try again.").model_dump_json()}
            return
        con_last = "".join(con_chunks)

        rounds.append({"round": round_num, "pro": pro_last, "con": con_last})

        yield {
            "data": DebateEvent(type="round_end", round=round_num).model_dump_json()
        }

    # judge
    try:
        verdict = await judge.evaluate(req.topic, rounds)
        yield {"data": DebateEvent(type="judge", content=verdict).model_dump_json()}
    except Exception:
        yield {"data": DebateEvent(type="error", content="Service is busy right now. Please wait a minute and try again.").model_dump_json()}
        return
    yield {"data": DebateEvent(type="done").model_dump_json()}


@app.post("/api/debate")
async def start_debate(req: DebateRequest):
    return EventSourceResponse(_run_debate(req))


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# serve frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
async def index():
    return FileResponse("frontend/index.html")
