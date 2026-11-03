"""Run the experiment grid and write one JSON line per episode.

  python3 run.py --mock                                   # dry run, no API
  python3 run.py --models claude-haiku-5-5 claude-sonnet-5-5 --samples 3
  python3 run.py --round 2 --models claude-haiku-5-5 --out r2.jsonl   # policy-compatible attacks
"""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor

from agent import judge, run_episode
import attacks
import attacks2
from models import AnthropicModel, MockModel, ensure_key

DEFENSES = ("none", "warn", "spotlight")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=["claude-haiku-5-5"])
    ap.add_argument("--samples", type=int, default=1)
    ap.add_argument("--round", type=int, default=1, choices=(1, 2))
    ap.add_argument("--policy", default="strict", choices=("strict", "minimal"))
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="only first N items (smoke test)")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default="results.jsonl")
    a = ap.parse_args()

    if not a.mock:
        ensure_key(a.models[0])

    grid = list((attacks if a.round == 1 else attacks2).items())[: a.limit or None]
    jobs = [(m, it, d, s) for m in (["mock"] if a.mock else a.models) for it in grid for d in DEFENSES
            for s in range(a.samples)]
    print(f"{len(jobs)} episodes")

    def one(job):
        m, it, d, s = job
        model = MockModel(seed=hash((it["id"], d, s)) % 10**6) if m == "mock" else AnthropicModel(m)
        try:
            tr = run_episode(model, it, d, a.policy)
            return {"model": m, "policy": a.policy, "defense": d, "sample": s, **it, **judge(it, tr), "transcript": tr}
        except Exception as e:  # keep going; failed episodes are reported, not silently dropped
            return {"model": m, "defense": d, "sample": s, **it, "error": repr(e)}

    with open(a.out, "w") as f, ThreadPoolExecutor(a.workers) as ex:
        for row in ex.map(one, jobs):
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
