"""
Shared Memory পড়ে system prompt বানানো, যাতে প্রতিটা AI call
প্রজেক্টের নিয়ম-কানুন জানে — একটা provider আরেকটার কাজ ভাঙবে না।
"""

from pathlib import Path

SYSTEM_TEMPLATE = """তুমি একজন সিনিয়র Flutter ইঞ্জিনিয়ার। শুধু কোড লিখবে, ব্যাখ্যা নয়।

প্রজেক্ট নিয়ম (PROJECT_RULES.md):
{rules}

গুরুত্বপূর্ণ:
- শুধু চাওয়া ফাইলটার সম্পূর্ণ কনটেন্ট দাও, markdown code fence সহ।
- ফাইলের বাইরে কোনো ব্যাখ্যা, ভূমিকা বা মন্তব্য লিখবে না।
- বিদ্যমান আর্কিটেকচার/নেমিং কনভেনশন ভাঙবে না।
"""

FIX_TEMPLATE = """আগের চেষ্টায় নিচের ফাইলটা এই এররগুলো দিচ্ছে:

--- ERROR ---
{error}
--- END ERROR ---

--- বর্তমান ফাইল কনটেন্ট ({target_file}) ---
{current_content}
--- END FILE ---

শুধু ঠিক করা সম্পূর্ণ ফাইলটা আবার দাও, code fence সহ, কোনো ব্যাখ্যা ছাড়া।
"""


def load_rules(rules_path: str) -> str:
    p = Path(rules_path)
    if p.exists():
        return p.read_text(encoding="utf-8")
    return "(কোনো PROJECT_RULES.md পাওয়া যায়নি — সাধারণ Flutter best practice অনুসরণ করো)"


def build_system_prompt(rules_path: str) -> str:
    return SYSTEM_TEMPLATE.format(rules=load_rules(rules_path))


def build_task_prompt(task: dict, project_dir: str) -> str:
    context_snippets = []
    for cf in task.get("context_files", []):
        p = Path(project_dir) / cf
        if p.exists():
            context_snippets.append(f"--- {cf} ---\n{p.read_text(encoding='utf-8')}")

    context_block = "\n\n".join(context_snippets) if context_snippets else "(কোনো এক্সট্রা context ফাইল নেই)"

    return (
        f"টাস্ক: {task['title']}\n\n"
        f"নির্দেশনা: {instruction = task.get("instructions") or task.get("instruction", "")}\n\n"
        f"টার্গেট ফাইল: {task['target_file']}\n\n"
        f"প্রাসঙ্গিক ফাইলসমূহ:\n{context_block}"
    )


def build_fix_prompt(task: dict, project_dir: str, error: str) -> str:
    target = Path(project_dir) / task["target_file"]
    current = target.read_text(encoding="utf-8") if target.exists() else "(ফাইল এখনো তৈরি হয়নি)"
    return FIX_TEMPLATE.format(error=error, target_file=task["target_file"], current_content=current)


def extract_code(text: str) -> str:
    """AI রেসপন্স থেকে ```...``` এর ভেতরের কোড বের করে। fence না থাকলে পুরো টেক্সট রিটার্ন করে।"""
    if "```" in text:
        parts = text.split("```")
        # parts[1] সাধারণত ```dart\ncode``` হলে "dart\ncode" হবে
        if len(parts) >= 2:
            block = parts[1]
            lines = block.split("\n", 1)
            if len(lines) == 2 and len(lines[0].split()) <= 1:
                return lines[1].strip() + "\n"
            return block.strip() + "\n"
    return text.strip() + "\n"
