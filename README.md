# AI Dev Orchestrator (MVP)

কোনো একক AI বা প্ল্যাটফর্মের উপর নির্ভরশীল না — Gemini, Groq, Cerebras, OpenRouter-এর ফ্রি টিয়ার ঘুরিয়ে ঘুরিয়ে ব্যবহার করে কোড জেনারেট, validate, auto-fix, commit ও push করে। **Flutter, Python, Kotlin, Node — যেকোনো ভাষার প্রজেক্টে কাজ করে**, কোনো ভাষা hardcode করা নেই।

## নতুন টাস্ক যোগ করার সবচেয়ে সহজ উপায় (মোবাইল থেকেই)

টার্মিনাল বা কোনো টোকেন ছাড়াই, শুধু GitHub-এর Actions ট্যাব থেকে ফর্ম পূরণ করে:

1. রিপোতে `Actions` ট্যাবে যাও
2. বাম পাশে `Add Orchestrator Task` workflow বেছে নাও
3. `Run workflow` বাটনে চাপ দাও — একটা ফর্ম আসবে:
   - **project_type**: `flutter` / `python` / `kotlin` / `node` / `generic` (dropdown)
   - **title**: সংক্ষিপ্ত নাম
   - **instruction**: কী বানাতে হবে তার বিস্তারিত
   - **target_file**: কোন ফাইলে লেখা হবে (যেমন `calculator.py` বা `lib/models/scene.dart`)
4. Submit করলেই এটা নিজে থেকে `tasks.json`-এ টাস্ক যোগ করবে এবং `app/orchestrator.config.json` সেই ভাষার জন্য সঠিক validate commands দিয়ে বসিয়ে দেবে
5. এরপর `AI Dev Orchestrator` workflow (ম্যানুয়ালি বা cron অনুযায়ী) চালালেই সেই টাস্ক প্রসেস হবে

**একটা গুরুত্বপূর্ণ ব্যাপার:** `orchestrator.config.json` পুরো প্রজেক্টের জন্য একটাই — মানে একটা repo একবারে এক ধরনের প্রজেক্ট (হয় Flutter, হয় Python) চালানোর জন্য ডিজাইন করা। ভিন্ন ভিন্ন ভাষার সম্পূর্ণ আলাদা প্রজেক্টের জন্য আলাদা GitHub repo ব্যবহার করাই ভালো।

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

## Validation যেভাবে কাজ করে (ভাষা-agnostic)

`validator.py` কোনো ভাষা hardcode করে না। প্রজেক্টের `orchestrator.config.json` ফাইলে যেসব কমান্ড দেওয়া থাকবে, ঠিক সেগুলোই ক্রমান্বয়ে চালাবে:

```json
{
  "language": "python",
  "validate_commands": ["python -m py_compile calculator.py", "python -m pytest"]
}
```

`config-examples/` ফোল্ডারে flutter, python, kotlin, node — প্রতিটার জন্য উদাহরণ config দেওয়া আছে। `manage_tasks.py` টুলটা এগুলোই স্বয়ংক্রিয়ভাবে বসিয়ে দেয়, তাই সাধারণত হাতে লিখতে হবে না।

## Manual-fix Email Alert (ঐচ্ছিক)

কোনো টাস্ক max retry শেষেও fail থাকলে ইমেইল যাবে। কাজ করাতে ৩টা Secret যোগ করো:

- `MAIL_USERNAME` — Gmail ঠিকানা
- `MAIL_PASSWORD` — Gmail App Password (সাধারণ পাসওয়ার্ড না; Google Account → Security → App Passwords থেকে বানাতে হবে)
- `MAIL_TO` — যেই ইমেইলে alert পাঠাতে চাও

এই secret গুলো না দিলে email step নিজে থেকেই স্কিপ হয়ে যাবে, error দেবে না।

## Provider Tracking

প্রতিটা টাস্ক সম্পন্ন/ব্যর্থ হওয়ার পর `tasks.json`-এ `"provider"` ফিল্ডে কোন AI (gemini/groq/cerebras/openrouter) সেটা করেছে তা সেভ হয়ে যায় — মনিটরিং app এখান থেকেই দেখাতে পারবে।

## Provider মডেল "404" বা "rate-limited" দিচ্ছে?

ফ্রি LLM provider-রা (Groq, Cerebras) মাঝে মাঝেই মডেল বদলে/সরিয়ে দেয়, কোনো নোটিশ ছাড়াই। লগে `404 Not Found` বা মডেলের নাম-সম্পর্কিত error দেখলে:

1. `orchestrator/config.py` ফাইলে `PROVIDERS` লিস্টে গিয়ে সেই provider-এর `"model"` ভ্যালু বদলাও
2. বর্তমান মডেল নাম জানতে provider-এর official docs দেখো (Groq: console.groq.com/docs/models, Cerebras: cloud.cerebras.ai)
3. একটা মডেল কাজ না করলে সেটা active_providers() লিস্ট থেকে সরিয়ে দিলে বাকিগুলো দিয়েই চলবে

## APK বানানো ও ফোনে ইনস্টল করা

যেকোনো সময় progress দেখতে চাইলে:

1. `Actions` ট্যাব → `Build APK` workflow বেছে নাও → `Run workflow`
2. ২-৩ মিনিট অপেক্ষা করো (build শেষ হলে সবুজ ✔ দেখাবে)
3. রান-এর পেজে নিচের দিকে **Artifacts** সেকশনে `our-story-apk` নামে একটা ZIP পাবে — ট্যাপ করে ডাউনলোড করো
4. ফোনে ZIP এক্সট্রাক্ট করে `.apk` ফাইলটা খুলে ইনস্টল করো ("Install from unknown sources" অনুমতি চাইতে পারে, allow করো)

এটা Play Store-এর মতো official-signed APK না (debug keystore দিয়ে সাইন করা) — শুধু নিজের ফোনে টেস্ট করার জন্য, এতে কোনো সমস্যা নেই।

## GitHub Actions দিয়ে অটোমেট করা

1. এই পুরো repo GitHub-এ push করো
2. Repo Settings → Secrets → Actions-এ `GEMINI_API_KEY`, `GROQ_API_KEY` ইত্যাদি যোগ করো
3. `Actions` ট্যাব থেকে `AI Dev Orchestrator` workflow ম্যানুয়ালি রান করো (বা cron অনুযায়ী নিজে চলবে)

## Free tier কনফিগারেশন (২০২৬ অনুযায়ী, নিয়মিত বদলায় — নিজে যাচাই করে নাও)

| Provider | মোটামুটি লিমিট | সাইনআপ | Secret নাম |
|---|---|---|---|
| Gemini (AI Studio) | ~১৫০০ req/day, ক্রেডিট কার্ড লাগে না | aistudio.google.com/apikey | `GEMINI_API_KEY` |
| Groq | ~১,০০০ req/day (২০২৬-এ কমানো হয়েছে) | console.groq.com | `GROQ_API_KEY` |
| Cerebras | ~১M token/day, মডেল লিস্ট মাঝে মাঝে বদলায় | cloud.cerebras.ai | `CEREBRAS_API_KEY` |
| Mistral (La Plateforme) | ~১B token/month (generous) | console.mistral.ai | `MISTRAL_API_KEY` |
| NVIDIA NIM | ৪০ req/min, দৈনিক cap নেই | build.nvidia.com | `NVIDIA_API_KEY` |
| SambaNova | মাত্র ~২০ req/day (extra fallback হিসেবে ভালো) | cloud.sambanova.ai | `SAMBANOVA_API_KEY` |
| OpenRouter (:free মডেল) | ~২০ req/min, ~২০০ req/day | openrouter.ai | `OPENROUTER_API_KEY` |

যেকোনো একটা key দিলেই চলবে, বেশি key দিলে বেশি resilience — একটা rate-limit খেলে পরেরটা নিজে থেকে try হবে। নতুন provider যোগ করতে চাইলে `orchestrator/config.py`-তে `PROVIDERS` লিস্টে একটা এন্ট্রি বাড়াও, আর GitHub Secrets + `orchestrator.yml`-এর `env:` ব্লকে সেই key যোগ করো।

## কেন এভাবে ডিজাইন করা হয়েছে (এবং কী ইচ্ছাকৃতভাবে বাদ দেওয়া হয়েছে)

- **Sequential queue, parallel worker না** — একজন ডেভেলপারের জন্য branch/merge conflict handle করা রিভিউ সময়ের চেয়ে বেশি খরচ করে। queue ধীর কিন্তু predictable ও debug-যোগ্য।
- **Planner এখানে rule-based (মানুষ নিজেই tasks.json লেখে)**, AI না — যাতে প্রজেক্ট স্ট্রাকচার প্রতিবার না বদলে যায়। AI-driven planner ভবিষ্যতে যোগ করা যায়, কিন্তু আগে stable base দরকার।
- **flutter না থাকলে validator gracefully skip করে** — তাই একই orchestrator Node.js, Python বা যেকোনো প্রজেক্টে reuse করা যাবে, শুধু `validator.py` বদলে দিলেই হবে।

## পরের ধাপ (যখন MVP স্টেবল হবে)

1. `validator.py`-কে প্রজেক্ট-এগনস্টিক করা (config দিয়ে কমান্ড ঠিক করা)
2. Embedding-based context retrieval (পুরো repo না পাঠিয়ে শুধু relevant snippet)
3. Multiple provider-কে parallel-এ ছোট, independent টাস্কে ব্যবহার করা (একবারে একটাই ফাইল পরিবর্তন করে এমন টাস্কে ঝুঁকি কম)
4. Dashboard (এই ধাপে দরকার নেই — `tasks.json` + git history-ই এখন dashboard)
