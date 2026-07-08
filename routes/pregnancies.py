from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from models import db
from models.cattle import Cattle
from models.pregnancy import Pregnancy

pregnancies_bp = Blueprint("pregnancies", __name__)


@pregnancies_bp.route("/pregnancies")
def list_pregnancies():
    pregnancies = Pregnancy.query.order_by(Pregnancy.created_at.desc()).all()
    return render_template("pregnancies/list.html", pregnancies=pregnancies)


@pregnancies_bp.route("/pregnancies/new", methods=["GET", "POST"])
def create_pregnancy():
    cattle = Cattle.query.order_by(Cattle.name).all()
    if request.method == "POST":
        pregnancy = Pregnancy(
            cattle_id=int(request.form.get("cattle_id")),
            insemination_date=datetime.strptime(request.form.get("insemination_date"), "%Y-%m-%d").date(),
        )
        pregnancy.calculate_expected_calving_date()
        db.session.add(pregnancy)
        db.session.commit()
        flash("Pregnancy record created successfully.", "success")
        return redirect(url_for("pregnancies.list_pregnancies"))
    return render_template("pregnancies/form.html", cattle=cattle, pregnancy=None)


@pregnancies_bp.route("/pregnancies/<int:pregnancy_id>/edit", methods=["GET", "POST"])
def edit_pregnancy(pregnancy_id):
    pregnancy = Pregnancy.query.get_or_404(pregnancy_id)
    cattle = Cattle.query.order_by(Cattle.name).all()
    if request.method == "POST":
        pregnancy.cattle_id = int(request.form.get("cattle_id"))
        pregnancy.insemination_date = datetime.strptime(request.form.get("insemination_date"), "%Y-%m-%d").date()
        pregnancy.calculate_expected_calving_date()
        db.session.commit()
        flash("Pregnancy record updated successfully.", "success")
        return redirect(url_for("pregnancies.list_pregnancies"))
    return render_template("pregnancies/form.html", cattle=cattle, pregnancy=pregnancy)


@pregnancies_bp.route("/pregnancies/<int:pregnancy_id>/delete", methods=["POST"])
def delete_pregnancy(pregnancy_id):
    pregnancy = Pregnancy.query.get_or_404(pregnancy_id)
    db.session.delete(pregnancy)
    db.session.commit()
    flash("Pregnancy record deleted successfully.", "success")
    return redirect(url_for("pregnancies.list_pregnancies"))
