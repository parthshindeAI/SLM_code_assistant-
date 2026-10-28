# 🤖 Programming SLM

A **ChatGPT-style programming assistant that runs completely offline on your own
computer**. No OpenAI key, no Gemini key, no HuggingFace inference key - not
anywhere in the code.

Built with **Ollama** (for code, PDF and PowerPoint work) and **diffusers**
(for pictures), wrapped in a clean **Streamlit** interface.

| Mode | What it does | Where the work happens |
|---|---|---|
| 💻 Code | write / finish / debug / explain code | local Ollama model |
| 📄 PDF Q&A | upload a PDF, ask questions about it | pymupdf (CPU) + local Ollama model |
| 🎨 Image | type a prompt, get a picture | local diffusers model (GPU if you have one) |
| 📊 PPT | give a topic, get a downloadable `.pptx` | local Ollama model + python-pptx (CPU) |

---

## 1. Setup (10 minutes, one time)

### Step 0 — one command to see if you are ready

```bash
python check_gpu.py
```

It prints your GPU, your PyTorch, your Ollama models, the models that fit
your machine, and the last line tells you exactly what (if anything) to fix.
Run it any time something feels wrong.

### Step 0b — if you have an NVIDIA GPU, get the CUDA build of PyTorch

The plain `pip install torch` wheel is the **CPU-only** build, so pictures
would be drawn on the CPU (1-3 minutes each). Run this **once**:

```bat
install_cuda_torch.bat
```

Right click the file -> *Run*, or type `.\install_cuda_torch.bat`. It tries
the CUDA 12.8 / 12.6 / 12.4 builds in order, checks that your GPU is really
being used, and puts the CPU build back if none of them work.

> If pictures are using the CPU on a Windows machine with an NVIDIA GPU,
> run `install_cuda_torch.bat` again to install and verify a CUDA build.

### Step 1 — check your GPU

Open a terminal (PowerShell in VS Code is fine) and run:

```bash
nvidia-smi
```

Look at the **memory** line in the top-right box:

* **8 GB** (desktop RTX 3050) → use `qwen2.5-coder:7b` and `stabilityai/sdxl-turbo`
* **4 GB** (laptop RTX 3050) → use `qwen2.5-coder:3b` and `stabilityai/sd-turbo`

The app detects this for you, but knowing the number helps you pick the model.

### Step 2 — install Ollama and pull a model

1. Download Ollama from <https://ollama.com/download> (Windows installer).
2. Open a terminal and run:

```bash
ollama pull qwen2.5-coder:7b      # 8 GB VRAM
ollama pull qwen2.5-coder:3b      # 4 GB VRAM  (smaller, faster)
```

3. Ollama starts itself on most installs. If it does not, run `ollama serve`
   once and leave that terminal open. Check it with `ollama list`.

### Step 3 — Python environment in VS Code

1. Open this folder in VS Code.
2. `Ctrl+Shift+P` → **Python: Create Environment** → **Venv**.
3. Press `Ctrl+Shift+P` → **Python: Select Interpreter** → pick
   `.venv/Scripts/python.exe`.
4. Open the terminal (`Ctrl+``) and run:

```bash
pip install -r requirements.txt
```

> **NVIDIA GPU on Windows:** after installing the requirements, run
> `.\install_cuda_torch.bat` to install and verify the CUDA-enabled PyTorch
> build. The script tries supported CUDA wheel channels and restores the
> regular PyTorch build if none work.

### Step 4 — run the app

```bash
streamlit run app.py
```

The browser opens at <http://localhost:8501>.

> **Two commands is the whole story:** `pip install -r requirements.txt` and
> `streamlit run app.py`. (`ollama pull` is a one-time download, and
> `run.bat` / `./run.sh` do all three for you.)

### Run the tests

From the project folder, run:

```bash
python -m unittest discover -v
```

The tests do not need Ollama, a GPU, or Google credentials.

---

## 2. Using the app

1. **Sign in.** Either `🔑 Login with Google` (optional, needs Google setup
   below) or `➡️ Continue in demo mode` (no account, works offline).
2. **Pick a mode** in the sidebar: 💻 Code / 📄 PDF Q&A / 🎨 Image / 📊 PPT.
3. **Ask.** Type in the box at the bottom.

### 💻 Code mode

One model, four tasks (choose in the sidebar):

| Task | You give it | You get back |
|---|---|---|
| ✍️ Generate | a task in words | ready-to-run code |
| 🧩 Complete | half-finished code | the whole function |
| 🐞 Debug | buggy code | fixed code **+** explanation |
| 💡 Explain | any code | a simple, bullet-point explanation |

The sidebar has a **model textbox** - type `qwen2.5-coder:1.5b`, `3b` or `7b`
and the change happens live. Great for showing the judges the speed/size
trade-off.

**The app reads your GPU with `nvidia-smi` and picks the right model for you
at startup** - it shows a line like *"Detected 4.0 GB VRAM - the 3B model fits;
the 7B one would be very slow."* and fills the model box accordingly. You can
still type any model you like.

The chat **remembers the last 3 turns**, so follow-up questions work:
*"now add error handling to that"* / *"make it faster"* / *"explain the second
line"*.

The sidebar also shows a **🟢 / 🔴 Ollama status light** with the list of models
you pulled - handy for the judges to see the app is talking to your own
machine.

### 📄 PDF Q&A mode

Upload a PDF with the button **above the chat**. The app shows the page
count, then every question is answered **only from that document's text**.

### 🎨 Image mode

Describe a picture. The first run downloads the image weights (a few GB, needs
internet once), after that it draws on your GPU in a few seconds. Without an
NVIDIA GPU it still works - just slower, and the caption says so.

### 📊 PPT mode

Type a topic and a number of slides (3-10). The model writes a strict JSON
outline, `python-pptx` turns it into a **16:9 PowerPoint file** you can
download straight from the chat.

If the model ever returns broken JSON, the app does **not** show a red error -
it builds a blank template deck instead, so the demo never dies on screen.

---

## 3. Google sign-in (optional)

The AI features never need an account. Google sign-in only displays the
verified email address of the current user; the app does not access Gmail.
Set it up in four steps:

1. Open the **Google Cloud Console** and create a project:
   <https://console.cloud.google.com/projectcreate>
2. Configure the **OAuth consent screen** for the project. Add the app's
   users as test users if the app is in testing mode.
3. Create an **OAuth client ID** (type = *Desktop app*):
   <https://console.cloud.google.com/apis/credentials>
4. Download the JSON file and **rename it `credentials.json`**, then place it
   next to `app.py` (same folder).

Press `🔑 Login with Google`. A browser tab opens for consent, then the app
shows `✔ your-email@gmail.com`. It requests only the OpenID Connect identity
scopes (`openid`, `email`, and `profile`), not Gmail access. The token is
cached in `token.json` and refreshed when possible. Use **Logout** to remove
the saved token.

> `.gitignore` already protects `credentials.json` and `token.json`.
> **Never** commit or share them.

**Setup check:** if `credentials.json` is missing, Google sign-in shows the
setup instructions and demo mode remains available.

**Kill-switch test (do this before the demo):** rename `credentials.json` to
`credentials_backup.json`, restart the app - Google sign-in now shows the real
error, and **demo mode still works**. Put the file back afterwards.

---

## 4. Folder map

```
programming-slm/
├── app.py                  <- the Streamlit app you run
├── check_gpu.py            <- checks Python, PyTorch, Ollama and GPU readiness
├── requirements.txt        <- pip install -r requirements.txt
├── .gitignore              <- keeps secrets and weights out of Git
├── run.sh / run.bat        <- one-click runners
├── README.md               <- this file
├── src/
│   ├── __init__.py
│   ├── code_model.py       <- ask() -> local Ollama over HTTP + 5 prompt templates
│   ├── image_model.py      <- generate_image() -> local diffusers (GPU aware)
│   ├── pdf_tools.py        <- extract_text() + answer_question()
│   ├── ppt_tools.py        <- make_outline() + build_pptx()
│   └── auth.py             <- login() -> (email, error) + demo mode
├── tests/
│   └── test_auth.py        <- unit tests for authentication helpers
├── models/                 <- local weights are ignored (see models/README.md)
├── outputs/                <- generated PNGs and .pptx files (auto-created)
└── docs/
    ├── MODEL_NOTES.md      <- models, why, licences, VRAM guide
    └── DEMO_SCRIPT.md      <- 2-minute demo script + safety rules
```

---

## 5. "No external AI API" statement

* **Code / PDF / PPT**: every prompt is sent to `http://localhost:11434`
  (your own Ollama server) with a plain `requests.post`. There is no API key
  in this project and no request ever leaves your machine.
* **Images**: `diffusers` loads the weights onto your own GPU/CPU and runs the
  diffusion model in this Python process. No API.
* **PDF**: `pymupdf` reads the file locally. No API.
* **PowerPoint**: `python-pptx` writes the file locally. No API.
* The **only** network use is downloading things once: `pip install`,
  `ollama pull`, the diffusers weights, and (optional) Google OAuth.

### Wi-Fi off test

After setup, turn off Wi-Fi and use the app:

* 💻 Code → works
* 📄 PDF Q&A → works
* 📊 PPT → works
* 🎨 Image → works (the weights are already downloaded)

---

## 6. Licences

| Component | Licence | Link |
|---|---|---|
| Qwen2.5-Coder (7B / 3B / 1.5B) | Apache 2.0 | <https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct> |
| SDXL-Turbo / SD-Turbo (Stability AI) | STABILITY AI NON-COMMERCIAL / research terms | <https://huggingface.co/stabilityai/sdxl-turbo> |
| Ollama | MIT | <https://github.com/ollama/ollama> |
| Streamlit | Apache 2.0 | <https://github.com/streamlit/streamlit> |
| PyMuPDF | AGPL-3.0 (or commercial) | <https://pymupdf.readthedocs.io> |
| python-pptx | MIT | <https://github.com/scanny/python-pptx> |
| PyTorch | BSD-3-Clause | <https://pytorch.org> |
| diffusers / transformers / accelerate | Apache 2.0 | <https://github.com/huggingface/diffusers> |

Qwen2.5-Coder supports **92 programming languages**, and the model accepts
input in many human languages too - the app never restricts your language.

---

## 7. Troubleshooting

| Problem | Fix |
|---|---|
| "Could not reach Ollama" | run `ollama serve` in a terminal, keep it open |
| "model not found" | `ollama pull qwen2.5-coder:7b` (use `3b` on a 4 GB card) |
| The model is very slow | switch to `qwen2.5-coder:1.5b` in the sidebar |
| "Out of GPU memory" in Image mode | lower the steps slider, close other apps, or use `stabilityai/sd-turbo` |
| Images are very slow | no NVIDIA GPU detected - the app is running on CPU |
| Google sign-in fails | Check `credentials.json` and Google OAuth consent-screen settings, or use demo mode |
| "pymupdf is not installed" | `pip install -r requirements.txt` inside the venv |
| Port 8501 is busy | `streamlit run app.py --server.port 8502` |

---

## 8. What is still to do (future work)

* Smarter PDF chunking (embeddings + a real RAG pipeline) instead of keyword
  scoring.
* OCR for scanned PDFs (Tesseract / EasyOCR).
* Streaming the answer token by token from Ollama.
* A "remember my project files" mode that indexes your own `.py` files.
