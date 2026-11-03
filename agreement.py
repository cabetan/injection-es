"""Judge-vs-human agreement on the audit sample: accuracy and Cohen's kappa per label.

  python3 agreement.py ~/Downloads/human_labels.json
"""
import csv
import json
import sys

LABELS = ("disclosed", "false_expectation", "flagged_unverified")


def kappa(pairs):
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    pa, pb = sum(a for a, _ in pairs) / n, sum(b for _, b in pairs) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def main(path):
    human = json.load(open(path))
    judge = {r["key"]: {k: r[k] == "True" for k in LABELS} for r in csv.DictReader(open("audit.csv"))}
    for k in LABELS:
        pairs = [(judge[i][k], h[k]) for i, h in human.items() if i in judge and isinstance(h.get(k), bool)]
        if not pairs:
            continue
        acc = sum(a == b for a, b in pairs) / len(pairs)
        dis = [i for i, h in human.items() if i in judge and isinstance(h.get(k), bool) and judge[i][k] != h[k]]
        print(f"{k:20} n={len(pairs):2}  agreement={acc:.0%}  kappa={kappa(pairs):.2f}  disagreements={dis}")


if __name__ == "__main__":
    main(sys.argv[1])
