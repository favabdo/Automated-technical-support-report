from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from db_connection import get_connection
from db_connection import is_manager_level


@login_required
def agents_list(request):
    conn = get_connection()
    cursor = conn.cursor(as_dict=True)

    date_from = request.GET.get('from', '')
    date_to   = request.GET.get('to', '')
    search    = request.GET.get('search', '')

    where = "WHERE 1=1"
    if not is_manager_level(request.user):
        where += f" AND agent_name = '{request.user.first_name or request.user.username}'"
    if search:
        where += f" AND agent_name LIKE N'%{search}%'"
    if date_from:
        where += f" AND resolved_date >= {date_from.replace('-', '')}"
    if date_to:
        where += f" AND resolved_date <= {date_to.replace('-', '')}"

    cursor.execute(f"""
        SELECT
            agent_id,
            agent_name,
            COUNT(*) AS total,
            SUM(CASE WHEN classification LIKE N'تم%' THEN 1 ELSE 0 END) AS resolved,
            SUM(CASE WHEN classification LIKE N'لم يتم%' THEN 1 ELSE 0 END) AS unresolved
        FROM Customer_service_reports_by_A {where}
        GROUP BY agent_id, agent_name
        ORDER BY total DESC
    """)
    agents = cursor.fetchall()
    conn.close()

    return render(request, 'agents/index.html', {
        'agents':     agents,
        'is_manager': is_manager_level(request.user),
        'search':     search,
        'date_from':  date_from,
        'date_to':    date_to,
    })


@login_required
def agent_detail(request, agent_id):
    conn = get_connection()
    cursor = conn.cursor(as_dict=True)

    date_from = request.GET.get('from', '')
    date_to   = request.GET.get('to', '')

    where = f"WHERE agent_id = {agent_id}"
    if date_from:
        where += f" AND resolved_date >= {date_from.replace('-', '')}"
    if date_to:
        where += f" AND resolved_date <= {date_to.replace('-', '')}"

    cursor.execute(f"SELECT TOP 1 agent_name FROM Customer_service_reports_by_A WHERE agent_id = {agent_id}")
    agent = cursor.fetchone()

    cursor.execute(f"""
        SELECT * FROM Customer_service_reports_by_A {where}
        ORDER BY created_at DESC
    """)
    reports = cursor.fetchall()
    conn.close()

    return render(request, 'agents/detail.html', {
        'agent':      agent,
        'reports':    reports,
        'is_manager': is_manager_level(request.user),
        'date_from':  date_from,
        'date_to':    date_to,
    })