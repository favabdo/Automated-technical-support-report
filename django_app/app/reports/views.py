from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from db_connection import get_connection
import calendar
from datetime import date


def is_manager(user):
    return user.groups.filter(name='manager').exists() or user.is_superuser


# ---------------- ALL REPORTS ----------------
@login_required
def reports_list(request):
    conn = get_connection()
    cursor = conn.cursor(as_dict=True)

    date_from      = request.GET.get('from', '')
    date_to        = request.GET.get('to', '')
    agent_filter   = request.GET.get('agent', '')
    class_filter   = request.GET.get('classification', '')

    where = "WHERE 1=1"
    if not is_manager(request.user):
        where += f" AND agent_name = '{request.user.get_full_name() or request.user.username}'"
    if agent_filter:
        where += f" AND agent_name = '{agent_filter}'"
    if date_from:
        where += f" AND resolved_date >= {date_from.replace('-', '')}"
    if date_to:
        where += f" AND resolved_date <= {date_to.replace('-', '')}"
    if class_filter:
        where += f" AND classification LIKE N'%{class_filter}%'"

    cursor.execute(f"SELECT * FROM Customer_service_reports_by_A {where} ORDER BY created_at DESC")
    data = cursor.fetchall()

    agents = []
    if is_manager(request.user):
        cursor.execute("SELECT DISTINCT agent_name FROM Customer_service_reports_by_A")
        agents = [r['agent_name'] for r in cursor.fetchall()]

    conn.close()

    return render(request, 'reports/list.html', {
        'data': data, 'agents': agents,
        'is_manager': is_manager(request.user),
        'filters': {'agent': agent_filter, 'from': date_from, 'to': date_to, 'classification': class_filter},
    })


# ---------------- AGENTS LIST ----------------
@login_required
def agents_list(request):
    conn = get_connection()
    cursor = conn.cursor(as_dict=True)

    date_from = request.GET.get('from', '')
    date_to   = request.GET.get('to', '')
    search    = request.GET.get('search', '')

    where = "WHERE 1=1"
    if date_from:
        where += f" AND resolved_date >= {date_from.replace('-', '')}"
    if date_to:
        where += f" AND resolved_date <= {date_to.replace('-', '')}"
    if search:
        where += f" AND agent_name LIKE N'%{search}%'"

    if not is_manager(request.user):
        where += f" AND agent_name = '{request.user.get_full_name() or request.user.username}'"

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
        'agents': agents,
        'is_manager': is_manager(request.user),
        'search': search,
        'date_from': date_from,
        'date_to': date_to,
    })


# ---------------- AGENT DETAIL ----------------
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

    cursor.execute(f"""
        SELECT * FROM Customer_service_reports_by_A {where}
        ORDER BY created_at DESC
    """)
    reports = cursor.fetchall()

    cursor.execute(f"SELECT TOP 1 agent_name FROM Customer_service_reports_by_A WHERE agent_id = {agent_id}")
    agent = cursor.fetchone()

    conn.close()

    return render(request, 'agents/detail.html', {
        'reports': reports,
        'agent': agent,
        'is_manager': is_manager(request.user),
        'date_from': date_from,
        'date_to': date_to,
    })


# ---------------- CUSTOMERS LIST ----------------
@login_required
def customers_list(request):
    if not is_manager(request.user):
        return redirect('home')

    conn = get_connection()
    cursor = conn.cursor(as_dict=True)

    search = request.GET.get('search', '')

    if search:
        cursor.execute(f"""
            SELECT c.*,
                   COUNT(r.id) AS total_reports,
                   SUM(CASE WHEN r.classification LIKE N'تم%' THEN 1 ELSE 0 END) AS resolved,
                   SUM(CASE WHEN r.classification LIKE N'لم يتم%' THEN 1 ELSE 0 END) AS unresolved
            FROM customer_detail_by_A c
            LEFT JOIN Customer_service_reports_by_A r ON c.customer_id = r.customer_id
            WHERE c.customer_name LIKE N'%{search}%' OR c.customer_phone LIKE N'%{search}%'
            GROUP BY c.customer_id, c.customer_name, c.customer_phone
            ORDER BY total_reports DESC
        """)
    else:
        cursor.execute("""
            SELECT c.*,
                   COUNT(r.id) AS total_reports,
                   SUM(CASE WHEN r.classification LIKE N'تم%' THEN 1 ELSE 0 END) AS resolved,
                   SUM(CASE WHEN r.classification LIKE N'لم يتم%' THEN 1 ELSE 0 END) AS unresolved
            FROM customer_detail_by_A c
            LEFT JOIN Customer_service_reports_by_A r ON c.customer_id = r.customer_id
            GROUP BY c.customer_id, c.customer_name, c.customer_phone
            ORDER BY total_reports DESC
        """)

    customers = cursor.fetchall()
    conn.close()

    return render(request, 'customers/index.html', {
        'customers': customers,
        'search': search,
        'is_manager': True,
    })


# ---------------- CUSTOMER DETAIL ----------------
@login_required
def customer_detail(request, customer_id):
    if not is_manager(request.user):
        return redirect('home')

    conn = get_connection()
    cursor = conn.cursor(as_dict=True)

    cursor.execute(f"SELECT * FROM customer_detail_by_A WHERE customer_id = {customer_id}")
    customer = cursor.fetchone()

    cursor.execute(f"""
        SELECT * FROM Customer_service_reports_by_A
        WHERE customer_id = {customer_id}
        ORDER BY created_at DESC
    """)
    reports = cursor.fetchall()
    conn.close()

    return render(request, 'customers/detail.html', {
        'customer': customer,
        'reports': reports,
        'is_manager': True,
    })


# ---------------- MONTHLY ----------------
@login_required
def monthly(request):
    conn = get_connection()
    cursor = conn.cursor(as_dict=True)

    year  = int(request.GET.get('year',  date.today().year))
    month = int(request.GET.get('month', date.today().month))

    month_start = int(f"{year}{month:02d}01")
    month_end   = int(f"{year}{month:02d}{calendar.monthrange(year, month)[1]}")

    where = f"WHERE resolved_date BETWEEN {month_start} AND {month_end}"
    if not is_manager(request.user):
        where += f" AND agent_name = '{request.user.get_full_name() or request.user.username}'"

    cursor.execute(f"""
        SELECT agent_name,
               COUNT(*) AS total,
               SUM(CASE WHEN classification LIKE N'تم%' THEN 1 ELSE 0 END) AS resolved,
               SUM(CASE WHEN classification LIKE N'لم يتم%' THEN 1 ELSE 0 END) AS unresolved
        FROM Customer_service_reports_by_A {where}
        GROUP BY agent_name
        ORDER BY total DESC
    """)
    data = cursor.fetchall()
    conn.close()

    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years  = list(range(date.today().year - 2, date.today().year + 1))

    return render(request, 'reports/monthly.html', {
        'data': data,
        'months': months,
        'years': years,
        'selected_month': month,
        'selected_year': year,
        'is_manager': is_manager(request.user),
    })
