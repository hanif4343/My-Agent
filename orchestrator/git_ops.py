"""ছোট Git wrapper — commit ও push।"""

import subprocess


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def commit_and_push(project_dir: str, message: str, push: bool = True) -> dict:
    add = run(["git", "add", "-A"], project_dir)
    commit = run(["git", "commit", "-m", message], project_dir)
    log = add.stdout + add.stderr + commit.stdout + commit.stderr

    if push:
        pushr = run(["git", "push"], project_dir)
        log += pushr.stdout + pushr.stderr
        ok = pushr.returncode == 0 or "nothing to commit" in commit.stdout
    else:
        ok = True

    return {"ok": ok, "output": log}
