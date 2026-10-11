"""OpsPilot: educational enterprise-style incident assistant."""

from pathlib import Path
from dotenv import load_dotenv

# Load local developer config without putting secrets in source control.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")
