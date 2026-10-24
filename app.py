"""
LLM-powered Data Analysis Assistant
Run with:
    streamlit run app.py
"""

import os
import io
import contextlib
import traceback

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import streamlit as st

from llm_backend import get_llm_response

st.set_page_config(page_title="LLM Data Analysis Assistant", layout="wide")
st.title("📊 LLM-powered Data Analysis Assistant")
st.caption("Upload a CSV, ask questions in plain English, and get pandas answers + charts.")

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("Settings")
    provider = st.selectbox("LLM Provider", ["OpenAI", "Anthropic", "Groq"])

    env_key = {
        "OpenAI": "OPENAI_API_KEY",
        "Anthropic": "ANTHROPIC_API_KEY",
        "Groq": "GROQ_API_KEY",
    }[provider]

    api_key = st.text_input(
        f"{provider} API Key",
        value=os.environ.get(env_key, ""),
        type="password",
        help=f"Or set {env_key} as an environment variable before starting Streamlit.",
    )

    default_model = {
        "OpenAI": "gpt-4o-mini",
        "Anthropic": "claude-sonnet-4-5",
        "Groq": "openai/gpt-oss-20b",
    }[provider]

    model_name = st.text_input("Model", value=default_model)
    st.caption("Keys are used only for the current Streamlit session.")

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if "df" not in st.session_state:
    st.session_state.df = None
if "history" not in st.session_state:
    st.session_state.history = []

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        # Make a copy and normalize only obvious date columns for easier analysis.
        for col in df.columns:
            if "date" in str(col).lower():
                converted = pd.to_datetime(df[col], errors="coerce")
                if converted.notna().mean() >= 0.8:
                    df[col] = converted
        st.session_state.df = df
    except Exception as e:
        st.error(f"Could not read CSV: {e}")

df = st.session_state.df

if df is None:
    st.info("Upload a CSV to get started.")
    st.stop()

st.subheader("Preview")
st.dataframe(df.head(20), use_container_width=True)
st.caption(f"{df.shape[0]} rows × {df.shape[1]} columns")

question = st.text_input(
    "Ask a question about this data",
    placeholder="e.g. What are the top 5 categories by total sales?",
)
ask_btn = st.button("Ask", type="primary")

if ask_btn and question.strip():
    if not api_key.strip():
        st.error(f"Enter a {provider} API key in the sidebar.")
        st.stop()

    code = None
    output_text = ""
    error_text = None
    fig = None

    for attempt in range(2):
        with st.spinner("Generating analysis..." if attempt == 0 else "Fixing generated code..."):
            try:
                code = get_llm_response(
                    question=question,
                    df_columns=list(df.columns),
                    df_dtypes=df.dtypes.astype(str).to_dict(),
                    df_head=df.head(5).to_dict(orient="records"),
                    provider=provider,
                    api_key=api_key.strip(),
                    model_name=model_name.strip(),
                    previous_code=code,
                    previous_error=error_text,
                )
            except Exception as e:
                st.error(f"{provider} API call failed: {e}")
                code = None
                break

        if not code:
            break

        local_ns = {"df": df.copy(), "pd": pd, "plt": plt}
        stdout_buf = io.StringIO()
        error_text = None
        fig = None

        try:
            plt.close("all")
            with contextlib.redirect_stdout(stdout_buf):
                exec(compile(code, "<generated_analysis>", "exec"), {"__builtins__": __builtins__}, local_ns)

            output_text = stdout_buf.getvalue()
            if plt.get_fignums():
                fig = plt.gcf()
            break
        except Exception:
            error_text = traceback.format_exc()
            output_text = stdout_buf.getvalue()
            plt.close("all")

    st.session_state.history.insert(
        0, (question, code or "# No code generated", output_text, error_text, fig)
    )

for i, (q, code, output_text, error_text, fig) in enumerate(st.session_state.history):
    with st.expander(f"Q: {q}", expanded=(i == 0)):
        st.markdown("**Generated code**")
        st.code(code, language="python")

        if error_text:
            st.error("Execution error after retry:")
            st.code(error_text)

        if output_text.strip():
            st.markdown("**Output**")
            st.text(output_text)

        if fig is not None:
            st.pyplot(fig)

        if not output_text.strip() and fig is None and not error_text:
            st.info("The code ran but produced no printed result or chart.")
