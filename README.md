# LLM Data Analysis Assistant — Fixed Version

A Streamlit app that lets you upload a CSV and ask questions in plain English.
The LLM generates pandas/matplotlib code, the app executes it locally, and
shows the result/chart.

## Providers

- OpenAI — default model: `gpt-4o-mini`
- Anthropic — default model: `claude-sonnet-4-5`
- Groq — default model: `openai/gpt-oss-20b`

## Windows setup

Open PowerShell in this folder:

```powershell
py -3.10 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

## API key

You can paste the key into the sidebar.

Or set it before starting Streamlit:

```powershell
$env:OPENAI_API_KEY="your_key_here"
```

For Anthropic:

```powershell
$env:ANTHROPIC_API_KEY="your_key_here"
```

For Groq:

```powershell
$env:GROQ_API_KEY="your_key_here"
```

### Important

Do not put a Groq key into the OpenAI provider box.
Choose **Groq** when using a `gsk_...` key.

Do not put an OpenAI key into the Groq provider box.
Choose **OpenAI** when using an OpenAI API key.

## Test

1. Start the app.
2. Upload `sample_sales.csv`.
3. Select a provider.
4. Enter the matching API key.
5. Ask:

`What are total units sold by region?`

Then try:

`Which region has the highest average unit price?`

and:

`Plot units sold over date.`

## What was fixed

- Added Groq support.
- Added clearer provider-specific API-key handling.
- Added generated-code cleanup.
- Added automatic one-time code repair when generated pandas code fails.
- Added safer date-column normalization for uploaded CSVs.
- Added better handling of empty model responses.
- Added explicit model defaults per provider.
- Added error details instead of silently failing.
 <!-- py -3.10 -m venv venv
>> .\venv\Scripts\Activate.ps1
>> pip install -r requirements.txt
>> streamlit run app.py -->