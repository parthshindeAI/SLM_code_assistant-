"""
Programming SLM - a ChatGPT-style assistant that runs 100% offline.

HOW TO RUN (VS Code terminal):
    pip install -r requirements.txt
    ollama pull qwen2.5-coder:7b        (one time only)
    streamlit run app.py

Everything the AI does happens on YOUR computer:
  * code / PDF / PPT answers -> your local Ollama server (http://localhost:11434)
  * pictures                 -> local diffusers models
  * PDF reading              -> local pymupdf
There is no OpenAI / Gemini / HuggingFace inference API anywhere in this app.
"""

import json
import os
from pathlib import Path

import streamlit as st

from src import auth, code_model, image_model, pdf_tools, ppt_tools

st.set_page_config(page_title="Programming SLM", page_icon="🤖", layout="wide")

PROJECT_DIR = Path(__file__).resolve().parent

# The version of the code you are running. It is printed in the terminal and
# shown in the sidebar, so you always know whether you have the new build.
APP_VERSION = "v5 - 2026-10-21 (Google sign-in)"

print("=" * 62, flush=True)
print("  Programming SLM  " + APP_VERSION, flush=True)
print("  Running from: " + str(PROJECT_DIR), flush=True)
print("=" * 62, flush=True)

# --------------------------------------------------------------------- config
MODES = {
    "code": {"label": "💻 Code", "greeting": "Ask me to write, finish, debug or explain code."},
    "pdf": {"label": "📄 PDF Q&A", "greeting": "Upload a PDF above, then ask me anything about it."},
    "image": {"label": "🎨 Image", "greeting": "Describe a picture and I will draw it locally."},
    "ppt": {"label": "📊 PPT", "greeting": "Give me a topic and I will build a PowerPoint deck."},
}
MODE_KEYS = list(MODES.keys())

CODE_TASKS = {
    "generate": "✍️ Generate (task ➜ code)",
    "complete": "🧩 Complete (partial ➜ full code)",
    "debug": "🐞 Debug (buggy ➜ fixed code)",
    "explain": "💡 Explain (code ➜ simple words)",
}

# Small CSS so it looks a bit like ChatGPT.
# IMPORTANT: never hardcode background or text colours here - Streamlit's
# light/dark theme must stay in charge, otherwise text becomes invisible.
st.markdown(
    """
    <style>
      .block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 980px; }
      .stChatMessage { border-radius: 14px; }
      .slm-title { font-weight: 700; font-size: 1.4rem; color: inherit; }
      /* Safety net: the sidebar always uses the theme's own colour.
         Without this, a hardcoded light background can make the sidebar
         text invisible in dark mode. */
      [data-testid="stSidebar"], section[data-testid="stSidebar"] {
        background-color: var(--secondary-background-color, transparent) !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# -------------------------------------------------------------- session state
def init_state():
    """Create the session variables we need (only once per browser session)."""
    st.session_state.setdefault("signed_in_as", None)
    st.session_state.setdefault("mode", "code")
    # Ask the GPU how much memory we have and pick a model that fits it.
    suggested_model, gpu_note = code_model.suggest_model()
    st.session_state.setdefault("gpu_note", gpu_note)
    st.session_state.setdefault(
        "ollama_model",
        os.environ.get("OLLAMA_MODEL", suggested_model),
    )
    st.session_state.setdefault("pdf_text", "")
    st.session_state.setdefault("pdf_pages", 0)
    st.session_state.setdefault("pdf_name", "")
    st.session_state.setdefault("pdf_file_id", None)
    for key in MODE_KEYS:
        st.session_state.setdefault("chat_" + key, [])


init_state()


# ------------------------------------------------------------------- helpers
@st.cache_data(ttl=30, show_spinner=False)
def installed_models():
    """Ask Ollama which models are pulled. Cached for 30 seconds."""
    return code_model.list_models()


def push_message(mode, role, text=None, kind="text", path=None, caption=None, data=None):
    """Save one chat message in the history of this mode."""
    st.session_state["chat_" + mode].append(
        {
            "role": role,
            "text": text or "",
            "kind": kind,
            "path": path,
            "caption": caption,
            "data": data,
        }
    )


def chat_memory(mode, turns=3):
    """The last few turns of this chat, so follow-up questions make sense.

    The newest message is skipped - that is the question we are answering now.
    """
    history = st.session_state["chat_" + mode][:-1]
    parts = []
    for message in history[-turns:]:
        if message.get("kind") not in ("text", "code"):
            continue
        text = message.get("text", "")
        if message.get("kind") == "code":
            text = "```\n" + text + "\n```"
        who = "User" if message["role"] == "user" else "Assistant"
        parts.append(who + ": " + text)
    return "\n\n".join(parts)


def render_reply(text):
    """Show a reply: normal text as markdown, code blocks in a code box."""
    for kind, content in code_model.split_code_blocks(text):
        if kind == "code":
            st.code(content, language="python")
        elif content.strip():
            st.markdown(content)


def show_history(mode):
    """Draw every saved message of one mode."""
    for number, message in enumerate(st.session_state["chat_" + mode]):
        with st.chat_message(message["role"]):
            kind = message.get("kind", "text")
            if kind == "image":
                path = message.get("path")
                if path and Path(path).exists():
                    st.image(path, caption=message.get("caption", ""))
                    st.download_button(
                        "⬇️ Download PNG",
                        data=Path(path).read_bytes(),
                        file_name=Path(path).name,
                        key="dl_img_" + mode + "_" + str(number),
                    )
            elif kind == "pptx":
                path = message.get("path")
                st.success(message.get("caption", "Deck ready."))
                if message.get("text"):
                    with st.expander("Outline used for the deck", expanded=False):
                        st.json(json.loads(message["text"]))
                if path and Path(path).exists():
                    st.download_button(
                        "⬇️ Download PPTX",
                        data=Path(path).read_bytes(),
                        file_name=Path(path).name,
                        key="dl_ppt_" + mode + "_" + str(number),
                    )
            else:
                render_reply(message.get("text", ""))


def render_login(where="main"):
    """The login card (used in the sidebar and on the locked screen).

    `where` makes the widget keys unique - Streamlit needs different keys
    for two widgets that live on the same page.
    """
    google_ready = auth.credentials_ready()

    # --- Google (only shown as the main option when it is set up) --------
    if google_ready:
        if st.button("🔑 Login with Google", key="google_login_" + where,
                     use_container_width=True):
            with st.spinner("Opening Google sign-in in your browser..."):
                email, error = auth.login()
            if email:
                st.session_state["signed_in_as"] = email
                st.rerun()
            else:
                st.error(error)
    else:
        st.info(
            "**Google sign-in is not set up on this computer** - it needs a Google OAuth "
            "file (`credentials.json`) in the project folder. See the Google sign-in "
            "instructions in README.\n\n"
            "👇 **Demo mode needs no setup at all** and works completely offline."
        )

    # --- demo mode: always available, always the quickest way in --------
    st.caption("No Google account? Use demo mode - it needs no internet:")
    demo_name = st.text_input("Your name or email", value="student@example.com",
                               key="demo_name_" + where, label_visibility="collapsed")
    if st.button("➡️ Continue in demo mode", key="demo_login_" + where,
                 type="primary", use_container_width=True):
        email, error = auth.demo_login(demo_name)
        if email:
            st.session_state["signed_in_as"] = email
            st.rerun()
        else:
            st.error(error)

    # --- the Google button is still reachable, just tucked away ----------
    if not google_ready:
        with st.expander("Set up Google sign-in instead (needs credentials.json)"):
            if st.button("🔑 Try Google sign-in", key="google_login2_" + where,
                         use_container_width=True):
                with st.spinner("Opening Google sign-in in your browser..."):
                    email, error = auth.login()
                if email:
                    st.session_state["signed_in_as"] = email
                    st.rerun()
                else:
                    st.error(error)


# ------------------------------------------------------------------- sidebar
def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="slm-title">🤖 Programming SLM</div>', unsafe_allow_html=True)
        st.caption("Offline coding assistant · Ollama + local models")
        st.caption("Build: " + APP_VERSION)

        st.divider()

        # --- 1. sign in -----------------------------------------------------
        if st.session_state["signed_in_as"]:
            st.success("✔ " + st.session_state["signed_in_as"])
            if st.button("Logout"):
                error = auth.logout()
                if error:
                    st.error(error)
                else:
                    st.session_state["signed_in_as"] = None
                    st.rerun()
        else:
            st.subheader("1️⃣ Sign in")
            render_login("sidebar")
            st.divider()

        # --- 2. mode --------------------------------------------------------
        st.subheader("2️⃣ Mode")
        chosen = st.radio(
            "Mode",
            MODE_KEYS,
            format_func=lambda key: MODES[key]["label"],
            key="mode",
        )

        # --- 3. settings for the chosen mode --------------------------------
        st.subheader("3️⃣ Settings")
        if chosen == "code":
            st.selectbox("Task", list(CODE_TASKS.keys()),
                         format_func=lambda key: CODE_TASKS[key], key="code_task")
        elif chosen == "image":
            st.slider("Steps", min_value=1, max_value=4, value=2, key="img_steps")
            st.selectbox("Size", [512, 640, 768], index=0, key="img_size")
            info, model_id = image_model.device_info()
            st.caption("Model: " + model_id)
            st.info(info)
        elif chosen == "ppt":
            st.slider("Number of slides", min_value=3, max_value=10, value=5, key="ppt_slides")
        else:  # pdf
            if st.session_state["pdf_pages"]:
                st.caption("Loaded: " + st.session_state["pdf_name"] +
                           " (" + str(st.session_state["pdf_pages"]) + " pages)")
            else:
                st.caption("No PDF loaded yet.")

        # Ollama model (used by code / pdf / ppt)
        st.markdown("**Ollama model**")
        st.caption(st.session_state["gpu_note"])
        st.text_input("Model name", key="ollama_model",
                      help="Type any model you pulled, e.g. qwen2.5-coder:1.5b")
        installed = installed_models()
        if installed:
            st.success("🟢 Ollama is running")
            st.caption("Pulled models: " + ", ".join(installed))
        else:
            st.error("🔴 Ollama is not running")
            st.caption("Fix it: open a terminal, run  ollama serve  and  ollama pull " +
                       st.session_state["ollama_model"])
        if st.button("🔄 Check Ollama again"):
            installed_models.clear()      # forget the cached answer
            st.rerun()

        st.divider()

        # --- 4. clear chat ---------------------------------------------------
        if st.button("🗑️ Clear this chat", use_container_width=True):
            st.session_state["chat_" + chosen] = []
            st.rerun()


render_sidebar()

# ------------------------------------------------------------------ the gate
if not st.session_state["signed_in_as"]:
    st.title("🤖 Programming SLM")
    st.markdown(
        "A ChatGPT-style **programming assistant that runs entirely on your own "
        "computer** - no cloud AI API, no internet needed after setup."
    )
    st.info("Sign in with Google, or use **demo mode** (works with no account and no internet).")
    render_login("main")
    st.stop()

# ----------------------------------------------------------------- main area
mode = st.session_state["mode"]
st.title(MODES[mode]["label"])

if mode == "pdf":
    # the uploader sits above the chat
    uploaded = st.file_uploader("📎 Upload a PDF to ask questions about it",
                                type=["pdf"], key="pdf_upload")
    if uploaded is not None:
        fingerprint = uploaded.name + str(len(uploaded.getvalue()))
        if st.session_state["pdf_file_id"] != fingerprint:
            try:
                with st.spinner("Reading the PDF..."):
                    text, pages = pdf_tools.extract_text(uploaded.getvalue())
                st.session_state["pdf_text"] = text
                st.session_state["pdf_pages"] = pages
                st.session_state["pdf_name"] = uploaded.name
                st.session_state["pdf_file_id"] = fingerprint
                push_message("pdf", "assistant",
                             "📄 Loaded **" + uploaded.name + "** - " + str(pages) +
                             " pages, " + str(len(text)) + " characters of text. "
                             "Ask me anything about it!")
            except Exception as error:
                st.session_state["pdf_text"] = ""
                st.session_state["pdf_pages"] = 0
                st.error(str(error))
    if st.session_state["pdf_pages"]:
        st.success("✔ " + st.session_state["pdf_name"] + " - " +
                   str(st.session_state["pdf_pages"]) + " pages loaded")

# seed a friendly greeting the first time a mode is opened
if not st.session_state["chat_" + mode]:
    push_message(mode, "assistant", MODES[mode]["greeting"])

show_history(mode)

# --------------------------------------------------------------- chat input
placeholders = {
    "code": "Ask for code, paste code to fix, or paste code to explain...",
    "pdf": "Ask a question about the uploaded PDF...",
    "image": "Describe the picture you want, e.g. 'a blue robot coding at a laptop'...",
    "ppt": "Give a topic, e.g. 'Machine Learning for beginners'...",
}
prompt = st.chat_input(placeholders[mode], key="chat_input_" + mode)

if prompt:
    push_message(mode, "user", prompt)
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # ---------------------------------------------------------- CODE MODE
        if mode == "code":
            task = st.session_state["code_task"]
            model = st.session_state["ollama_model"]
            memory = chat_memory("code", 3)
            with st.spinner("Thinking (" + model + ")..."):
                try:
                    reply = code_model.ask(prompt, task, model, context=memory)
                except Exception as error:
                    reply = None
                    message = str(error)
            if reply:
                render_reply(reply)
                push_message(mode, "assistant", reply)
            else:
                st.error(message)
                push_message(mode, "assistant", "⚠️ " + message)

        # ----------------------------------------------------------- PDF MODE
        elif mode == "pdf":
            model = st.session_state["ollama_model"]
            if not st.session_state["pdf_text"]:
                st.warning("Upload a PDF above first.")
                push_message(mode, "assistant", "⚠️ Please upload a PDF above first.")
            else:
                memory = chat_memory("pdf", 3)
                with st.spinner("Reading the document (" + model + ")..."):
                    try:
                        reply = pdf_tools.answer_question(
                            st.session_state["pdf_text"], prompt, model, memory=memory)
                    except Exception as error:
                        reply = None
                        message = str(error)
                if reply:
                    render_reply(reply)
                    push_message(mode, "assistant", reply)
                else:
                    st.error(message)
                    push_message(mode, "assistant", "⚠️ " + message)

        # --------------------------------------------------------- IMAGE MODE
        elif mode == "image":
            steps = st.session_state["img_steps"]
            size = st.session_state["img_size"]
            with st.spinner("Drawing (first run downloads the model, be patient)..."):
                try:
                    path, caption = image_model.generate_image(prompt, steps=steps, size=size)
                except Exception as error:
                    path = None
                    message = str(error)
            if path:
                st.image(str(path), caption=caption)
                st.download_button("⬇️ Download PNG", data=Path(path).read_bytes(),
                                   file_name=Path(path).name, key="dl_img_new")
                push_message(mode, "assistant", "", kind="image", path=str(path),
                             caption=caption)
            else:
                st.error(message)
                push_message(mode, "assistant", "⚠️ " + message)

        # ----------------------------------------------------------- PPT MODE
        elif mode == "ppt":
            slides = st.session_state["ppt_slides"]
            model = st.session_state["ollama_model"]
            with st.spinner("Writing the outline (" + model + ")..."):
                try:
                    outline, error = ppt_tools.make_outline(prompt, slides, model)
                except Exception as error:
                    outline, error = None, str(error)
            if not outline:
                st.error(error)
                push_message(mode, "assistant", "⚠️ " + str(error))
            else:
                if error:
                    st.warning("⚠️ " + str(error))
                try:
                    with st.spinner("Building the PowerPoint file..."):
                        path = ppt_tools.build_pptx(outline, prompt, model)
                except Exception as error:
                    path = None
                    message = str(error)
                if path:
                    st.success("✅ Deck ready - " + str(len(outline["slides"])) + " slides.")
                    with st.expander("Outline used for the deck", expanded=True):
                        st.json(outline)
                    st.download_button("⬇️ Download PPTX", data=Path(path).read_bytes(),
                                       file_name=Path(path).name, key="dl_ppt_new")
                    push_message(mode, "assistant", json.dumps(outline), kind="pptx",
                                 path=str(path),
                                 caption="✅ Deck ready - " + str(len(outline["slides"])) +
                                         " slides about " + prompt)
                else:
                    st.error(message)
                    push_message(mode, "assistant", "⚠️ " + message)
