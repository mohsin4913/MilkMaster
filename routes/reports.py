from io import BytesIO
from datetime import datetime, timedelta

from flask import Blueprint, Response, render_template, request, url_for
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

from models.customer import Customer
from models.expense import Expense
from models.milk_entry import MilkEntry
from models.payment import Payment

reports_bp = Blueprint("reports", __name__)


def _resolve_report_window(period):
    today = datetime.utcnow().date()

    if period == "daily":
        return "Daily Report", today, today
    if period == "weekly":
        start_date = today - timedelta(days=today.weekday())
        return "Weekly Report", start_date, today
    if period == "overall":
        return "Overall Report", None, today

    start_date = today.replace(day=1)
    return "Monthly Report", start_date, today


def _fetch_report_data(start_date):
    milk_query = MilkEntry.query.order_by(MilkEntry.entry_date.desc())
    expense_query = Expense.query.order_by(Expense.expense_date.desc())
    payment_query = Payment.query.order_by(Payment.payment_date.desc())

    if start_date is not None:
        milk_query = milk_query.filter(MilkEntry.entry_date >= start_date)
        expense_query = expense_query.filter(Expense.expense_date >= start_date)
        payment_query = payment_query.filter(Payment.payment_date >= start_date)

    milk_entries = milk_query.all()
    expenses = expense_query.all()
    payments = payment_query.all()
    customers = Customer.query.order_by(Customer.name).all()
    return milk_entries, expenses, payments, customers


def _build_report_pdf(title, period_label, start_date, end_date, milk_entries, expenses, payments, customers):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"MilkMaster {title}", styles["Title"]))
    story.append(Paragraph(f"Period: {period_label}", styles["BodyText"]))
    story.append(Paragraph(f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles["BodyText"]))
    story.append(Spacer(1, 12))

    milk_total = round(sum(entry.amount for entry in milk_entries), 2)
    litres_total = round(sum(entry.total_litres for entry in milk_entries), 2)
    expense_total = round(sum(expense.amount for expense in expenses), 2)
    payment_total = round(sum(payment.amount for payment in payments), 2)
    outstanding_total = round(sum(customer.outstanding_balance() for customer in customers), 2)

    summary_data = [
        ["Milk income", f"{milk_total:.2f}"],
        ["Milk litres", f"{litres_total:.2f}"],
        ["Payments received", f"{payment_total:.2f}"],
        ["Expenses", f"{expense_total:.2f}"],
        ["Profit", f"{(milk_total - expense_total):.2f}"],
        ["Outstanding", f"{outstanding_total:.2f}"],
    ]
    summary_table = Table(summary_data, colWidths=[180, 120])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f7a4d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.beige]),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Milk Entries", styles["Heading2"]))
    entries_data = [["Date", "Customer", "Litres", "Amount"]]
    for entry in milk_entries[:50]:
        entries_data.append([str(entry.entry_date), entry.customer.name, f"{entry.total_litres:.2f}", f"{entry.amount:.2f}"])
    if len(entries_data) == 1:
        entries_data.append(["No entries found.", "", "", ""])
    entries_table = Table(entries_data, repeatRows=1)
    entries_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f7a4d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.beige]),
            ]
        )
    )
    story.append(entries_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Expenses", styles["Heading2"]))
    expense_data = [["Date", "Category", "Amount"]]
    for expense in expenses[:50]:
        expense_data.append([str(expense.expense_date), expense.category, f"{expense.amount:.2f}"])
    if len(expense_data) == 1:
        expense_data.append(["No expenses found.", "", ""])
    expense_table = Table(expense_data, repeatRows=1)
    expense_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f7a4d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.beige]),
            ]
        )
    )
    story.append(expense_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Payments", styles["Heading2"]))
    payment_data = [["Date", "Customer", "Amount"]]
    for payment in payments[:50]:
        payment_data.append([str(payment.payment_date), payment.customer.name, f"{payment.amount:.2f}"])
    if len(payment_data) == 1:
        payment_data.append(["No payments found.", "", ""])
    payment_table = Table(payment_data, repeatRows=1)
    payment_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f7a4d")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.beige]),
            ]
        )
    )
    story.append(payment_table)

    doc.build(story)
    buffer.seek(0)
    filename = f"{title.lower().replace(' ', '_')}.pdf"
    return Response(buffer.getvalue(), mimetype="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}"})


@reports_bp.route("/reports")
def reports_home():
    period = request.args.get("period", "monthly")
    title, start_date, end_date = _resolve_report_window(period)
    milk_entries, expenses, payments, customers = _fetch_report_data(start_date)

    milk_total = round(sum(entry.amount for entry in milk_entries), 2)
    litres_total = round(sum(entry.total_litres for entry in milk_entries), 2)
    expense_total = round(sum(expense.amount for expense in expenses), 2)
    payment_total = round(sum(payment.amount for payment in payments), 2)
    outstanding_total = round(sum(customer.outstanding_balance() for customer in customers), 2)

    return render_template(
        "reports/index.html",
        period=period,
        title=title,
        start_date=start_date,
        end_date=end_date,
        milk_entries=milk_entries,
        expenses=expenses,
        payments=payments,
        customers=customers,
        milk_total=milk_total,
        litres_total=litres_total,
        expense_total=expense_total,
        payment_total=payment_total,
        profit=round(milk_total - expense_total, 2),
        outstanding_total=outstanding_total,
    )


@reports_bp.route("/reports/download")
def download_report():
    period = request.args.get("period", "overall")
    title, start_date, end_date = _resolve_report_window(period)
    milk_entries, expenses, payments, customers = _fetch_report_data(start_date)
    if start_date is None:
        period_label = "All available records"
    else:
        period_label = f"{start_date} to {end_date}"
    return _build_report_pdf(title, period_label, start_date, end_date, milk_entries, expenses, payments, customers)
