"""
প্রজেক্ট টাইপ ও টাস্ক ইনফো নিয়ে:
1. app/orchestrator.config.json লেখে (project type অনুযায়ী সঠিক validate_commands সহ)
2. tasks.json এ নতুন টাস্ক যোগ করে

চালানোর নিয়ম:
    python orchestrator/manage_tasks.py \
        --project-type python \
        --title "Create a calculator" \
        --instruction "add/subtract/multiply/divide ফাংশনসহ একটা calculator.py বানাও" \
        --target-file "calculator.py"
"""

import argparse
import json
import sys
from pathlib import Path

# প্রতিটা project type-এর জন্য ডিফল্ট validate_commands টেমপ্লেট।
# {target_file} প্লেসহোল্ডার থাকলে সেটা আসল target_file দিয়ে বদলে যাবে।
CONFIG_TEMPLATES = {
    "flutter": {
        "language": "flutter",
        "validate_commands": ["flutter analyze", "flutter test"],
    },
    "python": {
        "language": "python",
        "validate_commands": ["python -m py_compile {target_file}"],
    },
    "kotlin": {
        "language": "kotlin",
        "validate_commands": ["./gradlew build --no-daemon"],
    },
    "node": {
        "language": "node",
        "validate_commands": ["npm install", "npm test"],
    },
    "generic": {
        "language": "generic",
        "validate_commands": [],
    },
}


def ensure_config(project_dir: Path, project_type: str, target_file: str) -> Path:
    template = CONFIG_TEMPLATES.get(project_type, CONFIG_TEMPLATES["generic"])
    cfg = {
        "language": template["language"],
        "validate_commands": [
            c.format(target_file=target_file) for c in template["validate_commands"]
        ],
    }
    project_dir.mkdir(parents=True, exist_ok=True)
    cfg_path = project_dir / "orchestrator.config.json"
    cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    return cfg_path


def add_task(tasks_path: Path, title: str, instruction: str, target_file: str) -> str:
    if tasks_path.exists():
        tasks = json.loads(tasks_path.read_text(encoding="utf-8"))
    else:
        tasks = []

    next_num = len(tasks) + 1
    new_id = f"task_{next_num:03d}"

    tasks.append(
        {
            "id": new_id,
            "title": title,
            "instruction": instruction,
            "target_file": target_file,
            "context_files": [],
            "status": "pending",
            "attempts": 0,
            "last_error": None,
        }
    )
    tasks_path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    return new_id


def main():
    parser = argparse.ArgumentParser(description="Orchestrator টাস্ক ও config ম্যানেজার")
    parser.add_argument("--project-type", required=True, choices=list(CONFIG_TEMPLATES.keys()))
    parser.add_argument("--title", required=True)
    parser.add_argument("--instruction", required=True)
    parser.add_argument("--target-file", required=True)
    parser.add_argument("--project-dir", default="app", help="প্রজেক্ট কোন ফোল্ডারে আছে (রিপো রুট থেকে)")
    parser.add_argument("--tasks-file", default="tasks.json")
    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    cfg_path = ensure_config(project_dir, args.project_type, args.target_file)
    task_id = add_task(Path(args.tasks_file), args.title, args.instruction, args.target_file)

    print(f"✔ config লেখা হলো: {cfg_path} (language={args.project_type})")
    print(f"✔ নতুন টাস্ক যোগ হলো: {task_id} — {args.title}")


if __name__ == "__main__":
    sys.exit(main())
