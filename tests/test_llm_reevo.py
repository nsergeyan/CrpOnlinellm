"""The real ReEvo end to end with a FAKE LLM server: canned answers, no API key, no cost.

ReEvo is untouched: it talks to the fake server through its normal base_url setting.
Skipped until scripts/setup_reevo.sh has been run.
"""
import itertools
import json
import os
import re
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from crp.paths import ROOT

REEVO = Path(os.environ.get("REEVO_DIR", ROOT / "frameworks" / "reevo"))
pytestmark = pytest.mark.skipif(not (REEVO / ".venv" / "bin" / "python").exists(),
                                reason="ReEvo not set up (bash scripts/setup_reevo.sh)")

SIGNATURE = "def priority_v2(SH: float, EMP: float, AVG: float, CUR: float, RI: float, DIFF: float) -> float:"
RULES = {  # body -> total on the training set at alpha 0.5
    "return RI": 26_452,
    "return SH + 10 * RI": 27_049,
    "return math.sqrt(SH) + 100 * RI": 27_047,  # math without import: our compile_rule provides it
    "return float('nan')": None,                # invalid
}
HINT = "Prefer stacks with low RI; never add DIFF."


def answer(prompt: str, rules) -> str:
    if "hints" in prompt:  # ReEvo's short- and long-term reflection prompts ask for hints
        return HINT
    return f"```python\n{SIGNATURE}\n    {next(rules)}\n```"


@pytest.fixture
def fake_llm():
    rules = itertools.cycle(RULES)
    lock = threading.Lock()  # ReEvo sends several requests at the same time

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            with lock:
                content = answer(body["messages"][-1]["content"], rules)
            reply = json.dumps({
                "id": "fake", "object": "chat.completion", "created": 0, "model": body["model"],
                "choices": [{"index": 0, "finish_reason": "stop",
                             "message": {"role": "assistant", "content": content}}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(reply)))
            self.end_headers()
            self.wfile.write(reply)

        def log_message(self, *args):  # keep test output quiet
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)  # port 0 = any free port
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}/v1"
    server.shutdown()


def test_reevo_runs_with_fake_llm(fake_llm, tmp_path):
    venv_bin = REEVO / ".venv" / "bin"
    out = subprocess.run(
        [str(venv_bin / "python"), "main.py", "problem=crp_online", "llm_client=openai",
         "llm_client.model=fake", "llm_client.api_key=fake", f"+llm_client.base_url={fake_llm}",
         "init_pop_size=6", "pop_size=4", "max_fe=10", "timeout=60", f"hydra.run.dir={tmp_path}"],
        cwd=REEVO, capture_output=True, text=True, timeout=600,
        env={**os.environ, "PATH": f"{venv_bin}:{os.environ['PATH']}"},  # eval.py runs with ReEvo's python
    )
    log = re.sub(r"\x1b\[[0-9;]*m", "", out.stdout + out.stderr)  # drop terminal colours
    assert out.returncode == 0, log[-3000:]

    scores = [float(s) for s in re.findall(r"Objective value: (\S+)", log)]
    assert scores[0] == 29_695                    # ReEvo scores the seed rule (return SH) first
    assert float("inf") in scores                 # the NaN rule was marked invalid
    assert 27_047 in scores                       # math without import works
    assert min(scores) == 26_452                  # best = return RI
    assert re.search(r"Best obj: 26452\.0", log)
    assert "val skipped" in log
