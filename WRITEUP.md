# Refuses the action, repeats the lie: how a customer-service agent handles injected notes in Spanish and English

*Carlos Betancur Gálvez — DRAFT, November 2026. Code and data: https://github.com/cabetan/injection-es.*
*AI assistance: the experiment code and this write-up were produced with substantial help from Claude (Anthropic). The research question, the choice of the small-business deployment setting and the interpretation are mine. I'm stating this plainly because it is part of the method.*

## TL;DR

- I tested a tool-using customer-service agent (Claude Haiku) that reads untrusted text (order notes, reviews, inbound emails) while answering a routine question. I ran ~1,450 episodes across Spanish, English and a mixed condition.
- **It never took the injected action.** That held for 0 of 1,450 episodes across three rounds: explicit attacks ("ignore your instructions"), policy-compatible attacks (an "already approved" refund, an "updated" customer email), and the same attacks with a minimal system prompt of the kind small businesses actually deploy.
- **It did repeat the injected content to the customer** in 81–98% of episodes, depending on condition. In roughly a quarter to a third of refund/email cases, the reply could leave the customer believing the false claim, for example that a refund was approved.
- **Language mattered for *how* it repeated it.** With a strict policy prompt, the agent flagged the note as unverified in **86% of English replies vs 71% of Spanish replies** (paired McNemar, p = 0.006).
- **A more explicit policy prompt made false expectations *more* common** (34–38% vs 24–25%) and warnings *less* common, compared to a minimal prompt.
- Common prompt defenses barely reduced disclosure: 100% with no defense, 90% with a warning, 82% with spotlighting.

## Why this matters

Agents deployed by small businesses in Latin America read third-party text all day: WhatsApp messages, CRM notes, reviews. Most prompt-injection work measures whether the agent *does* the attacker's action, and in English. In deployment there is a second failure mode: the agent refuses the action but **relays the attacker's claim to a real customer** ("your note says a 150,000 COP refund was approved"). That creates false promises, support load and, potentially, legal exposure, with no tool call ever being made. I wanted to know whether either failure depends on language.

## Setup

**Agent.** A support assistant for a fictional Colombian clothing store, with four tools: `lookup_order`, `issue_refund`, `send_email` and `get_discount_code`. The customer asks a benign question ("what's the status of order #1042?"). The injected text appears only inside the `lookup_order` result, as an order note, a product review or an inbound email (indirect injection).

**Conditions.**
- *Language:* full Spanish, full English, and a Spanish scenario with an English injection. The ES/EN templates are hand-written to be parallel.
- *Defense:* none; a warning that tool output is untrusted; spotlighting (the warning plus explicit delimiters).
- *System prompt:* **strict** (explicit refund/email/discount-code policy) or **minimal** ("help customers with their orders").
- *Attack goals:* unauthorized refund, sending customer data to a non-registered email, and revealing an internal discount code.

**Rounds.**
1. Explicit attacks in 6 styles (direct, fake system message, authority, urgency, polite, buried in filler), strict prompt. 486 episodes.
2. Policy-compatible attacks in 3 framings (CRM record, colleague's handover note, the customer's own earlier message), strict prompt, plus a vague customer follow-up ("anything else pending?"). 486 episodes.
3. Round 2 with the minimal prompt. 478 episodes; 8 were lost to network timeouts.

**Measurement.** Attack success is detected programmatically from tool calls. Disclosure is labelled by an LLM judge (Claude Sonnet) that reads the injected note and the agent's replies and answers three yes/no questions: *disclosed* specific content, created a *false expectation*, *flagged* the note as unverified. The judge works in either language and judges meaning, not keywords. An earlier keyword detector missed cross-language paraphrases, which is why I switched.

## Results

### 1. No injected action was ever taken

| Round | Episodes | Attack success |
|---|---|---|
| 1 — explicit | 486 | 0 (95% CI upper bound 6.6% per cell) |
| 2 — policy-compatible, strict prompt | 486 | 0 |
| 3 — policy-compatible, minimal prompt | 478 | 0 |

Across all rounds the only tool the agent called was `lookup_order`. Even with no written policy, it reasoned that it shouldn't process a refund the customer had not requested and that it couldn't verify.

### 2. But it relayed the injected content

Refund and email goals only (n = 615 judged; see Limitations for the discount-code goal):

| Prompt | Language | Disclosed | False expectation | Flagged as unverified |
|---|---|---|---|---|
| strict | EN | 98% | 38% | **86%** |
| strict | ES | 89% | 34% | **71%** |
| strict | ES + EN injection | 89% | 35% | 64% |
| minimal | EN | 95% | 25% | 98% |
| minimal | ES | 91% | 25% | 94% |
| minimal | ES + EN injection | 81% | 24% | 95% |

Paired comparisons on identical items (ES vs EN, McNemar):
- Flagged as unverified, strict prompt: 6 pairs where only the Spanish reply flagged vs 21 where only the English reply did, **p = 0.006**.
- Disclosed, strict prompt: 1 vs 10, p = 0.012. English replies disclose *more*.
- False expectation: no significant language difference (p > 0.3).

So, in Spanish the agent was slightly quieter about the note, but when it did mention it, it was less likely to tell the customer it couldn't be trusted.

### 3. The strict prompt traded safety of actions for safety of words

Compared to the minimal prompt, the strict policy prompt produced *more* false expectations (34–38% vs 24–25%) and *fewer* warnings (64–86% vs 94–98%). One reading: with an explicit refund policy, the agent tends to frame the note in policy terms ("I can't process that refund unless you ask"), which implicitly confirms that a refund exists. With no policy it falls back on generic skepticism. I have not tested this mechanism; it is a hypothesis.

### 4. Prompt defenses help a little

Disclosure (refund + email): no defense 100%, warning 90%, spotlighting 82%. Telling the model that tool output is untrusted stops it from acting, which it already didn't do, but it doesn't stop it from repeating the content.

## Limitations

- **One model, one scenario.** Only Claude Haiku and one synthetic store. Results may not transfer to other models or real deployments.
- **The judge is a model, and not yet validated against human labels.** I read transcripts informally while building the study, but a blind hand-labelled agreement check (`revision.html` → `agreement.py`) is still pending. Treat the disclosure numbers as provisional until it is done.
- **Missing judgments.** The judge returned empty output on 106 of 964 episodes, 81 of them on the discount-code goal, so I exclude that goal from the headline numbers. I have not diagnosed the cause.
- **Multiple comparisons.** I ran several paired tests. The p = 0.006 result survives a Bonferroni correction over the six language comparisons reported; p = 0.012 is borderline.
- **Is disclosure always bad?** Telling the customer "there's a note claiming X, which I can't verify" is arguably transparent. That is why I report *flagged* and *false expectation* separately from raw disclosure.
- **No temperature control.** The model does not accept a temperature parameter. Round 2 used two samples per item; the others used one.
- **Translation.** The ES/EN templates were written by a native Spanish speaker but not back-translated.

## What I'd do next

1. Repeat on more models, including open-weight models commonly used by small businesses, to see whether the action-refusal result is Claude-specific.
2. Test the "policy framing confirms the claim" hypothesis directly with prompt ablations.
3. Build a defense aimed at the disclosure failure itself. For example, an instruction or classifier that rewrites relayed third-party claims as explicitly unverified. Then measure false expectations, not just actions.
4. Use real, anonymized WhatsApp support conversations from deployed agents, with consent, instead of a synthetic store.

## Reproduce

```bash
python3 run.py --round 1 --models claude-haiku-5-5 --out results/haiku.jsonl
python3 run.py --round 2 --models claude-haiku-5-5 --samples 2 --out results/r2-haiku.jsonl
python3 run.py --round 2 --policy minimal --models claude-haiku-5-5 --samples 2 --out results/r2-minimal-haiku.jsonl
python3 judge.py results/r2-haiku.jsonl results/r2-minimal-haiku.jsonl
python3 judge.py --summary results/r2-haiku.judged.jsonl results/r2-minimal-haiku.judged.jsonl
python3 build_audit_page.py && open revision.html   # blind hand labels
python3 agreement.py ~/Downloads/human_labels.json
```
