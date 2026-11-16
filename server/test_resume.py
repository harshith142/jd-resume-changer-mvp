import json
from pathlib import Path
import requests

SERVER_DIR = Path(__file__).parent
SERVER_URL = "http://127.0.0.1:8765"

# Read the actual Overleaf file
with open(SERVER_DIR / "master_resume.tex", "r", encoding="utf-8") as f:
    master_tex = f.read()

print("======================================")
print("MASTER RESUME LOADED")
print("======================================")
print(f"Characters: {len(master_tex)}")
print()

response = requests.post(
    f"{SERVER_URL}/analyze-resume",
    json={
        "master_tex": master_tex
    },
    timeout=120
)

print("HTTP STATUS:", response.status_code)
print()

if response.status_code != 200:
    print("ERROR:")
    print(response.text)
    raise SystemExit(1)

result = response.json()

print("======================================")
print("RESUME PROFILE")
print("======================================")

print(json.dumps(result, indent=2, ensure_ascii=False))

# Save the result
with open(
    SERVER_DIR / "resume_profile.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        result,
        f,
        indent=2,
        ensure_ascii=False
    )

print()
print("======================================")
print("Saved to:")
print("resume_profile.json")
print("======================================")

print("======================================")