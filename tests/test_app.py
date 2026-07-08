import io
import json
import os
import tempfile
from datetime import datetime, timedelta

import pytest

from app import create_app
from models import db
from models.customer import Customer
from models.expense import Expense
from models.milk_entry import MilkEntry
from models.payment import Payment
from models.cattle import Cattle
from models.pregnancy import Pregnancy


@pytest.fixture()
def app():
    db_fd, db_path = tempfile.mkstemp()
    app = create_app()
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_path}",
    )

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

    os.close(db_fd)
    os.remove(db_path)


@pytest.fixture()
def client(app):
    return app.test_client()


def test_dashboard_loads(client):
    response = client.get("/")
    assert response.status_code == 200


def test_customer_crud_flow(client):
    response = client.post(
        "/customers/new",
        data={
            "name": "Ali",
            "mobile": "03001234567",
            "address": "Karachi",
            "milk_rate": "60",
            "opening_balance": "100",
            "active": "on",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    customer = Customer.query.filter_by(mobile="03001234567").first()
    assert customer is not None
    assert customer.outstanding_balance() == 100.0


def test_duplicate_customer_mobile_is_rejected_gracefully(client):
    first = client.post(
        "/customers/new",
        data={
            "name": "First Customer",
            "mobile": "03001112222",
            "address": "Town",
            "milk_rate": "60",
            "opening_balance": "0",
            "active": "on",
        },
        follow_redirects=True,
    )
    assert first.status_code == 200

    duplicate = client.post(
        "/customers/new",
        data={
            "name": "Second Customer",
            "mobile": "03001112222",
            "address": "Town",
            "milk_rate": "60",
            "opening_balance": "0",
            "active": "on",
        },
        follow_redirects=True,
    )
    assert duplicate.status_code == 200
    assert Customer.query.filter_by(mobile="03001112222").count() == 1


def test_invalid_customer_milk_rate_shows_friendly_error(client):
    response = client.post(
        "/customers/new",
        data={
            "name": "Rate Test",
            "mobile": "03001113333",
            "address": "Town",
            "milk_rate": "abc",
            "opening_balance": "0",
            "active": "on",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Milk rate must be a valid number." in response.data
    assert Customer.query.filter_by(mobile="03001113333").count() == 0


def test_milk_entry_and_payment_flow(client):
    customer = Customer(
        name="Sara",
        mobile="03009999999",
        address="Lahore",
        milk_rate=50,
        opening_balance=0,
        active=True,
    )
    db.session.add(customer)
    db.session.commit()

    response = client.post(
        "/milk-entries/new",
        data={
            "customer_id": customer.id,
            "entry_date": "2026-07-08",
            "morning_litres": "4",
            "evening_litres": "2",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    entry = MilkEntry.query.filter_by(customer_id=customer.id).first()
    assert entry is not None
    assert entry.amount == 300.0

    payment_response = client.post(
        "/payments/new",
        data={
            "customer_id": customer.id,
            "payment_date": "2026-07-09",
            "amount": "100",
            "payment_mode": "Cash",
            "notes": "partial",
        },
        follow_redirects=True,
    )
    assert payment_response.status_code == 200

    payment = Payment.query.filter_by(customer_id=customer.id).first()
    assert payment is not None


def test_morning_only_and_evening_only_entries_are_allowed(client):
    customer = Customer(
        name="Bashir",
        mobile="03007777777",
        address="Peshawar",
        milk_rate=45,
        opening_balance=0,
        active=True,
    )
    db.session.add(customer)
    db.session.commit()

    morning_response = client.post(
        "/milk-entries/new",
        data={
            "customer_id": customer.id,
            "entry_date": "2026-07-10",
            "morning_litres": "4.5",
            "evening_litres": "",
        },
        follow_redirects=True,
    )
    assert morning_response.status_code == 200

    morning_entry = MilkEntry.query.filter_by(customer_id=customer.id, entry_date=datetime.strptime("2026-07-10", "%Y-%m-%d").date()).first()
    assert morning_entry is not None
    assert morning_entry.morning_litres == 4.5
    assert morning_entry.evening_litres == 0.0
    assert morning_entry.total_litres == 4.5
    assert morning_entry.amount == pytest.approx(202.5)

    evening_response = client.post(
        "/milk-entries/new",
        data={
            "customer_id": customer.id,
            "entry_date": "2026-07-11",
            "morning_litres": "",
            "evening_litres": "2.5",
        },
        follow_redirects=True,
    )
    assert evening_response.status_code == 200

    evening_entry = MilkEntry.query.filter_by(customer_id=customer.id, entry_date=datetime.strptime("2026-07-11", "%Y-%m-%d").date()).first()
    assert evening_entry is not None
    assert evening_entry.morning_litres == 0.0
    assert evening_entry.evening_litres == 2.5
    assert evening_entry.total_litres == 2.5
    assert evening_entry.amount == pytest.approx(112.5)


def test_expense_and_cattle_and_pregnancy_flow(client):
    expense_response = client.post(
        "/expenses/new",
        data={
            "category": "Feed",
            "description": "Wheat",
            "amount": "250",
            "expense_date": "2026-07-08",
        },
        follow_redirects=True,
    )
    assert expense_response.status_code == 200

    cattle_response = client.post(
        "/cattle/new",
        data={
            "tag_number": "C001",
            "name": "Moti",
            "breed": "Holstein",
            "gender": "Female",
            "date_of_birth": "2024-01-01",
            "purchase_date": "2024-02-01",
            "purchase_cost": "50000",
            "current_status": "Milking",
        },
        follow_redirects=True,
    )
    assert cattle_response.status_code == 200

    pregnancy_response = client.post(
        "/pregnancies/new",
        data={
            "cattle_id": Cattle.query.first().id,
            "insemination_date": "2026-01-01",
        },
        follow_redirects=True,
    )
    assert pregnancy_response.status_code == 200

    pregnancy = Pregnancy.query.first()
    assert pregnancy is not None


def test_customer_monthly_statement_pdf(client):
    customer = Customer(
        name="Nawaz",
        mobile="03005556666",
        address="Islamabad",
        milk_rate=55,
        opening_balance=50,
        active=True,
    )
    db.session.add(customer)
    db.session.commit()

    entry = MilkEntry(
        customer_id=customer.id,
        entry_date=datetime.strptime("2026-07-05", "%Y-%m-%d").date(),
        morning_litres=3,
        evening_litres=2,
        total_litres=5,
        rate=55,
        amount=275,
    )
    db.session.add(entry)
    db.session.commit()

    response = client.get(f"/customers/{customer.id}/monthly-statement.pdf?month=2026-07")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"


def test_overall_report_pdf_download(client):
    customer = Customer(
        name="Report Customer",
        mobile="03008888888",
        address="Multan",
        milk_rate=50,
        opening_balance=0,
        active=True,
    )
    db.session.add(customer)
    db.session.commit()

    entry = MilkEntry(
        customer_id=customer.id,
        entry_date=datetime.strptime("2026-07-07", "%Y-%m-%d").date(),
        morning_litres=2,
        evening_litres=1,
        total_litres=3,
        rate=50,
        amount=150,
    )
    db.session.add(entry)
    db.session.commit()

    response = client.get("/reports/download?period=overall")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"


def test_auto_delete_removes_records_older_than_two_months(client):
    customer = Customer(
        name="Old Data",
        mobile="03006667777",
        address="Faisalabad",
        milk_rate=40,
        opening_balance=0,
        active=True,
    )
    db.session.add(customer)
    db.session.commit()

    old_date = datetime.utcnow().date() - timedelta(days=61)

    old_entry = MilkEntry(
        customer_id=customer.id,
        entry_date=old_date,
        morning_litres=1,
        evening_litres=0,
        total_litres=1,
        rate=40,
        amount=40,
    )
    old_payment = Payment(
        customer_id=customer.id,
        payment_date=old_date,
        amount=40,
        payment_mode="Cash",
        notes="old",
    )
    old_expense = Expense(
        category="Feed",
        description="Old feed cost",
        amount=20,
        expense_date=old_date,
    )
    db.session.add_all([old_entry, old_payment, old_expense])
    db.session.commit()

    response = client.get("/reports")
    assert response.status_code == 200

    assert MilkEntry.query.filter_by(customer_id=customer.id).count() == 0
    assert Payment.query.filter_by(customer_id=customer.id).count() == 0
    assert Expense.query.count() == 0


def test_settings_update_retention_days(client):
    response = client.post(
        "/settings",
        data={
            "default_milk_rate": "60",
            "currency": "INR",
            "theme": "light",
            "language": "en",
            "retention_days": "90",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    from models.setting import Setting

    assert Setting.get_value("retention_days") == "90"


def test_backup_download_and_restore_roundtrip(client):
    customer = Customer(
        name="Backup Customer",
        mobile="03002223333",
        address="Quetta",
        milk_rate=58,
        opening_balance=25,
        active=True,
    )
    db.session.add(customer)
    db.session.commit()

    backup_response = client.get("/settings/backup.json")
    assert backup_response.status_code == 200
    assert backup_response.mimetype == "application/json"

    backup_payload = backup_response.get_json()
    assert backup_payload["customers"]

    Customer.query.delete()
    db.session.commit()
    assert Customer.query.count() == 0

    restore_response = client.post(
        "/settings/restore",
        data={
            "backup_file": (io.BytesIO(json.dumps(backup_payload).encode("utf-8")), "milkmaster-backup.json")
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert restore_response.status_code == 200
    assert Customer.query.filter_by(mobile="03002223333").count() == 1


def test_pwa_assets_and_offline_page(client):
    manifest_response = client.get("/manifest.json")
    assert manifest_response.status_code == 200
    assert manifest_response.mimetype == "application/json"
    assert manifest_response.get_json()["name"] == "MilkMaster"

    assets_response = client.get("/pwa-assets.json")
    assert assets_response.status_code == 200
    asset_payload = assets_response.get_json()
    assert "/static/css/style.css" in asset_payload["assets"]
    assert "/offline" in asset_payload["shell"]

    service_worker_response = client.get("/service-worker.js")
    assert service_worker_response.status_code == 200
    assert service_worker_response.mimetype == "application/javascript"

    offline_response = client.get("/offline")
    assert offline_response.status_code == 200
    assert b"No internet connection" in offline_response.data
