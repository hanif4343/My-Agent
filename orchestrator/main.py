"""
Orchestrator মূল লুপ:

pending টাস্ক নাও → prompt বানাও → provider router দিয়ে কোড জেনারেট করো
→ ফাইলে লেখো → validate করো → fail হলে error ফিরিয়ে দিয়ে আবার জেনারেট করো
(max N বার) → pass করলে commit + push → পরের টাস্ক

চালানোর নিয়ম:
    python -m orchestrator.main --project ./my_flutter_app --tasks ./tasks.json
"""

import argparse
import sys
from pathlib import Path

from . import config
from .providers import ProviderRouter, AllProvidersFailedError
from .task_queue import TaskQueue, TaskValidationError
from . import validator, git_ops, prompts


def process_task(router: ProviderRouter, queue: TaskQueue, task: dict, project_dir: str, rules_path: str):
    print(f"\n▶ টাস্ক শুরু: {task['id']} — {task['title']}")
    queue.mark(task["id"], "in_progress")

    system_prompt = prompts.build_system_prompt(rules_path)
    user_prompt = prompts.build_task_prompt(task, project_dir)
    error_feedback = None

    for attempt in range(1, config.MAX_RETRY_PER_TASK + 1):
        queue.increment_attempt(task["id"])
        print(f"  চেষ্টা {attempt}/{config.MAX_RETRY_PER_TASK}")

        prompt_to_send = user_prompt
        if error_feedback:
            prompt_to_send = prompts.build_fix_prompt(task, project_dir, error_feedback)

        try:
            result = router.generate(system_prompt, prompt_to_send)
        except AllProvidersFailedError as e:
            queue.mark(task["id"], "failed", error=str(e))
            print(f"  ✖ সব provider ব্যর্থ: {e}")
            return False

        code = prompts.extract_code(result["text"])
        target_path = Path(project_dir) / task["target_file"]
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(code, encoding="utf-8")
        print(f"  📝 লেখা হলো: {task['target_file']} (provider: {result['provider']})")

        check = validator.validate_all(project_dir)
        if check["ok"]:
            print("  ✔ validation পাস")
            commit_msg = f"AI: {task['title']} ({result['provider']})"
            git_result = git_ops.commit_and_push(project_dir, commit_msg)
            if git_result["ok"]:
                queue.mark(task["id"], "done")
                print("  ✔ কমিট ও পুশ সম্পন্ন")
                return True
            else:
                queue.mark(task["id"], "failed", error=git_result["output"])
                print(f"  ✖ git push ব্যর্থ:\n{git_result['output']}")
                return False
        else:
            print(f"  ⚠ validation fail ({check['stage']}), AI-কে ফিক্স করতে বলা হচ্ছে")
            error_feedback = check["output"][:4000]  # খুব বড় error prompt-এ পাঠানো এড়াতে

    queue.mark(task["id"], "failed", error=error_feedback or "max retry শেষ")
    print(f"  ✖ {config.MAX_RETRY_PER_TASK} বার চেষ্টার পরও ব্যর্থ")
    return False


def main():
    parser = argparse.ArgumentParser(description="AI Dev Orchestrator MVP")
    parser.add_argument("--project", required=True, help="Flutter (বা যেকোনো) প্রজেক্টের path")
    parser.add_argument("--tasks", required=True, help="tasks.json এর path")
    parser.add_argument("--rules", default="PROJECT_RULES.md", help="shared rules ফাইলের path")
    parser.add_argument("--max-tasks", type=int, default=None, help="এই রানে সর্বোচ্চ কতগুলো টাস্ক প্রসেস হবে")
    args = parser.parse_args()

    router = ProviderRouter()
    print(f"সক্রিয় provider: {[p['name'] for p in router.providers]}")

    try:
        queue = TaskQueue(args.tasks)
    except TaskValidationError as e:
        print(f"\n✖ tasks.json ভুল আছে, থামছি:\n{e}\n")
        sys.exit(1)

    print("শুরুর অবস্থা:", queue.summary())

    processed = 0
    while True:
        if args.max_tasks is not None and processed >= args.max_tasks:
            print("\nmax-tasks সীমায় পৌঁছেছে, থামছি।")
            break

        task = queue.next_pending()
        if task is None:
            print("\nআর কোনো pending টাস্ক নেই। শেষ।")
            break

        process_task(router, queue, task, args.project, args.rules)
        processed += 1

    print("\nচূড়ান্ত অবস্থা:", queue.summary())


if __name__ == "__main__":
    sys.exit(main())
