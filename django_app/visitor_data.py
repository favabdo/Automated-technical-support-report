# بيانات وهمية للـ Visitor
# يتحط في django_app/visitor_data.py

FAKE_AGENTS = [
    {'agent_id': 1, 'agent_name': 'أحمد محمد', 'total': 45, 'resolved': 38, 'unresolved': 7},
    {'agent_id': 2, 'agent_name': 'سارة علي',  'total': 38, 'resolved': 30, 'unresolved': 8},
    {'agent_id': 3, 'agent_name': 'محمد خالد', 'total': 32, 'resolved': 25, 'unresolved': 7},
    {'agent_id': 4, 'agent_name': 'نورا حسن',  'total': 27, 'resolved': 22, 'unresolved': 5},
    {'agent_id': 5, 'agent_name': 'عمر يوسف',  'total': 20, 'resolved': 15, 'unresolved': 5},
]

FAKE_CUSTOMERS = [
    {'customer_id': 101, 'customer_name': 'شركة النيل',       'customer_phone': '01001234567', 'total_reports': 12, 'resolved': 10, 'unresolved': 2},
    {'customer_id': 102, 'customer_name': 'مؤسسة الأهرام',    'customer_phone': '01101234567', 'total_reports': 9,  'resolved': 7,  'unresolved': 2},
    {'customer_id': 103, 'customer_name': 'مجموعة الفجر',     'customer_phone': '01201234567', 'total_reports': 7,  'resolved': 6,  'unresolved': 1},
    {'customer_id': 104, 'customer_name': 'شركة الوادي',      'customer_phone': '01501234567', 'total_reports': 5,  'resolved': 4,  'unresolved': 1},
    {'customer_id': 105, 'customer_name': 'مؤسسة الدلتا',     'customer_phone': '01221234567', 'total_reports': 4,  'resolved': 3,  'unresolved': 1},
    {'customer_id': 106, 'customer_name': 'شركة سيناء',       'customer_phone': '01281234567', 'total_reports': 3,  'resolved': 2,  'unresolved': 1},
]

FAKE_REPORTS = [
    {'id': 1,  'customer_name': 'شركة النيل',    'customer_phone': '01001234567', 'agent_name': 'أحمد محمد', 'classification': 'تم حل مشكلة: انقطاع الإنترنت',      'summary': 'تم إعادة تشغيل الراوتر وحل مشكلة الاتصال', 'resolved_date': 20260501, 'resolved_time': '10:30 AM'},
    {'id': 2,  'customer_name': 'مؤسسة الأهرام', 'customer_phone': '01101234567', 'agent_name': 'سارة علي',  'classification': 'تم حل مشكلة: بطء الشبكة',           'summary': 'تم تحديث إعدادات الشبكة وتحسين السرعة',   'resolved_date': 20260502, 'resolved_time': '11:15 AM'},
    {'id': 3,  'customer_name': 'مجموعة الفجر',  'customer_phone': '01201234567', 'agent_name': 'محمد خالد', 'classification': 'لم يتم حل مشكلة: عطل في الجهاز',    'summary': 'الجهاز يحتاج صيانة متخصصة',               'resolved_date': 20260503, 'resolved_time': '09:00 AM'},
    {'id': 4,  'customer_name': 'شركة الوادي',   'customer_phone': '01501234567', 'agent_name': 'نورا حسن',  'classification': 'تم حل مشكلة: انقطاع الكهرباء',      'summary': 'تم التواصل مع الفريق الفني وحل المشكلة',  'resolved_date': 20260504, 'resolved_time': '02:45 PM'},
    {'id': 5,  'customer_name': 'مؤسسة الدلتا',  'customer_phone': '01221234567', 'agent_name': 'عمر يوسف',  'classification': 'سيتم التواصل مع العميل قريباً',      'summary': 'في انتظار رد الفريق التقني',               'resolved_date': 20260505, 'resolved_time': '04:00 PM'},
    {'id': 6,  'customer_name': 'شركة النيل',    'customer_phone': '01001234567', 'agent_name': 'أحمد محمد', 'classification': 'تم حل مشكلة: مشكلة في الطابعة',     'summary': 'تم تثبيت درايفر الطابعة وحل المشكلة',     'resolved_date': 20260506, 'resolved_time': '01:30 PM'},
    {'id': 7,  'customer_name': 'شركة سيناء',    'customer_phone': '01281234567', 'agent_name': 'سارة علي',  'classification': 'تم حل مشكلة: فيروس في الجهاز',      'summary': 'تم تنظيف الجهاز وإزالة الفيروسات',        'resolved_date': 20260507, 'resolved_time': '03:15 PM'},
    {'id': 8,  'customer_name': 'مؤسسة الأهرام', 'customer_phone': '01101234567', 'agent_name': 'محمد خالد', 'classification': 'لم يتم تعريف مشكلة',                'summary': 'المحادثة أغلقت دون وجود محادثة فعلية',     'resolved_date': 20260508, 'resolved_time': '10:00 AM'},
    {'id': 9,  'customer_name': 'مجموعة الفجر',  'customer_phone': '01201234567', 'agent_name': 'نورا حسن',  'classification': 'تم حل مشكلة: مشكلة في الإيميل',     'summary': 'تم إعادة ضبط إعدادات الإيميل',             'resolved_date': 20260509, 'resolved_time': '11:45 AM'},
    {'id': 10, 'customer_name': 'شركة الوادي',   'customer_phone': '01501234567', 'agent_name': 'عمر يوسف',  'classification': 'تم حل مشكلة: نسيان كلمة المرور',    'summary': 'تم إعادة تعيين كلمة المرور للعميل',        'resolved_date': 20260510, 'resolved_time': '09:30 AM'},
]

FAKE_AGENT_REPORTS = {
    1: [r for r in FAKE_REPORTS if r['agent_name'] == 'أحمد محمد'],
    2: [r for r in FAKE_REPORTS if r['agent_name'] == 'سارة علي'],
    3: [r for r in FAKE_REPORTS if r['agent_name'] == 'محمد خالد'],
    4: [r for r in FAKE_REPORTS if r['agent_name'] == 'نورا حسن'],
    5: [r for r in FAKE_REPORTS if r['agent_name'] == 'عمر يوسف'],
}

FAKE_CUSTOMER_REPORTS = {
    101: [r for r in FAKE_REPORTS if r['customer_name'] == 'شركة النيل'],
    102: [r for r in FAKE_REPORTS if r['customer_name'] == 'مؤسسة الأهرام'],
    103: [r for r in FAKE_REPORTS if r['customer_name'] == 'مجموعة الفجر'],
    104: [r for r in FAKE_REPORTS if r['customer_name'] == 'شركة الوادي'],
    105: [r for r in FAKE_REPORTS if r['customer_name'] == 'مؤسسة الدلتا'],
    106: [r for r in FAKE_REPORTS if r['customer_name'] == 'شركة سيناء'],
}

FAKE_STATS = {
    'total_reports':    162,
    'total_resolved':   130,
    'total_unresolved': 32,
    'total_customers':  6,
    'active_agents':    FAKE_AGENTS[:5],
    'agents_customers': [
        {'agent_name': 'أحمد محمد', 'total': 18},
        {'agent_name': 'سارة علي',  'total': 15},
        {'agent_name': 'محمد خالد', 'total': 12},
        {'agent_name': 'نورا حسن',  'total': 10},
        {'agent_name': 'عمر يوسف',  'total': 8},
    ],
    'common_problems': [
        {'classification': 'انقطاع الإنترنت',  'total': 45},
        {'classification': 'بطء الشبكة',        'total': 32},
        {'classification': 'عطل في الجهاز',     'total': 28},
        {'classification': 'مشكلة في الإيميل',  'total': 20},
        {'classification': 'نسيان كلمة المرور', 'total': 15},
    ],
}

FAKE_MONTHLY = [
    {'agent_name': 'أحمد محمد', 'total': 45, 'resolved': 38, 'unresolved': 7},
    {'agent_name': 'سارة علي',  'total': 38, 'resolved': 30, 'unresolved': 8},
    {'agent_name': 'محمد خالد', 'total': 32, 'resolved': 25, 'unresolved': 7},
    {'agent_name': 'نورا حسن',  'total': 27, 'resolved': 22, 'unresolved': 5},
    {'agent_name': 'عمر يوسف',  'total': 20, 'resolved': 15, 'unresolved': 5},
]
