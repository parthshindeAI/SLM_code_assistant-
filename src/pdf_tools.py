"""
pdf_tools.py - read a PDF that the user uploads and answer questions about it.

pymupdf (import name: fitz) is a normal Python library, so this works
with the Wi-Fi unplugged. No AI service is involved in reading the file.
"""

try:
    import pymupdf as fitz        # pymupdf >= 1.24
except ImportError:
    try:
        import fitz                # older pymupdf
    except ImportError:
        fitz = None

from src import code_model

# We do not send the whole PDF to the model - we send a slice of it.
MAX_CONTEXT_CHARS = 6000


def extract_text(pdf_bytes):
    """Return (text, page_count) for an uploaded PDF.

    Raises RuntimeError with a friendly message if the file cannot be read.
    """
    if fitz is None:
        raise RuntimeError("pymupdf is not installed. Run:  pip install pymupdf")

    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception:
        raise RuntimeError("That file could not be opened as a PDF.")

    try:
        pages = document.page_count
        chunks = [page.get_text() for page in document]
    finally:
        document.close()

    text = "\n".join(chunks).strip()
    if not text:
        raise RuntimeError(
            "No text found in this PDF. It is probably a scanned image - "
            "OCR is not part of this project (see docs/MODEL_NOTES.md)."
        )
    return text, pages


def pick_relevant_part(text, question):
    """Choose the most useful slice of the document for this question.

    Simple keyword scoring - good enough for a student project.
    A real RAG pipeline with embeddings is listed as future work.
    """
    if len(text) <= MAX_CONTEXT_CHARS:
        return text

    words = [w.lower().strip(".,?!:;\"'()") for w in question.split()]
    words = [w for w in words if len(w) > 3]

    best_chunk = text[:MAX_CONTEXT_CHARS]
    best_score = -1
    for start in range(0, len(text), MAX_CONTEXT_CHARS):
        chunk = text[start:start + MAX_CONTEXT_CHARS]
        score = sum(chunk.lower().count(word) for word in words)
        if score > best_score:
            best_score = score
            best_chunk = chunk
    return best_chunk


def answer_question(text, question, model=code_model.DEFAULT_MODEL, memory=""):
    """Answer a question using only the text of the uploaded PDF."""
    context = pick_relevant_part(text, question)

    prompt = (
        "Answer the question using ONLY the CONTEXT below.\n"
        "Quote short key phrases from the context when you answer.\n"
        "If the answer is not in the context, reply exactly: "
        "I could not find that in the document.\n\n"
        "CONTEXT:\n" + context + "\n\n"
        "QUESTION:\n" + question
    )
    if memory:
        prompt += "\n\nEARLIER CONVERSATION (use it only as context):\n" + memory
    return code_model.ask(prompt, "qa", model)
