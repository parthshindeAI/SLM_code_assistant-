"""
check_gpu.py - ONE command that tells you if everything is ready.

Run it from the project folder:

    python check_gpu.py

It prints your GPU, your PyTorch, your Ollama models, and the models that
fit your machine. Read the last line - it tells you what (if anything) to fix.
"""

import platform
import subprocess
import sys


def rule(title):
    print()
    print(title)
    print("-" * len(title))


def run(command):
    """Run a command and return its output as text."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=15)
        return (result.stdout or "").strip() or (result.stderr or "").strip()
    except FileNotFoundError:
        return "NOT INSTALLED (the command was not found on this computer)"
    except Exception as error:
        return "could not run: " + str(error)


def main():
    print("=" * 62)
    print("  Programming SLM - system check")
    print("=" * 62)
    print("python  :", sys.executable)
    print("version :", platform.python_version())
    print("windows :", platform.system(), platform.release())

    # ---------------------------------------------------------- the GPU
    rule("1. NVIDIA GPU")
    vram_mb = 0
    gpu_info = run(["nvidia-smi", "--query-gpu=name,memory.total",
                    "--format=csv,noheader,nounits"])
    if "NOT INSTALLED" in gpu_info or "could not run" in gpu_info:
        print("  no nvidia-smi found -> no NVIDIA GPU on this machine")
    else:
        for line in gpu_info.splitlines():
            print("  ", line)
            try:
                vram_mb = max(vram_mb, int(line.split(",")[1].strip()))
            except Exception:
                pass
        if vram_mb:
            print("  video memory : %.1f GB" % (vram_mb / 1024))

    # ---------------------------------------------------------- PyTorch
    rule("2. PyTorch (only needed for pictures)")
    torch_ok = False
    try:
        import torch
        print("  torch version  :", torch.__version__)
        print("  built with CUDA:", torch.version.cuda)
        cuda_ok = torch.cuda.is_available()
        print("  CUDA available :", cuda_ok)
        if cuda_ok:
            torch_ok = True
            print("  GPU name       :", torch.cuda.get_device_name(0))
            print("  -> pictures will be drawn on your GPU (fast)")
        else:
            print("  -> pictures would run on the CPU (1-3 minutes each)")
            print("  -> FIX IT WITH:")
            print("     pip install torch --index-url "
                  "https://download.pytorch.org/whl/cu124")
    except ImportError:
        print("  PyTorch is NOT installed")
        print("  -> FIX IT WITH:  pip install -r requirements.txt")

    # ---------------------------------------------------------- Ollama
    rule("3. Ollama (needed for code / PDF / PPT)")
    ollama = run(["ollama", "list"])
    print(ollama)
    if "NOT INSTALLED" in ollama or "could not run" in ollama:
        print("  -> FIX IT WITH: install Ollama from https://ollama.com/download")
    elif "NAME" not in ollama:
        print("  -> Ollama is installed but no model yet:")
        print("     ollama pull qwen2.5-coder:3b")

    # ------------------------------------------------------ what to use
    rule("4. Models that fit THIS machine")
    if vram_mb >= 7 * 1024:
        code_model = "qwen2.5-coder:7b"
    elif vram_mb >= 3.5 * 1024:
        code_model = "qwen2.5-coder:3b"
    else:
        code_model = "qwen2.5-coder:1.5b"
    print("  code model  :", code_model)
    print("  image model : stabilityai/sd-turbo")
    print("  (the app picks these for you automatically)")

    # ---------------------------------------------------------- verdict
    rule("5. Verdict")
    if not torch_ok:
        print("  MOSTLY READY - code, PDF and PPT work now.")
        print("  Only pictures are slow. Run the pip command above to use your GPU.")
    else:
        print("  ALL READY - code, PDF, PPT and pictures all use your GPU.")


if __name__ == "__main__":
    main()
