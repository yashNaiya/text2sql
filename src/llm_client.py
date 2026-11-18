"""LLM clients: Ollama (real) plus stubs for testing the harness without a model."""
import os
import re

import requests

from sql_guard import UNAUTHORIZED


class OllamaClient:
    def __init__(self, model: str = "qwen2.5-coder:3b", host: str | None = None,
                 num_ctx: int = 8192, timeout: int = 300):
        host = host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.host = host if host.startswith("http") else f"http://{host}"
        self.model, self.num_ctx, self.timeout = model, num_ctx, timeout

    def check_ready(self):
        try:
            r = requests.get(f"{self.host}/api/tags", timeout=10)
            r.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Cannot reach Ollama at {self.host}. Start it with `ollama serve`.") from e
        names = [m["name"] for m in r.json().get("models", [])]
        if not any(n == self.model or n.split(":")[0] == self.model for n in names):
            raise RuntimeError(f"Model {self.model!r} not found. Run: ollama pull {self.model}\n"
                               f"Installed: {names or 'none'}")

    def chat(self, messages: list) -> str:
        r = requests.post(f"{self.host}/api/chat", timeout=self.timeout, json={
            "model": self.model, "messages": messages, "stream": False,
            "options": {"temperature": 0, "seed": 0, "num_ctx": self.num_ctx, "num_predict": 512},
        })
        r.raise_for_status()
        return r.json()["message"]["content"]


def _question_of(messages: list) -> str:
    m = re.search(r"<question>\n(.*?)\n</question>", messages[-1]["content"], re.S)
    return m.group(1) if m else ""


class OracleStub:
    """Returns the gold SQL for known questions, a refusal otherwise.
    Lets us verify the harness end to end: it should score 100%."""
    def __init__(self, gold: dict):
        self.gold = gold

    def check_ready(self):
        pass

    def chat(self, messages):
        return self.gold.get(_question_of(messages), UNAUTHORIZED)


class FixedStub:
    """Always answers with the same text (used for failure-path and leak tests)."""
    def __init__(self, reply: str):
        self.reply = reply

    def check_ready(self):
        pass

    def chat(self, messages):
        return self.reply


def get_client(name: str, gold: dict | None = None):
    if name == "stub-oracle":
        return OracleStub(gold or {})
    if name == "stub-bad":
        return FixedStub("SELECT * FROM nonexistent_table;")
    if name == "stub-wrong":
        return FixedStub("SELECT COUNT(*) FROM orders;")  # valid, executes, almost never correct
    if name == "stub-leaky":
        return FixedStub("SELECT payment_type, SUM(payment_value) FROM order_payments GROUP BY payment_type;")
    return OllamaClient(model=name)
