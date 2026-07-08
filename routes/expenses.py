from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from models import db
from models.expense import Expense

expenses_bp = Blueprint("expenses", __name__)


@expenses_bp.route("/expenses")
def list_expenses():
    expenses = Expense.query.order_by(Expense.expense_date.desc()).all()
    return render_template("expenses/list.html", expenses=expenses)


@expenses_bp.route("/expenses/new", methods=["GET", "POST"])
def create_expense():
    if request.method == "POST":
        expense = Expense(
            category=request.form.get("category", "Other"),
            description=request.form.get("description", ""),
            amount=float(request.form.get("amount", 0) or 0),
            expense_date=datetime.strptime(request.form.get("expense_date"), "%Y-%m-%d").date(),
        )
        db.session.add(expense)
        db.session.commit()
        flash("Expense recorded successfully.", "success")
        return redirect(url_for("expenses.list_expenses"))
    return render_template("expenses/form.html", expense=None)


@expenses_bp.route("/expenses/<int:expense_id>/edit", methods=["GET", "POST"])
def edit_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if request.method == "POST":
        expense.category = request.form.get("category", "Other")
        expense.description = request.form.get("description", "")
        expense.amount = float(request.form.get("amount", 0) or 0)
        expense.expense_date = datetime.strptime(request.form.get("expense_date"), "%Y-%m-%d").date()
        db.session.commit()
        flash("Expense updated successfully.", "success")
        return redirect(url_for("expenses.list_expenses"))
    return render_template("expenses/form.html", expense=expense)


@expenses_bp.route("/expenses/<int:expense_id>/delete", methods=["POST"])
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    db.session.delete(expense)
    db.session.commit()
    flash("Expense deleted successfully.", "success")
    return redirect(url_for("expenses.list_expenses"))
