# Project Rules — Our Story (Hanif ❤️ Santona)

এই ফাইল প্রতিটা AI call-এর সাথে যায়। এটা MASTER_SPEC.md এর সংক্ষিপ্ত, কোডিং-ফোকাসড ভার্সন।

## আর্কিটেকচার
- Feature-First + Clean Architecture + MVVM
- Folder structure:
  ```
  lib/
    core/
      constants/        (enums: AppTheme, ChapterId, AnimationType, TransitionType)
      theme/
      utils/
    features/
      story/
        data/
          models/        (SceneModel ইত্যাদি — Hive TypeAdapter সহ)
          repositories/  (HiveSceneRepository)
        domain/
        presentation/
          creator_mode/
          story_mode/
          widgets/
    main.dart
  ```

## Storage
- Hive (offline only), কোনো Firebase/internet call না
- প্রতিটা model-এ `@HiveType`/`@HiveField` annotation ব্যবহার করবে, কিন্তু build_runner চালানো এই সিস্টেমে সম্ভব না — তাই **TypeAdapter হাতে লিখবে**, code generation (`.g.dart`) এর উপর নির্ভর করবে না

## অনুমোদিত প্যাকেজ (এই লিস্টের বাইরে নতুন প্যাকেজ যোগ করবে না)
- `hive`, `hive_flutter` — storage
- `path_provider` — ফাইল পাথ
- `video_player` — ভিডিও দৃশ্য
- `audioplayers` — মিউজিক ও ভয়েস প্লেব্যাক
- `record` — ভয়েস রেকর্ডিং
- `permission_handler` — ক্যামেরা/মাইক্রোফোন পারমিশন
- `image_picker`, `file_picker` — ছবি/ভিডিও নির্বাচন
- `provider` — state management (Riverpod না, simple ও AI-friendly রাখতে)
- `uuid` — Scene ID
- `google_fonts` — টাইপোগ্রাফি
- `lottie` — **অ্যানিমেশন লাইব্রেরির জন্য** (Heart Rain, Fireworks, Sparkle ইত্যাদি কাস্টম canvas painter দিয়ে না বানিয়ে ফ্রি Lottie JSON asset ব্যবহার করবে — `assets/animations/*.json` এ রাখা হবে, offline-ই কাজ করবে)

## কোডিং কনভেনশন
- ক্লাস নাম PascalCase, ফাইল নাম snake_case.dart
- Null-safety বাধ্যতামূলক
- প্রতিটা public মেথডে সংক্ষিপ্ত ডক কমেন্ট
- Creator Mode password: Hive-তে hashed (sha256) স্টোর হবে, plain text না

## Scene মডেলের ফিল্ড (স্পেসিফিকেশন অনুযায়ী)
`id (String/UUID), year (int), chapter (String), date (String), title (String), subtitle (String), storyText (String), photoPaths (List<String>), videoPaths (List<String>), voiceNotePaths (List<String>), musicPath (String?), theme (String), animationType (String), transitionType (String), durationSeconds (int), isFavorite (bool), tags (List<String>)`

## যা এই ধাপে করা হচ্ছে না (পরে হাতে/সরাসরি সহায়তায় হবে)
- কাস্টম canvas particle animation ডিজাইন (Lottie দিয়ে কভার হবে)
- চূড়ান্ত UI polish, রঙ/টাইমিং টিউনিং
- GitHub Actions APK build workflow (আলাদাভাবে যোগ হবে)
