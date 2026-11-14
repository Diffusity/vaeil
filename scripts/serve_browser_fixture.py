"""Owned, disposable browser-test fixture; never connects to deployment storage."""
from pathlib import Path
import os
import tempfile
import uvicorn
from vaeil.adapters.persistence import open_repository


def main():
    with tempfile.TemporaryDirectory(prefix="vaeil-browser-") as directory:
        url = "sqlite:///" + (Path(directory) / "browser.sqlite").as_posix()
        os.environ["DATABASE_URL"] = url
        os.environ["VAEIL_SECURE_COOKIES"] = "0"
        os.environ.pop("VAEIL_ADMIN_EMAIL", None)
        os.environ.pop("VAEIL_ADMIN_PASSWORD", None)
        with open_repository(url) as repository:
            with repository.transaction() as unit:
                unit.issue_invite("browser-invite", issuer_id="fictional-browser-admin")
                unit.commit()
        uvicorn.run("vaeil.web:create_app", factory=True, host="127.0.0.1", port=8765)


if __name__ == "__main__":
    main()
