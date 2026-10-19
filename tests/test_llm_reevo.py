"""ReEvo and the original EoH (bundled with ReEvo) end to end with a FAKE LLM server.

Canned answers, no API key, no cost. Both frameworks are untouched: they talk to the fake
server through ReEvo's normal base_url setting. Skipped until scripts/setup_reevo.sh has run.
"""
import itertools
import json
import os
import re
import subprocess
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from crp.paths import ROOT

REEVO = Path(os.environ.get("REEVO_DIR", ROOT / "frameworks" / "reevo")).resolve()
pytestmark = pytest.mark.skipif(not (REEVO / ".venv" / "bin" / "python").exists(),
                                reason="ReEvo not set up (bash scripts/setup_reevo.sh)")

SIGNATURE = "def priority_v2(SH: float, EMP: float, AVG: float, CUR: float, RI: float, DIFF: float) -> float:"
# Totals on the training set at alpha 0.5: return RI = 26,452; math.sqrt(SH) + 100 * RI = 27,047
HINT = "Prefer stacks with low RI; never add DIFF."

# ReEvo: plain code blocks
REEVO_ANSWERS = [f"```python\n{SIGNATURE}\n    {body}\n```" for body in [
    "return RI",
    "return SH + 10 * RI",
    "return math.sqrt(SH) + 100 * RI",  # math without import: our compile_rule provides it
    "return float('nan')",              # invalid
]]

# Original EoH: {idea} + code. EoH cuts the code at the last 'return' and appends the output
# name, so only rules that end with 'return priority' survive; 'return SH' becomes
# 'return priority' and fails with NameError (original paper code, not our change).
EOH_ANSWERS = [f"{{{idea}}}\n```python\n{SIGNATURE}\n{body}\n```" for idea, body in [
    ("Choose the stack that blocks the fewest containers.", "    priority = RI\n    return priority"),
    ("Lowest stack, returned directly.", "    return SH"),
    ("Square root of height plus heavy RI penalty.", "    priority = math.sqrt(SH) + 100 * RI\n    return priority"),
    ("Always NaN.", "    priority = float('nan')\n    return priority"),
]]


@contextmanager
def fake_llm(answers: list[str]):
    """A tiny OpenAI-style server that cycles through canned answers."""
    replies = itertools.cycle(answers)
    lock = threading.Lock()  # the frameworks send several requests at the same time

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            prompt = body["messages"][-1]["content"]
            with lock:
                content = HINT if "hints" in prompt else next(replies)  # ReEvo's reflections ask for hints
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
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1"
    finally:
        server.shutdown()


def run_main(algorithm: str, answers: list[str], out: Path) -> tuple[str, list[float]]:
    """Run ReEvo's main.py against the fake LLM; return its log and every score it logged."""
    venv_bin = REEVO / ".venv" / "bin"
    with fake_llm(answers) as url:
        done = subprocess.run(
            [str(venv_bin / "python"), "main.py", "problem=crp_online", f"algorithm={algorithm}",
             "llm_client=openai", "llm_client.model=fake", "llm_client.api_key=fake",
             f"+llm_client.base_url={url}", "init_pop_size=6", "pop_size=4", "max_fe=10",
             "timeout=60", f"hydra.run.dir={out}"],
            cwd=REEVO, capture_output=True, text=True, timeout=600,
            env={**os.environ, "PATH": f"{venv_bin}:{os.environ['PATH']}"},  # eval.py runs with ReEvo's python
        )
    log = re.sub(r"\x1b\[[0-9;]*m", "", done.stdout + done.stderr)  # drop terminal colours
    assert done.returncode == 0, log[-3000:]
    return log, [float(s) for s in re.findall(r"Objective value: (\S+)", log)]


def test_reevo_runs_with_fake_llm(tmp_path):
    log, scores = run_main("reevo", REEVO_ANSWERS, tmp_path)
    assert scores[0] == 29_695                    # ReEvo scores the seed rule (return SH) first
    assert float("inf") in scores                 # the NaN rule was marked invalid
    assert 27_047 in scores                       # math without import works
    assert min(scores) == 26_452                  # best = return RI
    assert re.search(r"Best obj: 26452\.0", log)
    assert "val skipped" in log


def test_original_eoh_runs_with_fake_llm(tmp_path):
    log, scores = run_main("eoh", EOH_ANSWERS, tmp_path)
    assert min(scores) == 26_452                  # best = priority = RI
    assert 27_047 in scores
    assert float("inf") in scores                 # NaN rule and 'return SH' rule failed
    # proof of the cut-at-return behaviour: 'return SH' was turned into 'return priority'
    stdouts = "".join(p.read_text() for p in (tmp_path / "evaluations").glob("*_stdout.txt"))
    assert "NameError: name 'priority' is not defined" in stdouts
    assert "val skipped" in log
