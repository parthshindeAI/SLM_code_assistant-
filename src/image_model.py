"""
image_model.py - draw pictures on YOUR computer with diffusers.

The heavy libraries (torch, diffusers) are imported only when a picture is
requested, so the app starts instantly. The pipeline is kept in a global so
the weights are loaded from disk just ONCE per session.

First run downloads the weights (~2 GB for sd-turbo, ~7 GB for sdxl-turbo).
After that everything works with the Wi-Fi unplugged.
"""

import time
from pathlib import Path

from src import code_model

PROJECT_DIR = Path(__file__).resolve().parent.parent
IMAGE_DIR = PROJECT_DIR / "outputs" / "images"

# heavy stuff -> keep it in a global so we load it only once
_PIPELINE = None
_PIPELINE_NAME = None


def device_info():
    """Return (description, model_id) for the machine we are running on."""
    # We ask nvidia-smi (not torch) about the VRAM, because torch may not be
    # installed yet - and the answer decides which image model we use.
    vram_mb = code_model.detect_vram_mb()
    vram_gb = vram_mb / 1024

    if vram_mb == 0:
        model_id = "stabilityai/sd-turbo"       # no GPU -> the small model
    elif vram_gb >= 7:
        model_id = "stabilityai/sdxl-turbo"     # 8 GB card -> better quality
    else:
        model_id = "stabilityai/sd-turbo"       # 4 GB card -> smaller model

    try:
        import torch
    except ImportError:
        return ("torch is not installed - run:  pip install -r requirements.txt",
                model_id)

    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0)
        if vram_mb:
            return ("GPU: " + name + "  (%.1f GB VRAM)" % vram_gb, model_id)
        return ("GPU: " + name, model_id)

    # no CUDA inside torch, but the machine may still have an NVIDIA GPU
    if vram_mb:
        return ("PyTorch is the CPU-only build, so your " + ("%.0f" % vram_gb) +
                " GB NVIDIA GPU is NOT being used. Fix it with:  pip install torch "
                "--index-url https://download.pytorch.org/whl/cu124", model_id)

    return ("CPU only - no NVIDIA GPU found, expect 1-3 minutes per picture",
            model_id)


def _load_pipeline(model_id, device, dtype):
    """Load the diffusion pipeline, trying a few options so it works everywhere."""
    from diffusers import AutoPipelineForText2Image

    attempts = [
        {"torch_dtype": dtype, "safety_checker": None, "requires_safety_checker": False},
        {"torch_dtype": dtype, "variant": "fp16"},
        {"torch_dtype": dtype},
    ]
    last_error = None
    for options in attempts:
        try:
            pipeline = AutoPipelineForText2Image.from_pretrained(model_id, **options)
            return pipeline.to(device)
        except Exception as error:          # try the next option
            last_error = error

    raise RuntimeError(
        "Could not load the image model '" + model_id + "': " + str(last_error) +
        ". The weights are downloaded on first use - check your internet connection."
    )


def generate_image(prompt, steps=2, model_id=None, size=512):
    """Draw one picture and save it as PNG.

    Returns (file_path, caption). Raises RuntimeError with a friendly message.
    """
    global _PIPELINE, _PIPELINE_NAME

    if not prompt.strip():
        raise RuntimeError("Please type a picture description first.")

    try:
        import torch
    except ImportError:
        raise RuntimeError("Image mode needs torch and diffusers. Run:  pip install -r requirements.txt")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32
    if device == "cuda":
        # small free speed-up on RTX cards (Ampere and newer)
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

    if model_id is None:
        model_id = device_info()[1]

    load_start = time.time()
    if _PIPELINE is None or _PIPELINE_NAME != model_id:
        _PIPELINE = _load_pipeline(model_id, device, dtype)
        _PIPELINE_NAME = model_id
    load_seconds = time.time() - load_start

    draw_start = time.time()
    try:
        result = _PIPELINE(
            prompt=prompt,
            num_inference_steps=int(steps),
            guidance_scale=0.0,       # turbo models are trained for 0 guidance
            height=int(size),
            width=int(size),
        )
        image = result.images[0]
    except torch.cuda.OutOfMemoryError:
        raise RuntimeError(
            "Out of GPU memory. Close other apps, lower the steps, or use the "
            "smaller model (stabilityai/sd-turbo) instead of sdxl-turbo."
        )
    except Exception as error:
        raise RuntimeError("Image generation failed: " + str(error))

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    file_path = IMAGE_DIR / ("image-" + stamp + ".png")
    image.save(str(file_path))

    draw_seconds = time.time() - draw_start
    if device == "cuda":
        caption = ("Made on your GPU with " + model_id + " in %.1f seconds "
                   "(model loaded in %.1f s)." % (draw_seconds, load_seconds))
    else:
        caption = ("Made on CPU with " + model_id + " in %.1f seconds. "
                   "This is slow because there is no NVIDIA GPU - on a real "
                   "RTX 3050 this takes a few seconds." % draw_seconds)
    return file_path, caption
