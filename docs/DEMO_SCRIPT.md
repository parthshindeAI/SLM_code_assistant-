# DEMO_SCRIPT - the 2-minute live demo

## Before you walk in (do this at home, not in the hall)

* [ ] `ollama serve` is running in a terminal (most installs auto-start it).
* [ ] `ollama list` shows `qwen2.5-coder:7b` (or `3b`).
* [ ] Diffusers downloads SD-Turbo on first use. **Generate one throwaway
      image at home** so the model is cached before the demo.
* [ ] `streamlit run app.py` starts with no red error in the terminal.
* [ ] `credentials.json` is in place **or** you have decided to demo in
      demo mode (both are fine - see the kill-switch test in the README).
* [ ] A sample PDF is on the Desktop: `sample.pdf`.
* [ ] Theme is dark/light, projector is connected, browser zoom is 100%.

## The 2 minutes

| Time | What you say | What you do |
|---|---|---|
| 0:00-0:20 | "This is a ChatGPT-style programming assistant that runs 100% offline - no OpenAI key, nothing leaves this laptop." | Open the app, click **Continue in demo mode**, show the ✔ badge |
| 0:20-0:50 | "One local model, four jobs." | Mode 💻 Code → task **Generate** → "write a Python function that merges two sorted lists" → the code appears → switch the task to **Debug** → paste a buggy function → the fix + explanation appears |
| 0:50-1:15 | "It reads my PDFs without the internet." | Mode 📄 PDF Q&A → upload `sample.pdf` → show the page count → "what is this document about?" → answer appears |
| 1:15-1:40 | "It also draws pictures on the GPU." | Mode 🎨 Image → "a blue robot writing code at a laptop, cartoon" → PNG appears → point at the caption "made on your GPU in 3.2 seconds" |
| 1:40-2:00 | "And it builds the PowerPoint for me." | Mode 📊 PPT → "Machine Learning for beginners" → outline appears → click **Download PPTX** → open the file in PowerPoint in 5 seconds |

## Three killer lines to say

1. "**No API key anywhere.** The only network use was downloading the models
   once. Here - I unplugged the Wi-Fi and it still works."
2. "**It fits my laptop's GPU.** 7B model on an 8 GB card, and I can swap to
   1.5B live from this textbox if I want it faster."
3. "**Everything is in five small Python files** that I wrote and can
   explain line by line."

## Safety rules (read before you present)

* **Do not** say "it writes perfect code". Say "it gives me a good starting
  point and explains the fix". Judges trust honest demos.
* **Never** put your `credentials.json` or `token.json` on the projector or
  in the shared drive. If you demo Gmail, sign out afterwards.
* **Never** run code the model wrote on the judge machine. Explain, don't
  execute.
* If the Wi-Fi drops, say it proudly - that is the point of the project.
* If a heavy step is slow (first image, first big answer), say "this is the
  one-time model load" and keep talking.

## The offline proof (do this on purpose)

1. Turn off Wi-Fi (or unplug the network cable).
2. Ask a code question → works.
3. Upload the PDF → works.
4. Make the PPT → works.
5. Turn Wi-Fi back on.

## If something breaks on stage

| Problem | Say this | Do this |
|---|---|---|
| "Could not reach Ollama" | "Ollama stopped - restarting it live." | `ollama serve` in a terminal, click a button again |
| The model is slow | "On a 4 GB card I use the 3B model - let me switch live." | type `qwen2.5-coder:1.5b` in the sidebar model box |
| The image takes long | "The model weights were not cached on this machine." | Generate a throwaway image before the demo; keep size at 512 |
| PDF answer is wrong | "This version uses keyword search, not a RAG pipeline - that is the next step I would do." | show `docs/MODEL_NOTES.md` |
| Everything is on fire | "Let me show the code instead - it is only five files." | open `src/code_model.py` in VS Code |
