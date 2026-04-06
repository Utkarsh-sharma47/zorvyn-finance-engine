"""Transaction API integration tests."""

import uuid
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.finance import Account, Transaction
from app.models.user import Department, Role


def test_create_transaction(
    client: TestClient,
    test_db: Session,
    finance_admin: dict,
) -> None:
    user_id = finance_admin["user_id"]
    account = Account(name="pytest-cash", balance=Decimal("1000.0000"), user_id=user_id)
    test_db.add(account)
    test_db.commit()
    test_db.refresh(account)

    amount = "250.2500"
    payload = {
        "account_id": account.id,
        "amount": amount,
        "transaction_type": "income",
        "category": "revenue",
        "description": "pytest create",
    }
    response = client.post(
        "/api/v1/transactions/",
        json=payload,
        headers=finance_admin["headers"],
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["amount"] == amount


def test_create_transaction_account_not_owned(
    client: TestClient,
    test_db: Session,
    finance_admin: dict,
) -> None:
    """Account exists but user_id does not match JWT user → 404 envelope."""
    _other_headers, other_uid = _register_admin(client)
    other = Account(name="other-user-cash", balance=Decimal("500.0000"), user_id=other_uid)
    test_db.add(other)
    test_db.commit()
    test_db.refresh(other)

    response = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": other.id,
            "amount": "10.0000",
            "transaction_type": "income",
            "category": "x",
            "description": "should fail",
        },
        headers=finance_admin["headers"],
    )
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert "access denied" in (body.get("error") or "").lower()


def test_create_transaction_account_missing_user_link(
    client: TestClient,
    test_db: Session,
    finance_admin: dict,
) -> None:
    """Legacy account with user_id NULL is treated as inaccessible."""
    orphan = Account(name="legacy", balance=Decimal("100.0000"), user_id=None)
    test_db.add(orphan)
    test_db.commit()
    test_db.refresh(orphan)

    response = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": orphan.id,
            "amount": "1.0000",
            "transaction_type": "expense",
            "category": "misc",
            "description": "nope",
        },
        headers=finance_admin["headers"],
    )
    assert response.status_code == 404


def test_insufficient_funds_transfer(
    client: TestClient,
    test_db: Session,
    finance_admin: dict,
) -> None:
    uid = finance_admin["user_id"]
    low = Account(name="from", balance=Decimal("10.0000"), user_id=uid)
    high = Account(name="to", balance=Decimal("0.0000"), user_id=uid)
    test_db.add(low)
    test_db.add(high)
    test_db.commit()
    test_db.refresh(low)
    test_db.refresh(high)

    response = client.post(
        "/api/v1/transactions/transfer",
        json={
            "from_account_id": low.id,
            "to_account_id": high.id,
            "amount": "100.0000",
            "description": "should fail",
        },
        headers=finance_admin["headers"],
    )
    assert response.status_code == 400


def _register_admin(client: TestClient) -> tuple[dict[str, str], int]:
    email = f"pytest_{uuid.uuid4().hex}@example.com"
    password = "PytestPass1!"
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "department": Department.FINANCE.value,
            "role": Role.ADMIN.value,
        },
    )
    assert reg.status_code == 200
    uid = reg.json()["data"]["id"]
    login = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, uid


def test_unauthorized_access(client: TestClient) -> None:
    response = client.get("/api/v1/transactions/")
    assert response.status_code == 401


def test_soft_delete_own_transaction(
    client: TestClient,
    test_db: Session,
    finance_admin: dict,
) -> None:
    user_id = finance_admin["user_id"]
    account = Account(name="del-cash", balance=Decimal("100.0000"), user_id=user_id)
    test_db.add(account)
    test_db.commit()
    test_db.refresh(account)

    create = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "5.0000",
            "transaction_type": "income",
            "category": "misc",
            "description": "to delete",
        },
        headers=finance_admin["headers"],
    )
    assert create.status_code == 200
    tx_id = create.json()["data"]["id"]

    delete = client.delete(f"/api/v1/transactions/{tx_id}", headers=finance_admin["headers"])
    assert delete.status_code == 200
    assert delete.json()["success"] is True

    test_db.expire_all()
    row = test_db.get(Transaction, tx_id)
    assert row is not None
    assert row.is_deleted is True


def test_soft_delete_forbidden_wrong_user(
    client: TestClient,
    test_db: Session,
    finance_admin: dict,
) -> None:
    user_id = finance_admin["user_id"]
    account = Account(name="owner-cash", balance=Decimal("100.0000"), user_id=user_id)
    test_db.add(account)
    test_db.commit()
    test_db.refresh(account)

    create = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "3.0000",
            "transaction_type": "expense",
            "category": "misc",
            "description": "other user cannot delete",
        },
        headers=finance_admin["headers"],
    )
    assert create.status_code == 200
    tx_id = create.json()["data"]["id"]

    other_headers, _ = _register_admin(client)
    delete = client.delete(f"/api/v1/transactions/{tx_id}", headers=other_headers)
    assert delete.status_code == 403
    assert delete.json()["success"] is False


def test_soft_delete_transfer_soft_deletes_counterpart(
    client: TestClient,
    test_db: Session,
    finance_admin: dict,
) -> None:
    uid = finance_admin["user_id"]
    low = Account(name="from-del", balance=Decimal("100.0000"), user_id=uid)
    high = Account(name="to-del", balance=Decimal("0.0000"), user_id=uid)
    test_db.add(low)
    test_db.add(high)
    test_db.commit()
    test_db.refresh(low)
    test_db.refresh(high)

    tr = client.post(
        "/api/v1/transactions/transfer",
        json={
            "from_account_id": low.id,
            "to_account_id": high.id,
            "amount": "15.0000",
            "description": "pair delete",
        },
        headers=finance_admin["headers"],
    )
    assert tr.status_code == 200
    data = tr.json()["data"]
    expense_id = data["expense_transaction"]["id"]
    income_id = data["income_transaction"]["id"]

    delete = client.delete(f"/api/v1/transactions/{expense_id}", headers=finance_admin["headers"])
    assert delete.status_code == 200

    test_db.expire_all()
    e = test_db.get(Transaction, expense_id)
    inc = test_db.get(Transaction, income_id)
    assert e is not None and e.is_deleted is True
    assert inc is not None and inc.is_deleted is True


def test_transfer_denied_if_counterparty_not_owned(
    client: TestClient,
    test_db: Session,
) -> None:
    headers_a, uid_a = _register_admin(client)
    _, uid_b = _register_admin(client)

    mine = Account(name="mine", balance=Decimal("1000.0000"), user_id=uid_a)
    theirs = Account(name="theirs", balance=Decimal("0.0000"), user_id=uid_b)
    test_db.add(mine)
    test_db.add(theirs)
    test_db.commit()
    test_db.refresh(mine)
    test_db.refresh(theirs)

    r = client.post(
        "/api/v1/transactions/transfer",
        json={
            "from_account_id": mine.id,
            "to_account_id": theirs.id,
            "amount": "10.0000",
            "description": "cross-user",
        },
        headers=headers_a,
    )
    assert r.status_code == 404
