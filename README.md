# AI Dev Orchestrator (MVP)

কোনো একক AI বা প্ল্যাটফর্মের উপর নির্ভরশীল না — Gemini, Groq, Cerebras, OpenRouter-এর ফ্রি টিয়ার ঘুরিয়ে ঘুরিয়ে ব্যবহার করে কোড জেনারেট, validate, auto-fix, commit ও push করে।

## কীভাবে কাজ করে

```
tasks.json (pending টাস্ক)
      │
Provider Router (Gemini → Groq → Cerebras → OpenRouter, rate-limit হলে পরেরটা)
      │
কোড জেনারেট → ফাইলে লেখা
      │
flutter analyze / dart format / flutter test
      │
   fail? ──► error ফেরত AI-কে ──► আবার জেনারেট (max ৩ বার)
      │
   pass ──► git commit + push ──► পরের টাস্ক
```

## সেটআপ (লোকাল)

```bash
pip install -r requirements.txt

export GEMINI_API_KEY="..."       # অন্তত একটা key দিলেই চলবে
export GROQ_API_KEY="..."
export CEREBRAS_API_KEY="..."
export OPENROUTER_API_KEY="..."

python -m orchestrator.main \
  --project ./path/to/your/flutter/app \
  --tasks ./tasks.json \
  --rules ./PROJECT_RULES.md
```

`tasks.example.json` কপি করে `tasks.json` বানাও এবং নিজের টাস্ক লেখো।

## GitHub Actions দিয়ে অটোমেট করা

1. এই পুরো repo GitHub-এ push করো
2. Repo Settings → Secrets → Actions-এ `GEMINI_API_KEY`, `GROQ_API_KEY` ইত্যাদি যোগ করো
3. `Actions` ট্যাব থেকে `AI Dev Orchestrator` workflow ম্যানুয়ালি রান করো (বা cron অনুযায়ী নিজে চলবে)

## Free tier কনফিগারেশন (২০২৬ অনুযায়ী, নিয়মিত বদলায় — নিজে যাচাই করে নাও)

| Provider | মোটামুটি লিমিট |
|---|---|
| Gemini (AI Studio) | ~১৫০০ req/day, ক্রেডিট কার্ড লাগে না, স্থায়ী ফ্রি টিয়ার |
| Groq | ৩০ req/min, ৬,০০০ token/min, ~১৪,৪০০ req/day |
| Cerebras | ~১M token/day, তবে মডেল লিস্ট মাঝে মাঝে বদলে যায় |
| OpenRouter (:free মডেল) | ~২০ req/min, ~২০০ req/day |

## কেন এভাবে ডিজাইন করা হয়েছে (এবং কী ইচ্ছাকৃতভাবে বাদ দেওয়া হয়েছে)

- **Sequential queue, parallel worker না** — একজন ডেভেলপারের জন্য branch/merge conflict handle করা রিভিউ সময়ের চেয়ে বেশি খরচ করে। queue ধীর কিন্তু predictable ও debug-যোগ্য।
- **Planner এখানে rule-based (মানুষ নিজেই tasks.json লেখে)**, AI না — যাতে প্রজেক্ট স্ট্রাকচার প্রতিবার না বদলে যায়। AI-driven planner ভবিষ্যতে যোগ করা যায়, কিন্তু আগে stable base দরকার।
- **flutter না থাকলে validator gracefully skip করে** — তাই একই orchestrator Node.js, Python বা যেকোনো প্রজেক্টে reuse করা যাবে, শুধু `validator.py` বদলে দিলেই হবে।

## পরের ধাপ (যখন MVP স্টেবল হবে)

1. `validator.py`-কে প্রজেক্ট-এগনস্টিক করা (config দিয়ে কমান্ড ঠিক করা)
2. Embedding-based context retrieval (পুরো repo না পাঠিয়ে শুধু relevant snippet)
3. Multiple provider-কে parallel-এ ছোট, independent টাস্কে ব্যবহার করা (একবারে একটাই ফাইল পরিবর্তন করে এমন টাস্কে ঝুঁকি কম)
4. Dashboard (এই ধাপে দরকার নেই — `tasks.json` + git history-ই এখন dashboard)
