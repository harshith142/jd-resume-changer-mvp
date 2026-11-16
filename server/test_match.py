import json
from pathlib import Path
import requests

SERVER_DIR = Path(__file__).parent
SERVER_URL = "http://127.0.0.1:8765"

# Load resume profile
with open(
    SERVER_DIR / "resume_profile.json",
    "r",
    encoding="utf-8"
) as f:
    resume_profile = json.load(f)


jd_text = """
Software Engineer

We are looking for a Software Engineer with 1-3 years of experience.

Required Skills:
- Java
- Spring Boot
- REST APIs
- SQL
- Git

Responsibilities:
- Develop backend applications using Java and Spring Boot.
- Build and maintain REST APIs.
- Work with relational databases.
- Write clean and maintainable code.
- Collaborate with frontend developers.

Good to have:
- React
- Docker
- AWS
- Microservices
"""


print("======================================")
print("ANALYZING JOB DESCRIPTION")
print("======================================")

response = requests.post(
    f"{SERVER_URL}/analyze-jd",
    json={
        "jd": jd_text
    },
    timeout=120
)

print("JD STATUS:", response.status_code)

if response.status_code != 200:
    print(response.text)
    raise SystemExit(1)

jd_profile = response.json()

print(
    json.dumps(
        jd_profile,
        indent=2,
        ensure_ascii=False
    )
)


print()
print("======================================")
print("MATCHING JD WITH RESUME")
print("======================================")

response = requests.post(
    f"{SERVER_URL}/match",
    json={
        "jd_profile": jd_profile,
        "resume_profile": resume_profile
    },
    timeout=120
)

print("MATCH STATUS:", response.status_code)

if response.status_code != 200:
    print(response.text)
    raise SystemExit(1)

match_result = response.json()


print()
print("======================================")
print("MATCH RESULT")
print("======================================")

print(
    json.dumps(
        match_result,
        indent=2,
        ensure_ascii=False
    )
)


with open(
    SERVER_DIR / "match_result.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        match_result,
        f,
        indent=2,
        ensure_ascii=False
    )

with open(
    SERVER_DIR / "jd_profile.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        jd_profile,
        f,
        indent=2
    )
print()
print("======================================")
print("Saved:")
print("match_result.json")
print("jd_profile.json")
print("======================================")
