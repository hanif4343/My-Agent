"""
সহজ, স্বচ্ছ Task Queue — শুধু একটা JSON ফাইল।
ডেটাবেজ বা কোনো এক্সট্রা সার্ভিস লাগে না, তাই debug করা সহজ,
আর GitHub repo-তেই কমিট হয়ে থাকে বলে পুরো history দেখা যায়।

tasks.json গঠন:
[
  {
    "id": "task-001",
    "title": "Create Scene model",
    "instruction": "lib/models/scene.dart ফাইলে Scene ক্লাস বানাও...",
    "target_file": "lib/models/scene.dart",
    "context_files": ["lib/models/README.md"],
    "status": "pending",   # pending | in_progress | done | failed
    "attempts": 0,
    "last_error": null
  }
]
"""

import json
from pathlib import Path

REQUIRED_FIELDS = ["id", "title", "instruction", "target_file"]


class TaskValidationError(Exception):
    pass


class TaskQueue:
    def __init__(self, path: str):
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"Task file পাওয়া যায়নি: {path}")
        self._load()
        self._validate()

    def _load(self):
        self.tasks = json.loads(self.path.read_text(encoding="utf-8"))

    def _validate(self):
        """প্রতিটা টাস্কে দরকারি ফিল্ড আছে কিনা লোড করার সময়েই চেক করে,
        যাতে লুপের মাঝপথে অস্পষ্ট KeyError-এ ক্র্যাশ না করে।"""
        for i, t in enumerate(self.tasks):
            missing = [f for f in REQUIRED_FIELDS if f not in t or t[f] in (None, "")]
            if missing:
                raise TaskValidationError(
                    f"tasks.json এর {i}-নম্বর টাস্কে (id={t.get('id', '?')}) এই ফিল্ডগুলো "
                    f"অনুপস্থিত বা খালি: {missing}। প্রতিটা টাস্কে অবশ্যই "
                    f"id, title, instruction, target_file থাকতে হবে।"
                )
            t.setdefault("context_files", [])
            t.setdefault("status", "pending")
            t.setdefault("attempts", 0)
            t.setdefault("last_error", None)

    def _save(self):
        self.path.write_text(
            json.dumps(self.tasks, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def next_pending(self):
        for t in self.tasks:
            if t["status"] == "pending":
                return t
        return None

    def mark(self, task_id: str, status: str, error: str = None):
        for t in self.tasks:
            if t["id"] == task_id:
                t["status"] = status
                if error is not None:
                    t["last_error"] = error
                self._save()
                return
        raise KeyError(f"টাস্ক পাওয়া যায়নি: {task_id}")

    def increment_attempt(self, task_id: str):
        for t in self.tasks:
            if t["id"] == task_id:
                t["attempts"] = t.get("attempts", 0) + 1
                self._save()
                return t["attempts"]
        raise KeyError(f"টাস্ক পাওয়া যায়নি: {task_id}")

    def summary(self):
        counts = {}
        for t in self.tasks:
            counts[t["status"]] = counts.get(t["status"], 0) + 1
        return counts
