---
name: quality-check
description: Review a generated clip or frame of The Last Storyteller against the character reference and brand rules, and log the verdict. Use after every generation, before approving a shot.
---

# فحص الجودة

1. اسحب إطارات من اللقطة (ffmpeg، حوالي 640px) وقارنها بـ `character/references/avatar-original.jpg`.
2. أجب بنعم/لا/غير مؤكد على كل بند:
   - الشخصية مطابقة للمرجع؟ العينان والأنف واللحية والشعر ثابتة؟
   - المعطف وملمس الطين والألوان متسقة؟
   - الحركة تخدم المعنى؟ اليدان والأصابع سليمتان؟
   - الفم متزامن مع الصوت (عند الكلام)؟ ملاحظة: الحكم على المزامنة يحتاج مشاهدة المالك، لا تدّعِه من إطارات ثابتة.
   - الإضاءة والظلال متسقة؟ قفزات أو وميض؟
   - النصوص مقروءة؟ المعلومات الواقعية موثقة؟ التصدير مناسب للمنصة؟
3. سجّل النتيجة في `continuity-log/<التاريخ>-<اللقطة>.md`: الأداة، النموذج، الإعدادات، المدة، العيوب، القرار (معتمد/إعادة/مرفوض).
4. المعتمد فقط ينتقل إلى `video/approved/`.
