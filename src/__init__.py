"""
Programming SLM - helper modules.

Nothing in here talks to a cloud AI API:
  code_model.py  -> your local Ollama server (http://localhost:11434)
  image_model.py -> local diffusers models (weights downloaded once)
  pdf_tools.py   -> local pymupdf
  ppt_tools.py   -> local python-pptx
  auth.py        -> optional Google sign-in (+ offline demo mode)
"""

__all__ = ["auth", "code_model", "image_model", "pdf_tools", "ppt_tools"]
