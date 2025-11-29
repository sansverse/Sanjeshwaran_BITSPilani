import requests


def test_health():
    r = requests.get("http://127.0.0.1:8000/health", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"


def test_extract_sample_url():
    # This test expects the server to be running locally and accessible.
    sample_url = (
        "https://hackrx.blob.core.windows.net/assets/datathon-IIT/sample_2.png"
    )
    r = requests.post("http://127.0.0.1:8000/extract", data={"pdf_url": sample_url}, timeout=30)
    assert r.status_code == 200
    j = r.json()
    assert "status" in j
