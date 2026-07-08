from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from models import db
from models.customer import Customer
from models.payment import Payment

payments_bp = Blueprint("payments", __name__)


@payments_bp.route("/payments")
def list_payments():
    payments = Payment.query.order_by(Payment.payment_date.desc()).all()
    return render_template("payments/list.html", payments=payments)


@payments_bp.route("/payments/new", methods=["GET", "POST"])
def create_payment():
    customers = Customer.query.order_by(Customer.name).all()
    if request.method == "POST":
        payment = Payment(
            customer_id=int(request.form.get("customer_id")),
            payment_date=datetime.strptime(request.form.get("payment_date"), "%Y-%m-%d").date(),
            amount=float(request.form.get("amount", 0) or 0),
            payment_mode=request.form.get("payment_mode", "Cash"),
            notes=request.form.get("notes", ""),
        )
        db.session.add(payment)
        db.session.commit()
        flash("Payment recorded successfully.", "success")
        return redirect(url_for("payments.list_payments"))
    return render_template("payments/form.html", customers=customers, payment=None)


@payments_bp.route("/payments/<int:payment_id>/edit", methods=["GET", "POST"])
def edit_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    customers = Customer.query.order_by(Customer.name).all()
    if request.method == "POST":
        payment.customer_id = int(request.form.get("customer_id"))
        payment.payment_date = datetime.strptime(request.form.get("payment_date"), "%Y-%m-%d").date()
        payment.amount = float(request.form.get("amount", 0) or 0)
        payment.payment_mode = request.form.get("payment_mode", "Cash")
        payment.notes = request.form.get("notes", "")
        db.session.commit()
        flash("Payment updated successfully.", "success")
        return redirect(url_for("payments.list_payments"))
    return render_template("payments/form.html", customers=customers, payment=payment)


@payments_bp.route("/payments/<int:payment_id>/delete", methods=["POST"])
def delete_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    db.session.delete(payment)
    db.session.commit()
    flash("Payment deleted successfully.", "success")
    return redirect(url_for("payments.list_payments"))
