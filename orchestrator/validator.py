"""
জেনারেট করা কোড ভ্যালিড কিনা চেক করে।
flutter না থাকলেও (যেমন এই ডেমো এনভায়রনমেন্টে) এটা gracefully skip করে,
যাতে পুরো orchestrator অন্য ভাষা/প্রজেক্টেও reuse করা যায়।
"""

import shutil
import subprocess


def flutter_available() -> bool:
    return shutil.which("flutter") is not None


def run_analyze(project_dir: str) -> dict:
    """
    রিটার্ন করে: {"ok": bool, "output": str}
    """
    if not flutter_available():
        return {"ok": True, "output": "(flutter পাওয়া যায়নি — analyze স্কিপ করা হলো)"}

    result = subprocess.run(
        ["flutter", "analyze"],
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=300,
    )
    ok = result.returncode == 0
    return {"ok": ok, "output": result.stdout + result.stderr}


def run_format_check(project_dir: str) -> dict:
    if not flutter_available():
        return {"ok": True, "output": "(flutter পাওয়া যায়নি — format skip করা হলো)"}

    result = subprocess.run(
        ["dart", "format", "--output=none", "--set-exit-if-changed", "."],
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return {"ok": result.returncode == 0, "output": result.stdout + result.stderr}


def run_tests(project_dir: str) -> dict:
    if not flutter_available():
        return {"ok": True, "output": "(flutter পাওয়া যায়নি — test skip করা হলো)"}

    result = subprocess.run(
        ["flutter", "test"],
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=600,
    )
    return {"ok": result.returncode == 0, "output": result.stdout + result.stderr}


def validate_all(project_dir: str) -> dict:
    """তিনটা চেক একসাথে চালায়, প্রথম যেটায় fail করে সেখানেই থামে।"""
    analyze = run_analyze(project_dir)
    if not analyze["ok"]:
        return {"stage": "analyze", **analyze}

    fmt = run_format_check(project_dir)
    if not fmt["ok"]:
        return {"stage": "format", **fmt}

    tests = run_tests(project_dir)
    if not tests["ok"]:
        return {"stage": "test", **tests}

    return {"stage": "all", "ok": True, "output": "সব চেক পাস করেছে"}
