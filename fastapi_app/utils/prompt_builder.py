def build_prompt(chat_history, existing_categories: list):
    cats_str = "\n".join(f"- {c}" for c in existing_categories) if existing_categories else "لا يوجد تصنيفات سابقة بعد"
    return f"""
You are a technical support assistant for monitoring the quality of solutions and the efficiency of the agent.
Overlook spelling mistakes. You are receiving a chat from the ChatWoot platform.

You MUST respond in EXACTLY this format — no extra text before or after:

النوع: resolved
المشكلة: وصف مختصر ودقيق للمشكلة
التصنيف: تصنيف المشكلة
الملخص: ملخص تفصيلي وشامل للمحادثة كاملة

Rules:
- النوع: اكتب "resolved" إذا تم حل المشكلة، أو "not_resolved" إذا لم تُحل أو العميل لا يرد أو لم تُعرَّف مشكلة.
- المشكلة: وصف دقيق للمشكلة فقط (لا رسائل ترحيب، لا إسناد محادثة). كن موجزاً دون إغفال التفاصيل المهمة.
- التصنيف: VERY IMPORTANT — راجع قائمة التصنيفات الموجودة أدناه. إذا كانت المشكلة تندرج تحت أي منها أو تشبهها، استخدم نفس التصنيف حرفياً. فقط إذا كانت مختلفة تماماً، اكتب تصنيفاً جديداً قصيراً.
- الملخص: اكتب ملخصاً تفصيلياً وشاملاً يتضمن: طبيعة المشكلة، الخطوات المتخذة، ردود الفعل، والنتيجة النهائية.
- اكتب دائماً بالعربية وتاكد انها عربيه سليمه مئه بالمئه
- لا تضف أي سطر إضافي خارج الأسطر الأربعة أعلاه.

التصنيفات الموجودة حالياً:
{cats_str}

Chat:
{chat_history}
"""
