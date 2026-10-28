"""
ppt_tools.py - turn a topic into a PowerPoint deck.

Step 1: the local model writes a STRICT JSON outline.
Step 2: python-pptx turns that outline into a 16:9 .pptx file.

Both steps run on your computer, so this works offline.
"""

import json
import re
import time
from pathlib import Path

from src import code_model

PROJECT_DIR = Path(__file__).resolve().parent.parent
DECK_DIR = PROJECT_DIR / "outputs" / "decks"

JSON_SHAPE = '{"slides": [{"title": "Short title", "bullets": ["point 1", "point 2"]}]}'


def _clean_json(raw_text):
    """Pull the JSON out of a model reply (models love adding ``` fences)."""
    text = raw_text.strip()

    # remove ```json ... ``` wrappers
    fenced = re.findall(r"```(?:json)?(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    for block in fenced:
        block = block.strip()
        if block.startswith("{") or block.startswith("["):
            text = block
            break

    # keep only the part between the first { and the last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]
    return text.strip()


def _validate(outline, wanted_slides):
    """Make sure the JSON has the shape we expect. Returns (ok, message)."""
    if not isinstance(outline, dict):
        return False, "The model did not return a JSON object."
    slides = outline.get("slides")
    if not isinstance(slides, list) or not slides:
        return False, "The JSON has no 'slides' list."

    for number, slide in enumerate(slides, start=1):
        if not isinstance(slide, dict):
            return False, "Slide " + str(number) + " is not an object."
        if not str(slide.get("title", "")).strip():
            return False, "Slide " + str(number) + " has no title."
        bullets = slide.get("bullets")
        if not isinstance(bullets, list) or not bullets:
            return False, "Slide " + str(number) + " has no bullets."

    if len(slides) < wanted_slides:
        return False, ("The model returned " + str(len(slides)) + " slides but " +
                       str(wanted_slides) + " were asked for.")
    return True, "ok"


def _blank_outline(topic, slides):
    """A simple outline built here in Python - our safety net for the demo."""
    return {
        "slides": [
            {
                "title": topic if number == 0 else "Point " + str(number + 1),
                "bullets": [
                    "Write here what this slide is about (" + topic + ")",
                    "Add one example or number",
                    "Made offline on your own computer",
                ],
            }
            for number in range(slides)
        ]
    }


def make_outline(topic, slides=5, model=code_model.DEFAULT_MODEL):
    """Ask the model for a JSON outline. Returns (outline, warning_message).

    If the model does not manage valid JSON we still return a usable blank
    outline, so the demo never ends with an empty screen.
    """
    instructions = (
        "You are a presentation designer. Write a slide outline as STRICT JSON.\n"
        "Use EXACTLY this shape and no other keys:\n" + JSON_SHAPE + "\n"
        "Rules:\n"
        "- exactly " + str(slides) + " slides\n"
        "- 3 or 4 short bullets per slide (max 12 words each)\n"
        "- plain text only, no markdown, no code fences, no extra keys\n\n"
        "Topic: " + topic
    )

    raw = code_model.ask(instructions, "qa", model)
    cleaned = _clean_json(raw)

    try:
        outline = json.loads(cleaned)
    except ValueError as error:
        # one retry: tell the model exactly what went wrong
        retry = (
            instructions + "\n\nIMPORTANT: your previous answer was not valid JSON "
            "(error: " + str(error) + "). Reply with the JSON object ONLY, "
            "starting with { and ending with }."
        )
        raw = code_model.ask(retry, "qa", model)
        cleaned = _clean_json(raw)
        try:
            outline = json.loads(cleaned)
        except ValueError:
            return _blank_outline(topic, slides), (
                "The model did not return valid JSON, so here is a blank template "
                "instead - type your own bullets in PowerPoint.")

    ok, message = _validate(outline, slides)
    if not ok:
        return _blank_outline(topic, slides), (
            "The model returned an outline we could not use (" + message +
            "), so here is a blank template instead.")

    # keep exactly the number of slides the user asked for
    outline["slides"] = outline["slides"][:slides]
    return outline, None


def build_pptx(outline, topic, model=code_model.DEFAULT_MODEL, file_name=None):
    """Build the .pptx file. Returns the path of the saved file."""
    try:
        from pptx import Presentation
        from pptx.util import Inches
    except ImportError:
        raise RuntimeError("python-pptx is not installed. Run:  pip install python-pptx")

    DECK_DIR.mkdir(parents=True, exist_ok=True)
    if not file_name:
        stamp = time.strftime("%Y%m%d-%H%M%S")
        file_name = "deck-" + stamp + ".pptx"
    file_path = DECK_DIR / file_name

    presentation = Presentation()
    # 16:9 widescreen (default python-pptx is 4:3)
    presentation.slide_width = Inches(13.333)
    presentation.slide_height = Inches(7.5)

    title_layout = presentation.slide_layouts[0]
    bullet_layout = presentation.slide_layouts[1]

    # --- slide 1: the title slide -------------------------------------------
    title_slide = presentation.slides.add_slide(title_layout)
    title_slide.shapes.title.text = topic
    title_slide.placeholders[1].text = ("Generated offline with " + model +
                                        " on the Programming SLM app")

    # --- one slide per outline entry ----------------------------------------
    for entry in outline.get("slides", []):
        slide = presentation.slides.add_slide(bullet_layout)
        slide.shapes.title.text = str(entry.get("title", "")).strip()
        body = slide.placeholders[1].text_frame
        body.word_wrap = True

        bullets = [str(b).strip() for b in entry.get("bullets", []) if str(b).strip()]
        for number, bullet in enumerate(bullets):
            paragraph = body.paragraphs[0] if number == 0 else body.add_paragraph()
            paragraph.text = bullet
            paragraph.level = 0

    presentation.save(str(file_path))
    return file_path
