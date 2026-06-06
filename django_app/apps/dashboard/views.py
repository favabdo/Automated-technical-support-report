from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from db_connection import get_connection, is_manager_level, get_role
from visitor_data import FAKE_STATS
import calendar
from datetime import date


@login_required
def home(request):
    date_from = request.GET.get('from', '')
    date_to   = request.GET.get('to', '')

    # Visitor → بيانات وهمية
    if get_role(request.user) == 'visitor':
        return render(request, 'dashboard/home.html', {
            **FAKE_STATS,
            'is_manager': True,
            'date_from':  date_from,
            'date_to':    date_to,
        })

    conn = get_connection()
    cursor = conn.cursor(as_dict=True)

    where = "WHERE 1=1"
    if not is_manager_level(request.user):
        where += f" AND agent_name = '{request.user.first_name or request.user.username}'"
    if date_from:
        where += f" AND resolved_date >= {date_from.replace('-', '')}"
    if date_to:
        where += f" AND resolved_date <= {date_to.replace('-', '')}"

    cursor.execute(f"SELECT COUNT(*) AS total FROM Customer_service_reports_by_A {where}")
    total_reports = cursor.fetchone()['total']

    cursor.execute(f"SELECT COUNT(*) AS total FROM Customer_service_reports_by_A {where} AND classification LIKE N'تم%'")
    total_resolved = cursor.fetchone()['total']

    cursor.execute(f"SELECT COUNT(*) AS total FROM Customer_service_reports_by_A {where} AND classification LIKE N'لم يتم%'")
    total_unresolved = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total FROM customer_detail_by_A")
    total_customers = cursor.fetchone()['total']

    cursor.execute(f"""
        SELECT TOP 5 agent_name, COUNT(*) AS total
        FROM Customer_service_reports_by_A {where}
        GROUP BY agent_name ORDER BY total DESC
    """)
    active_agents = cursor.fetchall()

    cursor.execute(f"""
        SELECT TOP 5 agent_name, COUNT(DISTINCT customer_id) AS total
        FROM Customer_service_reports_by_A {where}
        GROUP BY agent_name ORDER BY total DESC
    """)
    agents_customers = cursor.fetchall()

    cursor.execute(f"""
        SELECT TOP 5 classification, COUNT(*) AS total
        FROM Customer_service_reports_by_A {where}
        GROUP BY classification ORDER BY total DESC
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
        'is_manager':       is_manager_level(request.user),
        'date_from':        date_from,
        'date_to':          date_to,
    })