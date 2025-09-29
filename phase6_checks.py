import json
import os
import sys
import tempfile
from contextlib import suppress
from pathlib import Path

from fastapi.testclient import TestClient

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None  # type: ignore

PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / ".env"
if load_dotenv and ENV_PATH.exists():
    load_dotenv(ENV_PATH)

BACKEND_PATH = str(PROJECT_ROOT / "backend")
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

from app.main import app

client = TestClient(app)

results: list[dict[str, object]] = []

def record(step: str, response=None, error: Exception | None = None) -> None:
    entry: dict[str, object] = {"step": step}
    if response is not None:
        entry["status_code"] = response.status_code
        content_type = response.headers.get("content-type", "")
        body = None
        if "application/json" in content_type:
            with suppress(Exception):
                body = response.json()
        if body is None:
            body = response.text
        entry["body"] = body
    if error is not None:
        entry["error"] = str(error)
    results.append(entry)

def main() -> int:
    try:
        resp = client.get("/health")
        record("GET /health", resp)

        identifier = "+254700000010"
        resp = client.post("/auth/otp", json={"phone": identifier})
        record("POST /auth/otp", resp)
        if resp.status_code != 200:
            raise RuntimeError("OTP request failed")

        resp = client.post(
            "/auth/verify",
            json={
                "phone": identifier,
                "code": "123456",
                "full_name": "Phase6 Tester",
                "roles": ["borrower", "underwriter"],
            },
        )
        record("POST /auth/verify", resp)
        if resp.status_code != 200:
            raise RuntimeError("OTP verification failed")

        payload = resp.json()
        token = payload.get("access_token")
        if not token:
            raise RuntimeError("Missing access token")
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.post(
            "/me/consents",
            headers=headers,
            json={"mpesa": True, "geo": True, "documents": True},
        )
        record("POST /me/consents", resp)

        resp = client.patch(
            "/me/profile",
            headers=headers,
            json={
                "full_name": "Phase6 Tester",
                "business_type": "agriculture",
                "business_name": "Green Farm",
                "phone": identifier,
                "location": "Nairobi",
            },
        )
        record("PATCH /me/profile", resp)

        resp = client.post("/score/compute", headers=headers)
        record("POST /score/compute", resp)
        resp = client.get("/score/me", headers=headers)
        record("GET /score/me", resp)

        resp = client.get("/ai/greenscore/current", headers=headers)
        record("GET /ai/greenscore/current", resp)

        resp = client.get("/ai/greenscore/history", headers=headers, params={"months": 6})
        record("GET /ai/greenscore/history", resp)

        resp = client.get("/ai/carbon-credits/portfolio", headers=headers)
        record("GET /ai/carbon-credits/portfolio", resp)

        tmp_path = Path(tempfile.gettempdir()) / "phase6_evidence.txt"
        tmp_path.write_text("sample evidence content for phase 6 checks")
        try:
            with tmp_path.open("rb") as handle:
                files = {"file": ("evidence.txt", handle, "text/plain")}
                data = {
                    "sector": "agriculture",
                    "region": "Kenya",
                    "evidence_type": "solar_installation",
                    "description": "Phase 6 automated check",
                }
                resp = client.post(
                    "/ai/evidence/process",
                    headers=headers,
                    data=data,
                    files=files,
                )
            record("POST /ai/evidence/process", resp)
        finally:
            with suppress(FileNotFoundError):
                tmp_path.unlink()

        resp = client.post(
            "/loan/quote",
            headers=headers,
            json={"amount": 50000, "tenor": 12},
        )
        record("POST /loan/quote", resp)

        resp = client.post(
            "/loan/apply",
            headers=headers,
            json={"amount": 50000, "tenor": 12, "purpose": "Working capital expansion"},
        )
        record("POST /loan/apply", resp)
        loan_id = None
        with suppress(Exception):
            loan_id = resp.json().get("id")

        resp = client.get("/loan/my", headers=headers)
        record("GET /loan/my", resp)

        if loan_id:
            resp = client.post(
                f"/admin/applications/{loan_id}/decision",
                headers=headers,
                json={"decision": "approved"},
            )
            record(f"POST /admin/applications/{loan_id}/decision", resp)
        else:
            record("POST /admin/applications/<loan_id>/decision", error="loan_id missing")

    except Exception as exc:
        record("exception", error=exc)
        print(json.dumps(results, indent=2, default=str))
        return 1

    print(json.dumps(results, indent=2, default=str))
    return 0

if __name__ == "main":
    raise SystemExit("Run as module")

if __name__ == "__main__":
    raise SystemExit(main())
