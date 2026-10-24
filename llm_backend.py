"""
LLM backend for the Data Analysis Assistant.

Supported providers:
- OpenAI
- Anthropic
- Groq

The model is asked to return executable pandas/matplotlib code only.
"""

import re


SYSTEM_PROMPT = """You are a senior Python data analyst.

The DataFrame is already loaded as `df`.
You must answer the user's question using pandas and matplotlib.

Rules:
1. Return ONLY executable Python code. Never return markdown fences or explanations.
2. Use the existing DataFrame `df`; never load a file and never create fake data.
3. Print the final textual answer with print(...).
4. If a chart is useful, use the existing matplotlib object `plt`; do not call plt.show().
5. Prefer simple pandas code. Do not use seaborn or install packages.
6. Column names may contain spaces or special characters, so use df["exact column name"].
7. Handle missing values sensibly.
8. If a date column is needed, convert it with pd.to_datetime(..., errors="coerce") when necessary.
9. For calculations such as sales/revenue, infer the formula from available columns and state the result in print().
"""


def _build_user_prompt(question, df_columns, df_dtypes, df_head, previous_code=None, previous_error=None):
    repair = ""
    if previous_code and previous_error:
        repair = f"""
A previous generated program failed.

Previous code:
{previous_code}

Execution error:
{previous_error}

Generate corrected code now. Do not repeat the same error.
"""

    return f"""DataFrame columns: {df_columns}
DataFrame dtypes: {df_dtypes}
Sample rows:
{df_head}

User question:
{question}
{repair}

Return only executable Python code."""


def _strip_code_fences(text):
    if not text:
        raise ValueError("The model returned an empty response.")

    text = text.strip()
    match = re.match(r"^```(?:python|py)?\s*(.*?)\s*```$", text, re.DOTALL | re.IGNORECASE)
    if match:
        text = match.group(1).strip()

    # Some models occasionally add a short prefix before the code.
    if text.lower().startswith("python\n"):
        text = text[7:].lstrip()

    return text


def get_llm_response(
    question,
    df_columns,
    df_dtypes,
    df_head,
    provider,
    api_key,
    model_name,
    previous_code=None,
    previous_error=None,
):
    prompt = _build_user_prompt(
        question, df_columns, df_dtypes, df_head, previous_code, previous_error
    )

    provider = provider.strip().lower()

    if provider == "openai":
        raw = _call_openai(prompt, api_key, model_name)
    elif provider == "anthropic":
        raw = _call_anthropic(prompt, api_key, model_name)
    elif provider == "groq":
        raw = _call_groq(prompt, api_key, model_name)
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    return _strip_code_fences(raw)


def _call_openai(prompt, api_key, model_name):
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=1500,
    )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("OpenAI returned no text.")
    return content


def _call_anthropic(prompt, api_key, model_name):
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model_name,
        max_tokens=1500,
        temperature=0,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    parts = [
        block.text
        for block in response.content
        if getattr(block, "type", None) == "text"
    ]
    if not parts:
        raise RuntimeError("Anthropic returned no text.")
    return "\n".join(parts)


def _call_groq(prompt, api_key, model_name):
    from groq import Groq

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=1500,
    )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Groq returned no text.")
    return content
