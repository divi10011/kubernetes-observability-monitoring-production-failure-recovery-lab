"""PayTrack: a simulated payment API designed for observability practice.

The service intentionally keeps payment records in memory. It never connects to a
payment provider and must not be used for real payment processing.
"""

from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Request, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, Field, field_validator

from paytrack.logging_config import configure_logging

configure_logging()
logger = logging.getLogger("paytrack")

HTTP_REQUESTS = Counter(
    "paytrack_http_requests_total",
    "Total HTTP requests handled by PayTrack, excluding metric scrapes.",
    ["method", "path", "status_code"],
)
HTTP_ERRORS = Counter(
    "paytrack_http_errors_total",
    "Total client and server HTTP error responses from PayTrack.",
    ["method", "path", "status_code"],
)
HTTP_LATENCY = Histogram(
    "paytrack_http_request_duration_seconds",
    "HTTP request latency in seconds, excluding metric scrapes.",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)
PAYMENT_TRANSACTIONS = Counter(
    "paytrack_payment_transactions_total",
    "Simulated payment transactions accepted by PayTrack.",
    ["outcome"],
)


class PaymentCreate(BaseModel):
    """Input for a simulated payment; do not submit real customer data."""

    amount: Annotated[float, Field(gt=0, le=1_000_000)]
    currency: Annotated[str, Field(min_length=3, max_length=3)] = "USD"
    reference: Annotated[str | None, Field(max_length=64)] = None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, currency: str) -> str:
        normalized = currency.upper()
        if not normalized.isalpha():
            raise ValueError("currency must contain three alphabetic characters")
        return normalized


class Payment(BaseModel):
    id: UUID
    amount: float
    currency: str
    reference: str | None
    status: str


def _truthy_environment_value(name: str) -> bool:
    return os.getenv(name, "false").strip().lower() in {"1", "true", "yes", "on"}


def _metric_path(path: str) -> str:
    """Return a bounded label value rather than an untrusted URL path."""
    known_paths = {"/", "/health", "/ready", "/payments", "/metrics"}
    return path if path in known_paths else "unmatched"


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.payments = []
    application.state.force_not_ready = _truthy_environment_value(
        "PAYTRACK_READINESS_FAILURE_MODE"
    )
    logger.info(
        "application_started",
        extra={"readiness_failure_mode": application.state.force_not_ready},
    )
    yield
    logger.info("application_stopped")


app = FastAPI(
    title="PayTrack",
    version="0.1.0",
    description="A simulated payment API for local Kubernetes observability labs.",
    lifespan=lifespan,
)


@app.middleware("http")
async def instrument_http_requests(request: Request, call_next):
    """Collect low-cardinality request metrics and emit structured completion logs."""
    if request.url.path == "/metrics":
        return await call_next(request)

    started_at = time.perf_counter()
    metric_path = _metric_path(request.url.path)
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception:
        logger.exception(
            "request_failed",
            extra={"method": request.method, "path": metric_path, "status_code": status_code},
        )
        raise
    finally:
        duration = time.perf_counter() - started_at
        labels = {"method": request.method, "path": metric_path, "status_code": str(status_code)}
        HTTP_REQUESTS.labels(**labels).inc()
        HTTP_LATENCY.labels(method=request.method, path=metric_path).observe(duration)
        if status_code >= 400:
            HTTP_ERRORS.labels(**labels).inc()
        logger.info(
            "request_completed",
            extra={
                "method": request.method,
                "path": metric_path,
                "status_code": status_code,
                "duration_seconds": round(duration, 6),
            },
        )


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "paytrack", "environment": os.getenv("PAYTRACK_ENVIRONMENT", "local")}


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness endpoint: the process can serve requests."""
    return {"status": "healthy"}


@app.get("/ready")
async def ready(request: Request) -> dict[str, str]:
    """Readiness endpoint, with a safe environment-controlled failure mode for the lab."""
    if request.app.state.force_not_ready:
        logger.warning("readiness_check_failed", extra={"reason": "failure_mode_enabled"})
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="not ready")
    return {"status": "ready"}


@app.get("/payments")
async def list_payments(request: Request) -> dict[str, list[Payment] | int]:
    payments = [Payment.model_validate(payment) for payment in request.app.state.payments]
    return {"items": payments, "count": len(payments)}


@app.post("/payments", response_model=Payment, status_code=status.HTTP_201_CREATED)
async def create_payment(payload: PaymentCreate, request: Request) -> Payment:
    payment = Payment(
        id=uuid4(),
        amount=payload.amount,
        currency=payload.currency,
        reference=payload.reference,
        status="accepted",
    )
    request.app.state.payments.append(payment)
    PAYMENT_TRANSACTIONS.labels(outcome="accepted").inc()
    logger.info(
        "payment_accepted",
        extra={"payment_id": str(payment.id), "outcome": payment.status},
    )
    return payment


@app.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

