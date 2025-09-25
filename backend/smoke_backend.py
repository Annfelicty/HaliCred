from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db import Base, get_db


def prepare_inmemory_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db


def run_smoke():
    prepare_inmemory_db()
    client = TestClient(app)

    summary = {}

    res = client.get("/health")
    summary["health"] = (res.status_code, res.json())

    client.post("/auth/otp", json={"phone": "+254799999999"})
    verify = client.post(
        "/auth/verify",
        json={"phone": "+254799999999", "code": "123456", "full_name": "Smoke User"},
    )
    summary["verify_status"] = verify.status_code
    data = verify.json() if verify.status_code == 200 else {}

    token = data.get("access_token")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    summary["score"] = client.post("/score/compute", headers=headers).status_code
    summary["loan_quote"] = (
        client.post(
            "/loan/quote",
            json={"amount": 25000, "tenor": 12},
            headers=headers,
        ).status_code
    )
    summary["evidence"] = client.post("/evidence", headers=headers).status_code

    return summary


if __name__ == "__main__":
    results = run_smoke()
    for key, value in results.items():
        print(f"{key}: {value}")
