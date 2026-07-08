from datetime import datetime, timezone

from flask import Blueprint, Response, current_app, jsonify, render_template, send_from_directory, url_for

from models.cattle import Cattle
from models.customer import Customer
from models.expense import Expense
from models.milk_entry import MilkEntry
from utils.pwa import collect_static_asset_urls

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    customers = Customer.query.filter_by(active=True).count()
    today = datetime.now(timezone.utc).date()
    today_entries = MilkEntry.query.filter_by(entry_date=today).order_by(MilkEntry.created_at.desc()).all()
    today_income = round(sum(entry.amount for entry in today_entries), 2)
    today_litres = round(sum(entry.total_litres for entry in today_entries), 2)
    monthly_entries = MilkEntry.query.filter(
        MilkEntry.entry_date >= today.replace(day=1)
    ).all()
    monthly_income = round(sum(entry.amount for entry in monthly_entries), 2)
    monthly_litres = round(sum(entry.total_litres for entry in monthly_entries), 2)
    monthly_expenses = Expense.query.filter(
        Expense.expense_date >= today.replace(day=1)
    ).all()
    monthly_expense_total = round(sum(item.amount for item in monthly_expenses), 2)
    profit = round(monthly_income - monthly_expense_total, 2)
    cattle_count = Cattle.query.count()

    pending_balances = sorted(
        [customer for customer in Customer.query.all() if customer.outstanding_balance() > 0],
        key=lambda customer: customer.outstanding_balance(),
        reverse=True,
    )
    recent_entries = MilkEntry.query.order_by(
        MilkEntry.entry_date.desc(), MilkEntry.created_at.desc()
    ).limit(5).all()

    return render_template(
        "dashboard.html",
        customers=customers,
        cattle_count=cattle_count,
        today_income=today_income,
        today_litres=today_litres,
        monthly_income=monthly_income,
        monthly_litres=monthly_litres,
        monthly_expenses=monthly_expense_total,
        profit=profit,
        pending_balances=pending_balances[:5],
        recent_entries=recent_entries,
    )


@main_bp.route("/health")
def health():
    return {"status": "ok"}


@main_bp.route("/offline")
def offline():
    return render_template("offline.html")


@main_bp.route("/manifest.json")
def manifest_json():
    manifest_data = {
        "name": "MilkMaster",
        "short_name": "MilkMaster",
        "description": "Dairy management for milk entries, payments, reports, and offline access.",
        "id": "/",
        "start_url": url_for("main.index"),
        "scope": "/",
        "display": "standalone",
        "background_color": "#f7fcf9",
        "theme_color": "#1f7a4d",
        "icons": [
            {
                "src": url_for("static", filename="icons/icon.svg"),
                "sizes": "any",
                "type": "image/svg+xml",
                "purpose": "any maskable",
            },
            {
                "src": url_for("static", filename="icons/icon-192.svg"),
                "sizes": "192x192",
                "type": "image/svg+xml",
                "purpose": "any",
            },
            {
                "src": url_for("static", filename="icons/icon-512.svg"),
                "sizes": "512x512",
                "type": "image/svg+xml",
                "purpose": "any",
            },
            {
                "src": url_for("static", filename="icons/icon-maskable.svg"),
                "sizes": "512x512",
                "type": "image/svg+xml",
                "purpose": "maskable",
            }
        ],
    }
    return jsonify(manifest_data)


@main_bp.route("/manifest.webmanifest")
def manifest_webmanifest():
    return manifest_json()


@main_bp.route("/pwa-assets.json")
def pwa_assets():
    asset_urls = collect_static_asset_urls(current_app.static_folder)
    shell_urls = [url_for("main.index"), url_for("main.offline"), url_for("main.manifest_json")]
    return jsonify({"shell": shell_urls, "assets": asset_urls})


@main_bp.route("/service-worker.js")
def service_worker():
    return send_from_directory(current_app.static_folder, "js/service-worker.js", mimetype="application/javascript")
