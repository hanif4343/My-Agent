"""
Build Health Check: `flutter build apk --debug` চালিয়ে দেখে আসল build সফল হয় কিনা
(per-task flutter analyze/test এটা ধরতে পারে না, কারণ Gradle/Kotlin toolchain
সমস্যা শুধু আসল build করলেই বোঝা যায়)।

Build fail করলে:
1. Error output নেওয়া হয়
2. Candidate infra ফাইলগুলোর (pubspec.yaml, android/build.gradle,
   android/app/build.gradle, android/settings.gradle) বর্তমান কনটেন্ট AI-কে দেখানো হয়
3. AI বলে দেয় কোন ফাইল বদলাতে হবে, নতুন সম্পূর্ণ কনটেন্ট দেয়
4. সেই ফাইল লেখা হয়, আবার build করা হয় (max ২ বার চেষ্টা)
5. তারপরও fail করলে raw error নিয়ে exit code 1 দিয়ে থামে (workflow এটা ধরে email পাঠাবে)

চালানোর নিয়ম:
    python -m orchestrator.build_check --project ./output
"""

import argparse
import subprocess
import sys
from pathlib import Path

from .providers import ProviderRouter, AllProvidersFailedError

MAX_FIX_ATTEMPTS = 2

CANDIDATE_FILES = [
    "pubspec.yaml",
    "android/build.gradle",
    "android/app/build.gradle",
    "android/settings.gradle",
]

SYSTEM_PROMPT = """তুমি একজন সিনিয়র Flutter/Android বিল্ড ইঞ্জিনিয়ার।
Gradle/Flutter build fail করেছে। নিচে error এবং কয়েকটা candidate ফাইলের বর্তমান
কনটেন্ট দেওয়া আছে। বুঝে বলো ঠিক কোন ফাইলে সমস্যা এবং সেটার সম্পূর্ণ সংশোধিত কনটেন্ট দাও।

আউটপুট অবশ্যই এই ফরম্যাটে হতে হবে, প্রথম লাইনে ফাইলের path, তারপর একটা code fence:

TARGET_FILE: android/app/build.gradle
```
...সম্পূর্ণ সংশোধিত ফাইলের কনটেন্ট...
```

এর বাইরে কোনো ব্যাখ্যা লিখবে না। যেই ফাইল ঠিক করা দরকার শুধু সেটারই সম্পূর্ণ কনটেন্ট দেবে,
আংশিক/diff না।
"""


def run_build(project_dir: str, mode: str = "debug") -> dict:
    try:
        result = subprocess.run(
            ["flutter", "build", "apk", f"--{mode}"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=900,
        )
        ok = result.returncode == 0
        return {"ok": ok, "output": (result.stdout + result.stderr)[-6000:]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "output": "build টাইমআউট হয়েছে (১৫ মিনিট)"}


def build_fix_prompt(project_dir: str, error: str) -> str:
    snippets = [f"--- BUILD ERROR ---\n{error}\n--- END ERROR ---\n"]
    for cf in CANDIDATE_FILES:
        p = Path(project_dir) / cf
        if p.exists():
            snippets.append(f"--- {cf} ---\n{p.read_text(encoding='utf-8')}\n")
    return "\n".join(snippets)


def parse_ai_fix(text: str):
    lines = text.strip().splitlines()
    target_file = None
    for line in lines:
        if line.strip().startswith("TARGET_FILE:"):
            target_file = line.split("TARGET_FILE:", 1)[1].strip()
            break
    if not target_file:
        return None, None

    if "```" not in text:
        return target_file, None
    parts = text.split("```")
    if len(parts) < 2:
        return target_file, None
    block = parts[1]
    block_lines = block.split("\n", 1)
    if len(block_lines) == 2 and len(block_lines[0].split()) <= 1:
        content = block_lines[1]
    else:
        content = block
    return target_file, content.strip() + "\n"


def main():
    parser = argparse.ArgumentParser(description="Build Health Check + AI auto-fix")
    parser.add_argument("--project", required=True)
    parser.add_argument("--mode", default="debug", choices=["debug", "release"])
    args = parser.parse_args()

    router = ProviderRouter()
    print(f"সক্রিয় provider: {[p['name'] for p in router.providers]}")

    attempt = 0
    while True:
        attempt += 1
        print(f"\n▶ Build চেষ্টা {attempt}/{MAX_FIX_ATTEMPTS + 1} ({args.mode})")
        result = run_build(args.project, args.mode)

        if result["ok"]:
            print("✔ Build সফল হয়েছে।")
            return 0

        print(f"✖ Build ব্যর্থ:\n{result['output'][-1500:]}")

        if attempt > MAX_FIX_ATTEMPTS:
            print("\n✖ সর্বোচ্চ fix চেষ্টা শেষ, এখনো build fail করছে।")
            print("::error::Build Health Check ব্যর্থ, ম্যানুয়াল চেক দরকার।")
            with open("build_check_failure.txt", "w", encoding="utf-8") as f:
                f.write(result["output"])
            return 1

        print("AI দিয়ে fix করার চেষ্টা করা হচ্ছে...")
        prompt = build_fix_prompt(args.project, result["output"])
        try:
            ai_result = router.generate(SYSTEM_PROMPT, prompt)
        except AllProvidersFailedError as e:
            print(f"✖ সব provider ব্যর্থ: {e}")
            with open("build_check_failure.txt", "w", encoding="utf-8") as f:
                f.write(result["output"])
            return 1

        target_file, content = parse_ai_fix(ai_result["text"])
        if not target_file or content is None:
            print("✖ AI response থেকে target file/content বোঝা যায়নি।")
            with open("build_check_failure.txt", "w", encoding="utf-8") as f:
                f.write(result["output"])
            return 1

        target_path = Path(args.project) / target_file
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        print(f"📝 {target_file} আপডেট করা হলো (provider: {ai_result['provider']})। আবার build করা হচ্ছে...")


if __name__ == "__main__":
    sys.exit(main())
