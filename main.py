from pathlib import Path
import streamlit as st

ROOT = Path(__file__).parent
APP_PY = ROOT / "app.py"
TEST_PY = ROOT / "test.py"


st.set_page_config(page_title="Notre Territoire", layout="wide", initial_sidebar_state="expanded")
st.set_page_config = lambda *args, **kwargs: None  # no-op pour les sous-scripts

if "vue" not in st.session_state:
    st.session_state.vue = "carte" 

def _basculer():
    st.session_state.vue = "histoire" if st.session_state.vue == "carte" else "carte"


st.markdown(
    """
    <style>
        .st-key-switch_vue_btn {
            position: fixed;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1000000;
        }
        .st-key-switch_vue_btn button {
            background: #474747;
            color: #FFFFFF;
            border: 1px solid rgba(201,162,75,0.6);
            border-radius: 999px;
            padding: 8px 22px;
            font-weight: 600;
            font-size: 13.5px;
            letter-spacing: .02em;
            box-shadow: 0 8px 22px rgba(0,0,0,0.35);
        }
        .st-key-switch_vue_btn button:hover {
            border-color: #F5DF82;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

label = "L'histoire de la vallée" if st.session_state.vue == "carte" else "Carte patrimoniale"
st.button(label, key="switch_vue_btn", on_click=_basculer)

def _run(script_path: Path):
    code = script_path.read_text(encoding="utf-8")
    exec_globals = {
        "__name__": "__main__",
        "__file__": str(script_path),
    }
    exec(compile(code, str(script_path), "exec"), exec_globals)


if st.session_state.vue == "carte":
    _run(APP_PY)
else:
    _run(TEST_PY)
