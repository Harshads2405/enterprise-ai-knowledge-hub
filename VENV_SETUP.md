# Python Virtual Environment

The virtual environment is intentionally not committed or zipped because a venv is
machine-specific and non-portable.

Windows PowerShell:
    py -3.12 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt

After activation:
    python --version
    pip --version
