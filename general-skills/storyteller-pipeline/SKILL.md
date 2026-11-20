---
name: storyteller-pipeline
description: End-to-end workflow for producing one Arabic Last Storyteller video — script, ElevenLabs voice, image-to-video animation, lip-sync, HyperFrames edit and export. Use when the user asks to make, animate or produce a video/episode/shot.
---

# خط إنتاج الحلقة

اقرأ `CLAUDE.md` و`brand-bible/brand-bible.md` أولًا. نفّذ المراحل بالترتيب وتوقف عند كل بوابة للموافقة. أي توليد مدفوع: اذكر الأداة والمدة والتكلفة التقريبية واطلب الموافقة، وابدأ بأقصر اختبار.

## المراحل

1. **السكربت** (`scripts/`): بنية Hook ← Setup ← Escalation ← Reveal ← Aftertaste، جمل قابلة للنطق، فصل الوقائع عن التخمين. لا تكرر الخطاف نفسه.
2. **البطاقات** (`storyboards/`): استخدم مهارة `scene-card` لكل لقطة. للمشاريع الجديدة استخدم brainstorming أولًا.
3. **الصوت** (`audio/final/`): ElevenLabs. `creative_list_voices` للاختيار، ثم `creative_generate_speech` (موديل `eleven_v3` أو `eleven_multilingual_v2` مع `language_code=ar`). جرّب أكثر من أداء، ثم ثبّت الصوت والإعدادات في `continuity-log/`.
4. **الحركة** (`video/generations/`): صورة إلى فيديو عبر `creative_generate_video` من مرجع معتمد مع identity anchor من الـ Bible. المرشحون للمقارنة: Veo 3.1، Gemini Omni Flash 1.1، Seedance 2.x (يقبل مرجع صوت)، Kling 3/4. شغّل أولًا ثانية الاختبار القصيرة نفسها على أداتين.
5. **Lip-sync**: إن لم يطابق فم اللقطة الصوت النهائي، مرّر الفيديو والصوت إلى `sync-lipsync-v3` أو `veed-lipsync-v2` أو `minimax-h3-max-lipsync`. بديل: Voice Changer (`eleven_multilingual_sts_v2`) على صوت اللقطة الأصلي للحفاظ على توقيت الفم.
6. **الفحص**: مهارة `quality-check`، ومن ثم ينتقل المعتمد إلى `video/approved/`.
7. **المونتاج** (`edit/projects/`): HyperFrames (`/hyperframes`, `/hyperframes-cli`). كابشنز عربية بتأثيرات `motion-effects-12` عند الحاجة، الشعار والعناوين، موسيقى خفيفة. المعاينة: `npx hyperframes preview`، التصدير: `npx hyperframes render` إلى `exports/16x9/` ثم `exports/9x16/`.

## ملاحظات

- التوليد غير حتمي: أبقِ كل المحاولات، واعتمد اللقطة التي تجتاز الفحص فقط.
- لا تولّد نصوصًا دقيقة داخل الفيديو.
- قيّم ثبات الشخصية على عدة لقطات متتابعة، لا لقطة واحدة.
