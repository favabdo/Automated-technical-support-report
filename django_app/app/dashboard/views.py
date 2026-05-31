from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from db_connection import get_connection
from datetime import date


def is_manager(user):
    return user.groups.filter(name='manager').exists() or user.is_superuser


@login_required
def home(request):
    conn = get_connection()
    cursor = conn.cursor(as_dict=True)

    # فلتر التاريخ من الـ Navbar
    date_from = request.GET.get('from', '')
    date_to   = request.GET.get('to', '')

    where = "WHERE 1=1"
    if date_from:
        where += f" AND resolved_date >= {date_from.replace('-', '')}"
    if date_to:
        where += f" AND resolved_date <= {date_to.replace('-', '')}"

    # لو مش مدير يشوف بتاعته بس
    if not is_manager(request.user):
        where += f" AND agent_name = '{request.user.get_full_name() or request.user.username}'"

    # ---------------- إحصائيات عامة ----------------
    cursor.execute(f"SELECT COUNT(*) AS total FROM Customer_service_reports_by_A {where}")
    total_reports = cursor.fetchone()['total']

    cursor.execute(f"""
        SELECT COUNT(*) AS total FROM Customer_service_reports_by_A
        {where} AND classification LIKE N'تم%'
    """)
    total_resolved = cursor.fetchone()['total']

    cursor.execute(f"""
        SELECT COUNT(*) AS total FROM Customer_service_reports_by_A
        {where} AND classification LIKE N'لم يتم%'
    """)
    total_unresolved = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total FROM customer_detail_by_A")
    total_customers = cursor.fetchone()['total']

    # ---------------- Most Active Agents ----------------
    cursor.execute(f"""
        SELECT TOP 5 agent_name, COUNT(*) AS total
        FROM Customer_service_reports_by_A {where}
        GROUP BY agent_name
        ORDER BY total DESC
    """)
    active_agents = cursor.fetchall()

    # ---------------- Most Customers per Agent ----------------
    cursor.execute(f"""
        SELECT TOP 5 agent_name, COUNT(DISTINCT customer_id) AS total
        FROM Customer_service_reports_by_A {where}
        GROUP BY agent_name
        ORDER BY total DESC
    """)
    agents_customers = cursor.fetchall()

    # ---------------- Most Common Problems ----------------
    cursor.execute(f"""
        SELECT TOP 5 classification, COUNT(*) AS total
        FROM Customer_service_reports_by_A {where}
        GROUP BY classification
        ORDER BY total DESC
    """)
    common_problems = cursor.fetchall()

    conn.close()

    return render(request, 'dashboard/home.html', {
        'total_reports':    total_reports,
        'total_resolved':   total_resolved,
        'total_unresolved': total_unresolved,
        'total_customers':  total_customers,
        'active_agents':    active_agents,
        'agents_customers': agents_customers,
        'common_problems':  common_problems,
        'is_manager':       is_manager(request.user),
        'date_from':        date_from,
        'date_to':          date_to,
    })