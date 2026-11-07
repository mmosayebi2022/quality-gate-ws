import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

MODELS = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-flash-latest"]
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
MAX_CHARS = 12000
ATTEMPTS_PER_MODEL = 2


def read_file(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()[-MAX_CHARS:]
    except FileNotFoundError:
        return "(no output)"


def get_diff():
    base = os.environ["BASE_SHA"]
    head = os.environ["HEAD_SHA"]
    result = subprocess.run(
        ["git", "diff", f"{base}...{head}", "--", "app", "tests"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout[:MAX_CHARS]


def build_prompt(diff, test_output):
    return (
        "You are a senior code reviewer in a CI pipeline.\n"
        "A pull request FAILED the quality gate. Explain to a student, "
        "in simple Persian, why it failed and how to fix it.\n"
        "Use this format:\n"
        "1. Why the gate failed (1-2 sentences)\n"
        "2. Which functions or lines are the problem\n"
        "3. A short example of a test or fix\n"
        "Be concise and friendly.\n\n"
        f"=== TEST AND COVERAGE OUTPUT ===\n{test_output}\n\n"
        f"=== PR DIFF ===\n{diff}\n"
    )


def call_model(model, prompt):
    url = f"{API_BASE}/{model}:generateContent"
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 2048},
    }).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": os.environ["GEMINI_API_KEY"],
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        status = resp.status
        raw = resp.read().decode("utf-8", errors="replace")
    print(f"[{model}] HTTP {status}, body length {len(raw)}")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise ValueError(f"not JSON, first 300 chars: {raw[:300]}")
    candidates = data.get("candidates") or []
    if not candidates:
        raise ValueError(f"no candidates in answer: {raw[:300]}")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        raise ValueError(f"empty text, finishReason={candidates[0].get('finishReason')}")
    return text


def ask_model(prompt):
    for model in MODELS:
        for attempt in range(1, ATTEMPTS_PER_MODEL + 1):
            try:
                print(f"Trying {model} (attempt {attempt})")
                return call_model(model, prompt)
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", errors="replace")[:300]
                print(f"[{model}] HTTP error {e.code}: {detail}")
                if e.code in (400, 401, 403, 404):
                    break  # retrying will not help for this model
                if e.code == 429:
                    time.sleep(10)
            except Exception as e:
                print(f"[{model}] failed: {type(e).__name__}: {e}")
            time.sleep(3)
    return None


def post_comment(text):
    repo = os.environ["REPO"]
    pr = os.environ["PR_NUMBER"]
    url = f"https://api.github.com/repos/{repo}/issues/{pr}/comments"
    body = json.dumps({"body": text}).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
        },
    )
    urllib.request.urlopen(req, timeout=30)


def main():
    diff = get_diff()
    test_output = read_file("test_output.txt")
    review = ask_model(build_prompt(diff, test_output))
    if review is None:
        print("AI model did not answer. See messages above.")
        sys.exit(1)
    post_comment("## 🤖 AI Review\n\n" + review)
    print("Comment posted.")


if __name__ == "__main__":
    main()
