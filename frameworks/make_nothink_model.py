"""Create an Ollama copy of a Qwen3 model that never thinks, e.g. qwen3:14b -> qwen3:14b-nothink.

Ollama appends its own "/think" after the prompt (thinking is on by default), so a
"/no_think" written in the prompt is overruled. This copy changes only Qwen3's chat template:
it always ends the user message with "/no_think" and starts the answer with an empty
<think></think> block, which is Qwen3's official non-thinking mode (enable_thinking=False).
The model weights are the same; EoH and ReEvo both just use the new model name.

    python frameworks/make_nothink_model.py qwen3:14b
"""
import subprocess
import sys
import tempfile
from pathlib import Path

# the two "thinking off" branches of Qwen3's Ollama template, made unconditional
USER_SWITCH = '''{{- if and $.IsThinkSet (eq $i $lastUserIdx) }}
   {{- if $.Think -}}
      {{- " "}}/think
   {{- else -}}
      {{- " "}}/no_think
   {{- end -}}
{{- end }}<|im_end|>'''
EMPTY_THINK = '''{{ if and $.IsThinkSet (not $.Think) -}}
<think>

</think>

{{ end -}}'''


def make(base: str) -> str:
    modelfile = subprocess.run(["ollama", "show", base, "--modelfile"],
                               capture_output=True, text=True, check=True).stdout
    template = modelfile[modelfile.index('TEMPLATE """'):]
    template = template[:template.index('"""', len('TEMPLATE """')) + 3]
    if USER_SWITCH not in template or EMPTY_THINK not in template:
        raise SystemExit(f"{base}: template does not look like Qwen3's; nothing created")
    template = template.replace(USER_SWITCH, "{{- if eq $i $lastUserIdx }} /no_think{{ end }}<|im_end|>")
    template = template.replace(EMPTY_THINK, "<think>\n\n</think>\n\n")

    name = f"{base}-nothink"
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "Modelfile"
        path.write_text(f"FROM {base}\n{template}\n")
        subprocess.run(["ollama", "create", name, "-f", str(path)], check=True)
    return name


if __name__ == "__main__":
    print("created", make(sys.argv[1]))
