from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from db_connection import get_connection
from db_connection import is_manager_level


@login_required
def customers_list(request):
    if not is_manager_level(request.user):
        return redirect('home')

    conn = get_connection()
    cursor = conn.cursor(as_dict=True)

    search = request.GET.get('search', '')

    query = """
        SELECT c.*,
               COUNT(r.id) AS total_reports,
               SUM(CASE WHEN r.classification LIKE N'تم%' THEN 1 ELSE 0 END) AS resolved,
               SUM(CASE WHEN r.classification LIKE N'لم يتم%' THEN 1 ELSE 0 END) AS unresolved
        FROM customer_detail_by_A c
        LEFT JOIN Customer_service_reports_by_A r ON c.customer_id = r.customer_id
    """
    if search:
        query += f" WHERE c.customer_name LIKE N'%{search}%' OR c.customer_phone LIKE N'%{search}%'"

    query += " GROUP BY c.customer_id, c.customer_name, c.customer_phone ORDER BY total_reports DESC"

    cursor.execute(query)
    customers = cursor.fetchall()
    conn.close()

    return render(request, 'customers/index.html', {
        'customers': customers,
        'search':    search,
        'is_manager': True,
    })


@login_required
def customer_detail(request, customer_id):
    if not is_manager_level(request.user):
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
        'reports':  reports,
        'is_manager': True,
    })