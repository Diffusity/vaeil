"""Synthetic public deployment smoke. No credentials, writes or keep-alive loop."""

import argparse
import json
import time
import re
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
from urllib.parse import urlsplit


def read(url):
    try:
        with urlopen(url, timeout=5) as response:
            return response.status, response.read().decode()
    except HTTPError as error:
        return error.code, error.read().decode()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("origin")
    parser.add_argument("--expect-database-unavailable", action="store_true")
    args = parser.parse_args()
    origin = args.origin.rstrip("/")
    parsed = urlsplit(origin)
    if (not origin.startswith(("http://127.0.0.1:", "https://"))
            or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment):
        raise SystemExit("Use a loopback or HTTPS public origin, never a connection string.")
    for attempt in range(30):
        try:
            status, body = read(origin + "/api/health")
            if status == 200 and json.loads(body) == {"status": "ok"}:
                break
        except (URLError, TimeoutError, ValueError):
            pass
        time.sleep(1)
    else:
        raise SystemExit("Service did not become healthy; check host status privately.")
    status, page = read(origin + "/")
    assert status == 200 and '<div id="root">' in page
    assets = re.findall(r'(?:src|href)="(/assets/[^\"]+)"', page)
    assert assets
    for asset in assets:
        assert read(origin + asset)[0] == 200
    status, body = read(origin + "/api/demo/member")
    data = json.loads(body)
    assert status == 200 and set(data) == {"pseudonym", "values_profile"}
    assert data["pseudonym"] == "Comet"
    for canary in ("DemoPrivateNameZXQ", "demo-private-zxq@example.invalid", "+919876543210", "1987-03-14"):
        assert canary not in body + page
    status, body = read(origin + "/api/ready")
    expected = (503, {"status": "unavailable"}) if args.expect_database_unavailable else (200, {"status": "ready"})
    assert (status, json.loads(body)) == expected
    assert read(origin + "/api/health")[0] == 200
    print("PASS: synthetic HTML, anonymous payload, health and readiness contract")


if __name__ == "__main__":
    main()
