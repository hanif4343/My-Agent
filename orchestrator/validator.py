"""
ভাষা-agnostic validator।

প্রজেক্ট রুটে orchestrator.config.json থাকবে, যেখানে "validate_commands"
লিস্টে যেকোনো শেল কমান্ড দেওয়া যাবে (flutter analyze, pytest, ./gradlew build,
npm test — যা খুশি)। validator শুধু সেগুলো ক্রমান্বয়ে চালায়, প্রথম যেটায়
fail করে সেখানেই থামে। কোনো ভাষা hardcode করা নেই।
"""

import json
import shlex
import subprocess
from pathlib import Path

DEFAULT_CONFIG = {
    "language": "generic",
    "validate_commands": [],
}


def load_project_config(project_dir: str) -> dict:
    cfg_path = Path(project_dir) / "orchestrator.config.json"
    if not cfg_path.exists():
        return DEFAULT_CONFIG
    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"orchestrator.config.json পার্স করা যায়নি: {e}")

    data.setdefault("language", "generic")
    data.setdefault("validate_commands", [])
    return data


def run_command(command: str, project_dir: str, timeout: int = 600) -> dict:
    try:
        result = subprocess.run(
            shlex.split(command),
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        ok = result.returncode == 0
        return {"ok": ok, "output": result.stdout + result.stderr, "command": command}
    except FileNotFoundError:
        return {
            "ok": False,
            "output": f"কমান্ড খুঁজে পাওয়া যায়নি: '{command}'. "
                      f"workflow-এর 'setup' ধাপে এই টুল ইনস্টল করা আছে কিনা যাচাই করো।",
            "command": command,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "output": f"টাইমআউট: '{command}'", "command": command}


def validate_all(project_dir: str) -> dict:
    """
    orchestrator.config.json এর validate_commands একে একে চালায়।
    কোনো কমান্ড না থাকলে validation স্কিপ হয়ে যায় (ok=True ধরে নেওয়া হয়,
    যাতে নতুন/অজানা ভাষার প্রজেক্টেও orchestrator আটকে না যায়)।
    """
    config = load_project_config(project_dir)
    commands = config.get("validate_commands", [])

    if not commands:
        return {
            "stage": "none",
            "ok": True,
            "output": "(orchestrator.config.json এ কোনো validate_commands নেই — validation স্কিপ করা হলো)",
        }

    for cmd in commands:
        result = run_command(cmd, project_dir)
        if not result["ok"]:
            return {"stage": cmd, "ok": False, "output": result["output"]}

    return {"stage": "all", "ok": True, "output": "সব validate_commands পাস করেছে"}
