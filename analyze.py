"""Summarize results.jsonl: ASR with Wilson 95% CI per cell, utility, and paired ES-vs-EN McNemar test."""
import json
import math
import sys
from collections import defaultdict


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0, c - h), min(1, c + h))


def mcnemar(b, c):
    """Exact two-sided binomial McNemar p-value on discordant pairs."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def main(path="results.jsonl"):
    rows = [json.loads(l) for l in open(path)]
    errors = [r for r in rows if "error" in r]
    rows = [r for r in rows if "error" not in r]
    print(f"{len(rows)} episodes ok, {len(errors)} errors\n")

    cells = defaultdict(list)
    for r in rows:
        cells[(r["model"], r["defense"], r["cond"])].append(r)
    print(f"{'model':22} {'defense':10} {'cond':16} {'n':>4} {'ASR':>6}  95% CI        utility")
    for key in sorted(cells):
        rs = cells[key]
        k, n = sum(r["attack_success"] for r in rs), len(rs)
        lo, hi = wilson(k, n)
        u = sum(r["utility"] for r in rs) / n
        print(f"{key[0]:22} {key[1]:10} {key[2]:16} {n:4} {k/n:6.1%}  [{lo:.1%}, {hi:.1%}]  {u:.0%}")

    print("\nPaired ES vs EN (same goal/style/channel/sample):")
    idx = {(r["model"], r["defense"], r["cond"], r["goal"], r["style"], r["channel"], r["sample"]): r["attack_success"]
           for r in rows}
    for m, d in sorted({(r["model"], r["defense"]) for r in rows}):
        b = c = 0
        for (mm, dd, cond, *rest), es in idx.items():
            if (mm, dd, cond) != (m, d, "es"):
                continue
            en = idx.get((m, d, "en", *rest))
            if en is None:
                continue
            b += es and not en
            c += en and not es
        print(f"  {m:22} {d:10} ES-only={b:3} EN-only={c:3} p={mcnemar(b, c):.3f}")


if __name__ == "__main__":
    main(*sys.argv[1:])
