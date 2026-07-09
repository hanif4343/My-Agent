# Project Rules (Shared Memory)

এই ফাইলটা প্রতিটা AI call-এর system prompt-এ যোগ হয়, যাতে
কোনো provider বদলালেও কোড স্টাইল/আর্কিটেকচার একই থাকে।

## আর্কিটেকচার
- State management: Riverpod
- Folder structure: lib/models, lib/repositories, lib/screens, lib/widgets
- Local storage: Hive

## কোডিং কনভেনশন
- সব ক্লাস নাম PascalCase
- সব ফাইল নাম snake_case.dart
- প্রতিটা public মেথডে ডক কমেন্ট বাধ্যতামূলক না, তবে জটিল লজিকে থাকা ভালো
- Null-safety বাধ্যতামূলক, কোনো `dynamic` টাইপ ব্যবহার করা যাবে না যদি নির্দিষ্ট টাইপ জানা থাকে

## যা করা যাবে না
- নতুন কোনো external package যোগ করা যাবে না prior approval ছাড়া
- বিদ্যমান পাবলিক API/method signature ভাঙা যাবে না
