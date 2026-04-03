"""Transaction API integration tests."""

from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.finance import Account


def test_create_transaction(
    client: TestClient,
    test_db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    account = Account(name="pytest-cash", balance=Decimal("1000.0000"))
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
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["amount"] == amount


def test_insufficient_funds_transfer(
    client: TestClient,
    test_db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    low = Account(name="from", balance=Decimal("10.0000"))
    high = Account(name="to", balance=Decimal("0.0000"))
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
        headers=normal_user_token_headers,
    )
    assert response.status_code == 400


def test_unauthorized_access(client: TestClient) -> None:
    response = client.get("/api/v1/transactions/")
    assert response.status_code == 401
