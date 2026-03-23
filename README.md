# Debate Arena

Two AI agents debate any topic in real time. A third AI judges who wins.

**[Try it live](https://debate-arena-production-bdc0.up.railway.app)** (free, no sign-up needed)

![Python](https://img.shields.io/badge/python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![License](https://img.shields.io/badge/license-MIT-gray)

## What it does

1. You enter a debate topic
2. A **PRO** agent argues in favor, a **CON** agent argues against
3. They go back and forth for multiple rounds, responding to each other's points
4. A **Judge** agent evaluates the full debate and picks a winner

Everything streams in real time. You watch the arguments appear word by word.

## Architecture

```
User input → FastAPI (SSE) → PRO agent → streamed to UI
                            → CON agent → streamed to UI
                            → Judge     → verdict to UI
```

- **Multi-agent orchestration**: three independent LLM agents with distinct system prompts
- **Streaming**: Server-Sent Events for real-time text delivery
- **Provider abstraction**: swap between Groq (free), Claude, or GPT with one click
- **No framework**: agents built from scratch, no LangChain/CrewAI dependency

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# get a free Groq API key at https://console.groq.com
cp .env.example .env
# edit .env and add your GROQ_API_KEY

make serve
# open http://localhost:8000
```

## Tech stack

| Component | Tech |
|---|---|
| Backend | Python, FastAPI, SSE |
| Frontend | Vanilla JS, CSS (no build step) |
| Default LLM | Llama 3.3 70B via Groq (free) |
| Optional LLMs | Claude Sonnet, GPT-4o mini (BYOK) |

## Project structure

```
src/
  providers/       # LLM API abstraction layer
    base.py        # abstract provider interface
    groq_provider.py
    anthropic_provider.py
    openai_provider.py
  agents/
    debater.py     # PRO and CON debate agents
    judge.py       # impartial judge agent
  api/
    main.py        # FastAPI app + SSE endpoint
    schemas.py     # request/response models
frontend/
  index.html       # single-page app
  css/style.css    # dark theme UI
  js/app.js        # SSE client + DOM updates
tests/
  test_agents.py   # agent unit tests
  test_api.py      # API integration tests
```

## License

MIT
