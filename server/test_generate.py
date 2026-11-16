import json
from pathlib import Path
import requests

SERVER_DIR = Path(__file__).parent
BASE_URL = "http://127.0.0.1:8765"


print("======================================")
print("LOADING MASTER TEX")
print("======================================")


with open(
    SERVER_DIR / "master_resume.tex",
    "r",
    encoding="utf-8"
) as f:

    master_tex = f.read()


print(f"MASTER TEX CHARACTERS: {len(master_tex)}")


print()
print("======================================")
print("LOADING JD PROFILE")
print("======================================")


with open(
    SERVER_DIR / "jd_profile.json",
    "r",
    encoding="utf-8"
) as f:

    jd_profile = json.load(f)


print("JD PROFILE LOADED")


print()
print("======================================")
print("LOADING MATCH RESULT")
print("======================================")


with open(
    SERVER_DIR / "match_result.json",
    "r",
    encoding="utf-8"
) as f:

    match_result = json.load(f)


print("MATCH RESULT LOADED")


print()
print("======================================")
print("GENERATING TAILORED RESUME")
print("======================================")


payload = {
    "master_tex": master_tex,
    "jd_profile": jd_profile,
    "match_result": match_result
}


response = requests.post(
    f"{BASE_URL}/generate-resume",
    json=payload,
    timeout=180
)


print("STATUS:", response.status_code)


if response.status_code != 200:

    print(response.text)
    raise SystemExit(1)


result = response.json()


print()
print("======================================")
print("GENERATION SUCCESSFUL")
print("======================================")


latex = result["latex"]


with open(
    SERVER_DIR / "tailored_resume.tex",
    "w",
    encoding="utf-8"
) as f:

    f.write(latex)


print(
    f"TAILORED TEX CHARACTERS: {len(latex)}"
)


print()
print("======================================")
print("CHANGES")
print("======================================")


for change in result.get("changes", []):

    print("-", change)


print()
print("======================================")
print("PRESERVED")
print("======================================")


for item in result.get("preserved", []):

    print("-", item)


print()
print("Saved:")
print("tailored_resume.tex")
