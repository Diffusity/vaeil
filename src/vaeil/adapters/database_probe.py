"""One read-only connectivity attempt. DSN via environment, exit status only.

The parent kills/reaps this process after ten seconds, including DNS/connect/
query/cleanup work after process creation. It never exposes captured diagnostics.
"""

import os

import psycopg
import certifi


def main() -> int:
    try:
        with psycopg.connect(
            os.environ["DATABASE_URL"], sslmode="verify-full", sslrootcert=certifi.where(), connect_timeout=2,
            options="-c statement_timeout=2000 -c default_transaction_read_only=on",
            autocommit=True,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return 0 if cursor.fetchone() == (1,) else 1
    except Exception:
        # Worker diagnostics may contain credentials; only generic exit state escapes.
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

