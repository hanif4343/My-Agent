"""
tasks.json এ নতুন টাস্ক যোগ করে (শুধু My-Agent/control রিপোতে)।

লক্ষ্য করো: এই স্ক্রিপ্ট আর orchestrator.config.json লেখে না — কারণ আসল প্রজেক্ট
এখন একটা আলাদা "output" রিপোতে থাকে (My-Story-from-Agent), যেটা এই control
রিপোর অংশ না। orchestrator.config.json একবার ম্যানুয়ালি output রিপোতে বসিয়ে
দিলেই যথেষ্ট, প্রতি টাস্কে বদলানোর দরকার নেই।

চালানোর নিয়ম:
    python orchestrator/manage_tasks.py \
        --title "Create a calculator" \
        --instruction "add/subtract/multiply/divide ফাংশনসহ একটা calculator.py বানাও" \
        --target-file "calculator.py"
"""

import argparse
import json
import sys
from pathlib import Path


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
            "provider": None,
        }
    )
    tasks_path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    return new_id


def main():
    parser = argparse.ArgumentParser(description="Orchestrator টাস্ক ম্যানেজার")
    parser.add_argument("--title", required=True)
    parser.add_argument("--instruction", required=True)
    parser.add_argument("--target-file", required=True)
    parser.add_argument("--tasks-file", default="tasks.json")
    args = parser.parse_args()

    task_id = add_task(Path(args.tasks_file), args.title, args.instruction, args.target_file)
    print(f"✔ নতুন টাস্ক যোগ হলো: {task_id} — {args.title}")


if __name__ == "__main__":
    sys.exit(main())
