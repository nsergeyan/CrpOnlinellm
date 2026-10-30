"""A fake OpenAI-style LLM server for the framework tests (canned answers, no API key, no cost)."""
import itertools
import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HINT = "Prefer stacks with low RI; never add DIFF."


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
