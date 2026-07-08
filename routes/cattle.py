from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from models import db
from models.cattle import Cattle

cattle_bp = Blueprint("cattle", __name__)


def parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date() if value else None


@cattle_bp.route("/cattle")
def list_cattle():
    cattle = Cattle.query.order_by(Cattle.created_at.desc()).all()
    return render_template("cattle/list.html", cattle=cattle)


@cattle_bp.route("/cattle/new", methods=["GET", "POST"])
def create_cattle():
    if request.method == "POST":
        cattle = Cattle(
            tag_number=request.form.get("tag_number", "").strip(),
            name=request.form.get("name", "").strip(),
            breed=request.form.get("breed", "").strip(),
            gender=request.form.get("gender", "").strip(),
            date_of_birth=parse_date(request.form.get("date_of_birth")),
            purchase_date=parse_date(request.form.get("purchase_date")),
            purchase_cost=float(request.form.get("purchase_cost", 0) or 0),
            current_status=request.form.get("current_status", "Milking"),
        )
        db.session.add(cattle)
        db.session.commit()
        flash("Cattle added successfully.", "success")
        return redirect(url_for("cattle.list_cattle"))
    return render_template("cattle/form.html", cattle=None)


@cattle_bp.route("/cattle/<int:cattle_id>/edit", methods=["GET", "POST"])
def edit_cattle(cattle_id):
    cattle = Cattle.query.get_or_404(cattle_id)
    if request.method == "POST":
        cattle.tag_number = request.form.get("tag_number", "").strip()
        cattle.name = request.form.get("name", "").strip()
        cattle.breed = request.form.get("breed", "").strip()
        cattle.gender = request.form.get("gender", "").strip()
        cattle.date_of_birth = parse_date(request.form.get("date_of_birth"))
        cattle.purchase_date = parse_date(request.form.get("purchase_date"))
        cattle.purchase_cost = float(request.form.get("purchase_cost", 0) or 0)
        cattle.current_status = request.form.get("current_status", "Milking")
        db.session.commit()
        flash("Cattle updated successfully.", "success")
        return redirect(url_for("cattle.list_cattle"))
    return render_template("cattle/form.html", cattle=cattle)


@cattle_bp.route("/cattle/<int:cattle_id>/delete", methods=["POST"])
def delete_cattle(cattle_id):
    cattle = Cattle.query.get_or_404(cattle_id)
    db.session.delete(cattle)
    db.session.commit()
    flash("Cattle deleted successfully.", "success")
    return redirect(url_for("cattle.list_cattle"))
