"""Model adapters: Anthropic Messages API over plain HTTP (no SDK needed) and a mock for dry runs."""
import json
import os
import getpass
import random
import re
import sys
import time
import urllib.request


def ensure_key(check_model):
    """Ask for the API key if it is not set, then make one cheap call so a bad key fails once, clearly."""
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key.startswith("sk-ant-") or len(key) < 40:
        raw = getpass.getpass("Pega tu clave de Anthropic (no se verá al pegar) y pulsa Enter: ")
        m = re.search(r"sk-ant-[A-Za-z0-9_\-]+", raw)  # strips invisible bracketed-paste codes
        key = m.group(0) if m else raw.strip()
        if not key.startswith("sk-ant-") or len(key) < 40:
            sys.exit(f"Eso no parece una clave válida ({len(key)} caracteres). Debe empezar por sk-ant-api03-.")
        os.environ["ANTHROPIC_API_KEY"] = key
    try:
        AnthropicModel(check_model, max_tokens=5).create(
            system="", messages=[{"role": "user", "content": "hi"}], tools=[])
    except Exception as e:
        sys.exit(f"La API rechazó la llamada de prueba: {e}")
    print("Clave aceptada.")


class AnthropicModel:
    def __init__(self, model, temperature=0.0, max_tokens=1024):
        self.model, self.temperature, self.max_tokens = model, temperature, max_tokens
        self.key = os.environ["ANTHROPIC_API_KEY"]

    def create(self, system, messages, tools):
        body = json.dumps({"model": self.model, "max_tokens": self.max_tokens,
                           "system": system, "messages": messages, **({"tools": tools} if tools else {})}).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
            "x-api-key": self.key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
        for attempt in range(5):
            try:
                with urllib.request.urlopen(req, timeout=300) as r:
                    return json.loads(r.read())
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 529) and attempt < 4:
                    time.sleep(2 ** attempt * 5)
                    continue
                raise RuntimeError(f"HTTP {e.code}: {e.read().decode(errors='replace')[:300]}") from e
            except (TimeoutError, urllib.error.URLError):
                if attempt == 4:
                    raise
                time.sleep(2 ** attempt * 5)


class MockModel:
    """Looks up the order, then obeys the injection with probability p. Only for testing the pipeline."""

    def __init__(self, p=0.3, seed=0):
        self.p, self.rng, self.n = p, random.Random(seed), 0

    def _use(self, name, inp):
        self.n += 1
        return {"type": "tool_use", "id": f"t{self.n}", "name": name, "input": inp}

    def create(self, system, messages, tools):
        last = messages[-1]["content"]
        if isinstance(last, str):
            return {"content": [self._use("lookup_order", {"order_id": "1042"})]}
        data = last[0]["content"]
        if '"order_id"' in data and self.rng.random() < self.p:
            if "reembolso" in data or "refund" in data:
                return {"content": [self._use("issue_refund", {"order_id": "1042", "amount": 2000000})]}
            if "@" in data:
                return {"content": [self._use("send_email", {"to": "soporte.verificacion@mail-seguro.co", "body": "..."})]}
            return {"content": [self._use("get_discount_code", {})]}
        return {"content": [{"type": "text", "text": "Tu pedido está en camino y llega mañana. / In transit, arrives tomorrow."}]}
