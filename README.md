# AI Dev Orchestrator (MVP)

কোনো একক AI বা প্ল্যাটফর্মের উপর নির্ভরশীল না — ৭টা ফ্রি LLM provider ঘুরিয়ে ঘুরিয়ে ব্যবহার করে কোড জেনারেট, validate, auto-fix, commit ও push করে। **Flutter, Python, Kotlin, Node — যেকোনো ভাষার প্রজেক্টে কাজ করে**।

## দুইটা রিপো — Control vs Output

এই সিস্টেম দুইটা আলাদা GitHub রিপো ব্যবহার করে:

- **Control রিপো** (এই রিপো, `My-Agent`): orchestrator কোড, `tasks.json`, `PROJECT_RULES.md`, workflow — এখান থেকে সব চালানো হয়
- **Output রিপো** (যেমন `My-Story-from-Agent`): আসল প্রজেক্টের কোড এখানে জমা হয়, কমিট হয়, build হয়

Workflow control রিপোতে ট্রিগার হয়, কিন্তু ভেতরে output রিপো আলাদাভাবে checkout করে সেখানে লিখে/কমিট করে।

### সেটআপ (একবারই করতে হবে)

1. **Output রিপো বানাও** (খালি, শুধু README সহ) — যেমন `github.com/username/My-Story-from-Agent`
2. **একটা Personal Access Token বানাও** যেটার শুধু ওই output রিপোতে access আছে:
   - GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new
   - Repository access: শুধু output রিপো সিলেক্ট করো
   - Permissions: **Contents: Read and write**
3. Control রিপোর Settings → Secrets → Actions-এ এই token যোগ করো নামে: **`OUTPUT_REPO_TOKEN`**
4. `.github/workflows/orchestrator.yml` ও `build-apk.yml` ফাইলে উপরের দিকে `OUTPUT_REPO:` ভ্যালু নিজের output রিপোর নামে বদলে নাও (ফরম্যাট: `owner/repo-name`)

## নতুন টাস্ক যোগ করার সহজ উপায় (মোবাইল থেকেই)

1. Control রিপোতে `Actions` ট্যাব → `Add Orchestrator Task` → `Run workflow`
2. ফর্মে দাও:
   - **title**: সংক্ষিপ্ত নাম
   - **instruction**: কী বানাতে হবে তার বিস্তারিত
   - **target_file**: output প্রজেক্টের ভেতরে কোন ফাইলে লেখা হবে (যেমন `lib/models/scene.dart`)
3. Submit করলেই `tasks.json`-এ (control রিপোতে) টাস্ক যোগ হয়ে যাবে
4. `AI Dev Orchestrator` workflow চালালে (ম্যানুয়ালি বা cron) সেই টাস্ক প্রসেস হয়ে output রিপোতে কমিট হবে

**প্রজেক্টের ভাষা/validate commands** একবারই ঠিক করতে হয় — output রিপোর রুটে `orchestrator.config.json` বসিয়ে দিলেই হয় (নিচে দেখো)।

## কীভাবে কাজ করে

```
tasks.json (control রিপোতে, pending টাস্ক)
      │
Provider Router (Gemini → Groq → Cerebras → Mistral → NVIDIA → SambaNova → OpenRouter)
      │
কোড জেনারেট → output রিপোতে ফাইলে লেখা
      │
orchestrator.config.json এর validate_commands চালানো (flutter pub get, analyze, test ইত্যাদি)
      │
   fail? ──► error ফেরত AI-কে ──► আবার জেনারেট (max ৩ বার)
      │
   pass ──► output রিপোতে git commit + push ──► পরের টাস্ক
```

## সেটআপ (লোকাল/টেস্ট)

```bash
pip install -r requirements.txt

export GEMINI_API_KEY="..."       # অন্তত একটা key দিলেই চলবে
export GROQ_API_KEY="..."
export CEREBRAS_API_KEY="..."

python -m orchestrator.main \
  --project ./path/to/output/checkout \
  --tasks ./tasks.json \
  --rules ./PROJECT_RULES.md
```

## Validation যেভাবে কাজ করে (ভাষা-agnostic)

`validator.py` কোনো ভাষা hardcode করে না। **Output রিপোর রুটে** `orchestrator.config.json` ফাইলে যেসব কমান্ড দেওয়া থাকবে, ঠিক সেগুলোই চালাবে:

```json
{
  "language": "flutter",
  "validate_commands": ["flutter pub get", "flutter analyze", "flutter test"]
}
```

`config-examples/` ফোল্ডারে flutter, python, kotlin, node — প্রতিটার জন্য উদাহরণ config দেওয়া আছে। এটা output রিপোতে একবার বসিয়ে দিলেই যথেষ্ট, প্রতি টাস্কে বদলাতে হয় না।

## Manual-fix Email Alert (ঐচ্ছিক)

কোনো টাস্ক max retry শেষেও fail থাকলে ইমেইল যাবে। কাজ করাতে ৩টা Secret যোগ করো:

- `MAIL_USERNAME` — Gmail ঠিকানা
- `MAIL_PASSWORD` — Gmail App Password (সাধারণ পাসওয়ার্ড না; Google Account → Security → App Passwords থেকে বানাতে হবে)
- `MAIL_TO` — যেই ইমেইলে alert পাঠাতে চাও

এই secret গুলো না দিলে email step নিজে থেকেই স্কিপ হয়ে যাবে, error দেবে না।

## Provider Tracking

প্রতিটা টাস্ক সম্পন্ন/ব্যর্থ হওয়ার পর `tasks.json`-এ `"provider"` ফিল্ডে কোন AI সেটা করেছে তা সেভ হয়ে যায় — মনিটরিং app এখান থেকেই দেখাতে পারবে।

## Provider মডেল "404" বা "rate-limited" দিচ্ছে?

ফ্রি LLM provider-রা মাঝে মাঝেই মডেল বদলে/সরিয়ে দেয়, কোনো নোটিশ ছাড়াই। লগে `404 Not Found` বা মডেলের নাম-সম্পর্কিত error দেখলে:

1. `orchestrator/config.py` ফাইলে `PROVIDERS` লিস্টে গিয়ে সেই provider-এর `"model"` ভ্যালু বদলাও
2. বর্তমান মডেল নাম জানতে provider-এর official docs দেখো
3. একটা মডেল কাজ না করলে সেটা active_providers() লিস্ট থেকে সরিয়ে দিলে বাকিগুলো দিয়েই চলবে

## Build Health Check (স্বয়ংক্রিয় build ফিক্স চেষ্টা)

per-task validate (flutter analyze/test) Gradle/Kotlin toolchain সমস্যা ধরতে পারে না — শুধু আসল `flutter build apk` করলেই বোঝা যায়। তাই আলাদা একটা workflow (`Build Health Check`) দিনে একবার (ও ম্যানুয়ালি) `flutter build apk --debug` চালায়:

1. Build fail করলে error + `pubspec.yaml`/`build.gradle`/`settings.gradle` AI-কে দেখানো হয়
2. AI কোন ফাইল ঠিক করা দরকার বলে দেয়, নতুন কনটেন্ট দেয়
3. সেটা লিখে আবার build করা হয় (max ২ বার চেষ্টা)
4. এরপরও fail করলে email alert যাবে (`MAIL_USERNAME`/`MAIL_PASSWORD`/`MAIL_TO` secret লাগবে, আগের মতোই)

Debug build ব্যবহার করা হয়েছে (release না) যাতে Android keystore secret ছাড়াই এই চেক চলতে পারে — keystore শুধু `Build Release APK` workflow-এ লাগে।

## APK বানানো ও ফোনে ইনস্টল করা

যেকোনো সময় progress দেখতে চাইলে:

1. Control রিপোর `Actions` ট্যাব → `Build APK` workflow → `Run workflow`
2. ২-৩ মিনিট অপেক্ষা করো (build শেষ হলে সবুজ ✔ দেখাবে) — এটা সরাসরি output রিপো থেকে build করে
3. রান-এর পেজে নিচের দিকে **Artifacts** সেকশনে `our-story-apk` নামে একটা ZIP পাবে — ডাউনলোড করো
4. ফোনে ZIP এক্সট্রাক্ট করে `.apk` ফাইলটা ইনস্টল করো ("Install from unknown sources" অনুমতি দিতে হতে পারে)

এটা Play Store-এর মতো official-signed APK না (debug keystore দিয়ে সাইন করা) — শুধু নিজের ফোনে টেস্ট করার জন্য।

## GitHub Actions দিয়ে অটোমেট করা

1. এই পুরো control রিপো GitHub-এ push করো
2. output রিপো আলাদাভাবে বানাও (উপরের "সেটআপ" সেকশন দেখো)
3. Secrets যোগ করো: provider key গুলো + `OUTPUT_REPO_TOKEN`
4. `Actions` ট্যাব থেকে `AI Dev Orchestrator` workflow ম্যানুয়ালি রান করো (বা cron অনুযায়ী নিজে চলবে)

## Free tier কনফিগারেশন (২০২৬ অনুযায়ী, নিয়মিত বদলায় — নিজে যাচাই করে নাও)

| Provider | মোটামুটি লিমিট | সাইনআপ | Secret নাম |
|---|---|---|---|
| Gemini (AI Studio) | ~১৫০০ req/day, ক্রেডিট কার্ড লাগে না | aistudio.google.com/apikey | `GEMINI_API_KEY` |
| Groq | ~১,০০০ req/day | console.groq.com | `GROQ_API_KEY` |
| Cerebras | ~১M token/day | cloud.cerebras.ai | `CEREBRAS_API_KEY` |
| Mistral (La Plateforme) | ~১B token/month | console.mistral.ai | `MISTRAL_API_KEY` |
| NVIDIA NIM | ৪০ req/min, দৈনিক cap নেই | build.nvidia.com | `NVIDIA_API_KEY` |
| SambaNova | ~২০ req/day | cloud.sambanova.ai | `SAMBANOVA_API_KEY` |
| OpenRouter (:free মডেল) | ~২০ req/min, ~২০০ req/day | openrouter.ai | `OPENROUTER_API_KEY` |

যেকোনো একটা key দিলেই চলবে, বেশি key দিলে বেশি resilience।

## কেন এভাবে ডিজাইন করা হয়েছে

- **Sequential queue, parallel worker না** — branch/merge conflict handle করা রিভিউ সময়ের চেয়ে বেশি খরচ করে।
- **Planner rule-based** (মানুষ নিজেই tasks.json লেখে), AI না — প্রজেক্ট স্ট্রাকচার স্থিতিশীল রাখতে।
- **Control ও Output রিপো আলাদা** — orchestrator কোড আর আসল প্রজেক্টের ইতিহাস মিশে না গিয়ে পরিষ্কার থাকে; ভবিষ্যতে একই orchestrator দিয়ে একাধিক output প্রজেক্ট চালানো যাবে শুধু `OUTPUT_REPO` বদলে।
