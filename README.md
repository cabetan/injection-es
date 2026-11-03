# injection-es

Does a tool-using customer-service agent handle indirect prompt injection differently in Spanish and English?

**Short answer, for Claude Haiku:** it never took the injected action (0 of ~1,450 episodes), but it relayed the injected claim to the customer in 81–98% of episodes. With a strict policy prompt it warned that the claim was unverified less often in Spanish (71%) than in English (86%; paired McNemar p = 0.006). Full write-up: [WRITEUP.md](WRITEUP.md). One-page design: [DESIGN.md](DESIGN.md).

## Files

| File | What it does |
|---|---|
| `attacks.py` | Round 1: explicit injections (6 styles × 3 goals × 3 channels × 3 language conditions) |
| `attacks2.py` | Rounds 2–3: policy-compatible injections plus a customer follow-up |
| `agent.py` | Agent loop, tools, system prompts (strict/minimal), defenses, programmatic attack judge |
| `models.py` | Anthropic Messages API over plain HTTP (no SDK) and a mock model for dry runs |
| `run.py` | Runs the grid, one JSON line per episode |
| `analyze.py` | Attack success rate with Wilson CIs, paired ES vs EN McNemar test |
| `judge.py` | Bilingual LLM judge for disclosure, false expectation and flagging |
| `build_audit_page.py`, `agreement.py` | Blind hand-labelling page and judge–human agreement (Cohen's κ) |

## Run

```bash
python3 run.py --mock                       # dry run, no API key needed
python3 run.py --round 2 --models claude-haiku-5-5 --samples 2 --out r2-haiku.jsonl
python3 judge.py r2-haiku.jsonl && python3 judge.py --summary r2-haiku.judged.jsonl
```

The scripts ask for `ANTHROPIC_API_KEY` if it is not set. They use only the Python standard library (3.10+).

## Data

`results/` holds every episode transcript with labels (JSONL). The store, customer and email addresses are fictional.

## License

MIT
