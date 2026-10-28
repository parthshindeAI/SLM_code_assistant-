"""
code_model.py - ask a programming model that runs on YOUR computer.

We talk to Ollama over plain HTTP (http://localhost:11434).
No OpenAI / Gemini / HuggingFace inference API is used anywhere.

Four coding tasks share ONE model:
    generate  -> describe a task, get code
    complete  -> paste half code, get the whole thing
    debug     -> paste buggy code, get a fix + explanation
    explain   -> paste code, get a simple explanation
plus one pass-through task:
    qa        -> used by the PDF and PPT features
"""

import subprocess

import requests

# --------------------------------------------------------------------- config
OLLAMA_URL = "http://localhost:11434/api/generate"
TAGS_URL = "http://localhost:11434/api/tags"

# 8 GB VRAM (RTX 3050 desktop) -> 7b, 4 GB VRAM (laptop) -> 3b
DEFAULT_MODEL = "qwen2.5-coder:7b"
FALLBACK_MODELS = ["qwen2.5-coder:7b", "qwen2.5-coder:3b", "qwen2.5-coder:1.5b"]

TIMEOUT = 600  # seconds - a 7b model on a slow laptop needs time


class OllamaError(Exception):
    """A friendly error we can show in the chat instead of a traceback."""


# ------------------------------------------------------------------ templates
# Every template uses the placeholder {{INPUT}}.
# We fill it with .replace() and NEVER .format(), because user code is full
# of { } braces and .format() would crash on them.
TEMPLATES = {
    "generate": (
        "You are an expert software engineer. Write clean, working code for the task.\n"
        "Return ONLY one code block (```) with the final code - no extra talk.\n"
        "Add short comments inside the code to explain the tricky parts.\n\n"
        "TASK:\n{{INPUT}}"
    ),
    "complete": (
        "Complete the code below. Return ONLY the full finished code in one code block.\n"
        "Keep the same style, do not add a chatty explanation.\n\n"
        "CODE TO COMPLETE:\n```\n{{INPUT}}\n```"
    ),
    "debug": (
        "Find the bug in the code below and return the FIXED code in one code block.\n"
        "After the code block write a short paragraph that starts with 'Explanation:'\n"
        "and says what was wrong and why your fix works.\n\n"
        "BUGGY CODE:\n```\n{{INPUT}}\n```"
    ),
    "explain": (
        "Explain the code below in simple, easy-to-read words for a beginner student.\n"
        "Use short bullet points. Explain any jargon the first time you use it.\n"
        "Do not rewrite the code, just explain it.\n\n"
        "CODE:\n```\n{{INPUT}}\n```"
    ),
    # 'qa' is a pass-through: the caller writes the full instruction itself.
    "qa": (
        "You are a helpful and precise assistant. Follow the instructions exactly.\n"
        "If the instructions ask for a specific format, use that format and nothing else.\n\n"
        "{{INPUT}}"
    ),
}


def build_prompt(task, user_text):
    """Turn a task + the user's text into the final prompt for the model."""
    template = TEMPLATES.get(task, TEMPLATES["qa"])
    # .replace() is safe even when the user pastes code full of { } braces.
    return template.replace("{{INPUT}}", user_text)


# ------------------------------------------------------------------- talking
def ask(prompt, task="qa", model=DEFAULT_MODEL, context=""):
    """Send a prompt to the local Ollama model and return its reply as text.

    `context` is optional: put the earlier chat turns in it so the model
    understands follow-up questions like "now make it faster".
    Raises OllamaError with a friendly message if Ollama is not reachable.
    """
    full_prompt = build_prompt(task, prompt)
    if context:
        # we add the memory AFTER the instruction, so the template still works
        full_prompt += ("\n\nEARLIER CONVERSATION (use it only as context):\n" + context)
    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": False,
        "options": {"temperature": 0.2},
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise OllamaError(
            "Could not reach Ollama. Open a terminal and run  ollama serve  "
            "(then  ollama pull " + model + "  if the model is missing)."
        )
    except requests.exceptions.Timeout:
        raise OllamaError(
            "The model took too long to answer. Try a smaller model such as "
            "qwen2.5-coder:3b in the sidebar."
        )
    except requests.exceptions.RequestException as error:
        raise OllamaError("Ollama request failed: " + str(error))

    try:
        data = response.json()
    except ValueError:
        raise OllamaError("Ollama replied with something that was not valid JSON.")

    reply = data.get("response", "").strip()
    if not reply:
        raise OllamaError("Ollama returned an empty answer. Try again with a clearer prompt.")
    return reply


# ------------------------------------------------------------------- helpers
def detect_vram_mb():
    """Ask nvidia-smi how much video memory this machine has.

    Returns 0 when there is no NVIDIA GPU. We use nvidia-smi (not torch)
    because torch may not be installed yet.
    """
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return 0
        first_line = result.stdout.strip().splitlines()[0].strip()
        return int(first_line)
    except Exception:
        return 0


def suggest_model():
    """Return (model_name, note) - a model that fits THIS machine's GPU."""
    vram_mb = detect_vram_mb()
    if vram_mb == 0:
        return DEFAULT_MODEL, "No NVIDIA GPU found - " + DEFAULT_MODEL + \
            " will run on the CPU (slow, but it works)."

    vram_gb = vram_mb / 1024
    if vram_gb >= 7:
        return "qwen2.5-coder:7b", ("Detected " + ("%.0f" % vram_gb) +
                                    " GB VRAM - the 7B model fits nicely.")
    if vram_gb >= 3.5:
        return "qwen2.5-coder:3b", ("Detected " + ("%.1f" % vram_gb) +
                                    " GB VRAM - the 3B model fits; the 7B one would be very slow.")
    return "qwen2.5-coder:1.5b", ("Detected " + ("%.1f" % vram_gb) +
                                  " GB VRAM - only the 1.5B model fits comfortably.")


def is_running():
    """True if the local Ollama server is answering right now."""
    try:
        requests.get(TAGS_URL, timeout=3)
        return True
    except Exception:
        return False


def list_models():
    """Return the names of the models you already pulled (empty list if offline)."""
    try:
        response = requests.get(TAGS_URL, timeout=5)
        response.raise_for_status()
        return [item.get("name", "") for item in response.json().get("models", [])]
    except Exception:
        return []


def split_code_blocks(text):
    """Split a reply into parts so the UI can show code nicely.

    Returns a list of (kind, content) where kind is 'code' or 'text'.
    """
    parts = []
    inside = False
    buffer = []
    for line in text.splitlines():
        if line.strip().startswith("```"):
            if inside:
                parts.append(("code", "\n".join(buffer).strip()))
                buffer = []
                inside = False
            else:
                inside = True
        elif inside:
            buffer.append(line)
        else:
            parts.append(("text", line))
    if inside and buffer:          # reply ended while still inside a block
        parts.append(("code", "\n".join(buffer).strip()))

    # glue neighbouring plain-text lines back together
    merged = []
    for kind, content in parts:
        if kind == "text":
            if merged and merged[-1][0] == "text":
                merged[-1] = ("text", merged[-1][1] + "\n" + content)
            else:
                merged.append(("text", content))
        else:
            merged.append((kind, content))
    return merged
