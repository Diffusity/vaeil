"""Composition only: human review is the deployed baseline, never an HTTP switch."""
from datetime import datetime, timezone
import os
import secrets
import threading
import uuid
from vaeil.adapters import authentication
from vaeil.adapters.persistence import open_repository
from vaeil.application.admission import AdmissionApplication
from vaeil.domain import Verdict
from vaeil.domain.repository import RepositoryError


class RuntimeClock:
    def today(self):
        return self.now().date()
    def now(self):
        return datetime.now(timezone.utc)


class RuntimeTokens:
    def new_token(self):
        return secrets.token_urlsafe(32)
    def new_id(self):
        return uuid.uuid4().hex


class HumanReviewModel:
    def vet(self, application_note):
        return Verdict.NEEDS_REVIEW


class RuntimeAdmission:
    """Lazily own the SQL engine; failed auth storage never breaks public health."""
    def __init__(self):
        self._lock = threading.Lock()
        self._context = None
        self._application = None

    def get(self):
        with self._lock:
            if self._application is not None:
                return self._application
            context = open_repository(os.environ.get("DATABASE_URL") or "sqlite:///vaeil.sqlite")
            repository = context.__enter__()
            try:
                application = AdmissionApplication(repository, passwords=authentication, tokens=RuntimeTokens(),
                                                   clock=RuntimeClock(), model=HumanReviewModel())
                email, password = os.environ.get("VAEIL_ADMIN_EMAIL"), os.environ.get("VAEIL_ADMIN_PASSWORD")
                if bool(email) != bool(password):
                    raise RepositoryError("Admin configuration is incomplete.")
                if email and password:
                    application.seed_admin(email=email, password=password)
            except Exception:
                context.__exit__(None, None, None)
                raise
            self._context, self._application = context, application
            return application

    def close(self):
        with self._lock:
            if self._context is not None:
                self._context.__exit__(None, None, None)
                self._context, self._application = None, None
