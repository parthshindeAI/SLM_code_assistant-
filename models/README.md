# models/ - folder for local model files

This folder is **empty on purpose**. It is the place where you can put model
weights you download yourself, so the project keeps everything in one place.

The two models this app uses are NOT stored here - Ollama and diffusers keep
them in their own cache folders:

| Purpose | Model | Where it lives |
|---|---|---|
| Code / PDF / PPT answers | `qwen2.5-coder:7b` | Ollama cache (`%USERPROFILE%\.ollama\models` on Windows) |
| Text to image | `stabilityai/sdxl-turbo` | HuggingFace cache (`%USERPROFILE%\.cache\huggingface`) |

If you ever want to try a **local GGUF** model instead of Ollama, drop the
file in this folder, for example `models/qwen2.5-coder-7b-instruct.gguf`, and
`.gitignore` will make sure it is never committed to Git.

Model choices, VRAM maths and licences are written down in
[`docs/MODEL_NOTES.md`](../docs/MODEL_NOTES.md).
