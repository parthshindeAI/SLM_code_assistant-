# MODEL_NOTES - which models we use, why, and the licences

## 1. The code model - Qwen2.5-Coder

| | |
|---|---|
| Ollama name | `qwen2.5-coder:7b` (8 GB) · `qwen2.5-coder:3b` (4 GB) · `qwen2.5-coder:1.5b` (fallback) |
| Family | Qwen2.5-Coder-Instruct (Apache 2.0) |
| Languages | **92 programming languages** (Python, C++, Java, JavaScript, Rust, Go, SQL, ...) |
| Human languages | accepts input in many languages - the app never blocks a language |
| VRAM (fp16) | 7B ≈ 4.7 GB · 3B ≈ 2.0 GB · 1.5B ≈ 1.0 GB |
| Why this one | best free coding quality per GB, small enough for a 3050, and the chat template is tuned for instructions |
| Licence | Apache 2.0 - free for school, competition and commercial use |
| Link | <https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct> |

**Prompt templates** (all in `src/code_model.py`):

| Task | Shape of the answer |
|---|---|
| `generate` | one code block only |
| `complete` | one code block only, same style |
| `debug` | fixed code block + an `Explanation:` paragraph |
| `explain` | short bullet points for a beginner |
| `qa` | pass-through - used by the PDF and PPT features |

We inject your text with `.replace("{{INPUT}}", text)` and **never**
`.format()`, because pasted code is full of `{ }` braces that would crash
`.format()`.

---

## 2. The image model - SD-Turbo

| | Value |
|---|---|
| Diffusers id | `stabilityai/sd-turbo` |
| Steps | 1-4 (default 4) |
| Guidance scale | `0.0` |
| Image size | 512×512 recommended |
| License | Review the Stability AI Community License and model card for usage terms. |
| Model card | <https://huggingface.co/stabilityai/sd-turbo> |

SD-Turbo is designed for very fast generation. It can produce imperfect
details, misinterpret complex prompts, and does not reliably render legible
text or exact object counts.

The pipeline is loaded once and reused for subsequent images. Hugging Face
caches model weights on disk. If the default user cache already contains
SD-Turbo, the app loads it locally without downloading another copy.

The app uses the local PyTorch device:

```python
torch.cuda.is_available()  ->  GPU path, float16
otherwise                  ->  CPU path, float32 (slow)
```

---

## 3. VRAM guide for the RTX 3050

| VRAM | Code model | Image model | Notes |
|---|---|---|---|
| 8 GB (desktop) | `qwen2.5-coder:7b` | `stabilityai/sd-turbo` | GPU generation |
| 4 GB (laptop) | `qwen2.5-coder:3b` | `stabilityai/sd-turbo` | GPU generation |
| No NVIDIA GPU | `qwen2.5-coder:1.5b` | `stabilityai/sd-turbo` on CPU | Works, but slow |

The app reads `nvidia-smi` at startup and chooses the code model for you
(`src/code_model.py` → `detect_vram_mb()` and `suggest_model()`).

**The 7B model on a 4 GB card:** it *does* still run - Ollama offloads part of
it to the CPU - but it drops to roughly 2-5 tokens/s, which feels broken in a
demo. Use the 3B model on a 4 GB card.

**PyTorch with CUDA:** the plain `pip install torch` wheel is the **CPU-only**
build, so `torch.cuda.is_available()` returns `False` even on a good GPU. For Windows NVIDIA users, the project script tries the available CUDA
channels and verifies that PyTorch can use the GPU:

```bat
install_cuda_torch.bat
```

Then check with `python -c "import torch; print(torch.cuda.is_available())"` -
it should print `True`.

Check your card:

```bash
nvidia-smi
```

or from inside Python:

```python
import torch
print(torch.cuda.is_available())
print(torch.cuda.get_device_properties(0).total_memory / 1024**3, "GB")
```

---

## 4. Everything else is a normal Python library

| Library | Licence | Used for |
|---|---|---|
| Ollama | MIT | serving the code model locally |
| Streamlit | Apache 2.0 | the chat interface |
| requests | Apache 2.0 | the HTTP call to Ollama |
| PyMuPDF | AGPL-3.0 (or commercial licence) | reading PDF text |
| python-pptx | MIT | writing the .pptx file |
| PyTorch | BSD-3-Clause | running the diffusion model |
| diffusers / transformers / accelerate | Apache 2.0 | the diffusion pipeline |
| google-api-python-client / google-auth-oauthlib | Apache 2.0 | the optional Google sign-in |

---

## 5. Honest limits of this project

* The PDF reader is **not** OCR - a scanned PDF has no text layer and the app
  will tell you so.
* PDF answering uses **keyword scoring** to pick the relevant part of the
  document. Embeddings + a proper RAG pipeline is the natural next step.
* SD-Turbo is optimized for speed and can misinterpret prompts, struggle with
  exact object counts, and cannot reliably render readable text.
* The 7B model is a small model: it can be wrong. Always read the code it
  gives you before running it.
* No code is ever executed by the app - the "debug" task only *explains* the
  fix, it never runs your code.
