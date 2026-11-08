"""A small client for an OpenAI-style chat server (Ollama), and reading a rule from an answer.

Standard library only. EoH and ReEvo used the same model through Ollama, with temperature 1.0.
"""
from __future__ import annotations

import json
import re
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

CODE_BLOCK = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)
IDEA_LINE = re.compile(r"^\s*\**Idea:?\**:?\s*(.+)$", re.MULTILINE | re.IGNORECASE)


class LLM:
    def __init__(self, model: str, base_url: str, temperature: float, timeout: float = 600, retries: int = 3):
        self.model, self.url, self.temperature = model, base_url.rstrip("/") + "/chat/completions", temperature
        self.timeout, self.retries = timeout, retries
        self.calls = 0
        self._lock = threading.Lock()  # ask_many counts calls from several threads

    def ask(self, system: str, user: str) -> str:
        body = json.dumps({"model": self.model, "temperature": self.temperature,
                           "messages": [{"role": "system", "content": system},
                                        {"role": "user", "content": user}]}).encode()
        request = urllib.request.Request(self.url, body, {"Content-Type": "application/json",
                                                          "Authorization": "Bearer local"})
        for attempt in range(self.retries):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    answer = json.loads(response.read())["choices"][0]["message"]["content"]
                with self._lock:
                    self.calls += 1
                return answer
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                if attempt == self.retries - 1:
                    raise
                time.sleep(5 * (attempt + 1))  # the model server may still be loading
        raise RuntimeError("unreachable")

    def ask_many(self, system: str, users: list[str]) -> list[str]:
        """Answers to several prompts, sent at the same time so the server answers them together."""
        with ThreadPoolExecutor(len(users)) as pool:
            return list(pool.map(lambda user: self.ask(system, user), users))


def read_rule(answer: str) -> tuple[str | None, str]:
    """(code, idea) from an answer; code is None when the answer has no priority function."""
    idea_match = IDEA_LINE.search(answer)
    idea = idea_match.group(1).strip() if idea_match else ""
    blocks = [b for b in CODE_BLOCK.findall(answer) if "def priority" in b]
    if blocks:
        return blocks[0].strip() + "\n", idea
    start = answer.find("def priority")
    return (answer[start:].strip() + "\n" if start >= 0 else None), idea
