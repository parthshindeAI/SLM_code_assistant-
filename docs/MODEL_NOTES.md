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

## 2. The image model - SDXL-Turbo / SD-Turbo

| | SDXL-Turbo | SD-Turbo |
|---|---|---|
| Diffusers id | `stabilityai/sdxl-turbo` | `stabilityai/sd-turbo` |
| Use it when | VRAM **≥ 7 GB** (desktop RTX 3050) | VRAM **~4 GB** (laptop) or CPU |
| Size | 512×512 fast, 768×768 nicer | 512×512 |
| Steps | 1-4 (default 2) | 1-4 (default 2) |
| Guidance scale | `0.0` (turbo models are trained for it) | `0.0` |
| VRAM (fp16) | ≈ 7 GB | ≈ 2.5 GB |
| Licence | STABILITY AI NON-COMMERCIAL licence - **free for learning, school and this competition project**; check the model card before commercial use | same |
| Link | <https://huggingface.co/stabilityai/sdxl-turbo> | <https://huggingface.co/stabilityai/sd-turbo> |

The app picks the model automatically:

```python
torch.cuda.is_available()  ->  GPU path, float16, fast
otherwise                  ->  CPU path, float32, slow but it works
```

The pipeline is created **once** and kept in a global variable, so the weights
are read from disk only on the first picture.

---

## 3. VRAM guide for the RTX 3050

| VRAM | Code model | Image model | Notes |
|---|---|---|---|
| 8 GB (desktop) | `qwen2.5-coder:7b` | `stabilityai/sdxl-turbo` | best quality, ~15-30 tokens/s |
| 4 GB (laptop) | `qwen2.5-coder:3b` | `stabilityai/sd-turbo` | `1.5b` if you want it faster |
| No NVIDIA GPU | `qwen2.5-coder:1.5b` | `stabilityai/sd-turbo` on CPU | works, but slow |

The app reads `nvidia-smi` at startup and chooses the right one for you
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
| google-api-python-client / google-auth-oauthlib | Apache 2.0 | the optional Gmail sign-in |

---

## 5. Honest limits of this project

* The PDF reader is **not** OCR - a scanned PDF has no text layer and the app
  will tell you so.
* PDF answering uses **keyword scoring** to pick the relevant part of the
  document. Embeddings + a proper RAG pipeline is the natural next step.
* The 7B model is a small model: it can be wrong. Always read the code it
  gives you before running it.
* No code is ever executed by the app - the "debug" task only *explains* the
  fix, it never runs your code.
