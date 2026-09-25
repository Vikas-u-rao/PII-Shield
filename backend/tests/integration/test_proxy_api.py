"""
Integration Tests for Proxy API Endpoint
Verifies end-to-end inbound gateway execution via FastAPI TestClient.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_proxy_chat_mask_and_pseudonymize():
    payload = {
        "messages": [
            {
                "role": "user",
                "content": "My Aadhaar is 2345 6789 0124 and call me at 9876543210."
            }
        ]
    }

    response = client.post("/api/v1/proxy/chat/completions", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["outcome"] == "FORWARDED"
    sanitized = data["sanitized_messages"][0]["content"]

    # Raw Aadhaar should be masked preserving last 4 digits
    assert "2345 6789 0124" not in sanitized
    assert "XXXXXXXX0124" in sanitized

    # Phone should be pseudonymized with reserved token
    assert "9876543210" not in sanitized
    assert "⟦PII_PHONE_NUMBER_01⟧" in sanitized


def test_proxy_chat_policy_block():
    # Passport is configured with BLOCK policy action
    payload = {
        "messages": [
            {
                "role": "user",
                "content": "Here is my passport number: A1234567"
            }
        ]
    }

    response = client.post("/api/v1/proxy/chat/completions", json=payload)
    assert response.status_code == 403
    assert "Privacy violation" in response.json()["detail"]
