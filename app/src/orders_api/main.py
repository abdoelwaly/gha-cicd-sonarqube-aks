"""Orders API: a small service used to demonstrate the CI/CD pipeline.

It keeps orders in memory, exposes health probes for Kubernetes and
Prometheus metrics at /metrics.
"""

from __future__ import annotations

import os
import time
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Request, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, Field

APP_VERSION = os.getenv("APP_VERSION", "dev")

REQUESTS = Counter(
    "http_requests_total",
    "HTTP requests by method, route and status code.",
    ["method", "route", "status"],
)
LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency by method and route.",
    ["method", "route"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5),
)


class OrderIn(BaseModel):
    item: str = Field(min_length=1, max_length=100)
    quantity: int = Field(gt=0, le=1000)


class Order(OrderIn):
    id: UUID


app = FastAPI(title="orders-api", version=APP_VERSION)
_orders: dict[UUID, Order] = {}


@app.middleware("http")
async def record_metrics(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    route = request.scope.get("route")
    path = route.path if route else "unmatched"
    LATENCY.labels(request.method, path).observe(time.perf_counter() - start)
    REQUESTS.labels(request.method, path, str(response.status_code)).inc()
    return response


@app.get("/healthz", include_in_schema=False)
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz", include_in_schema=False)
def readiness() -> dict[str, str]:
    return {"status": "ready", "version": APP_VERSION}


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/orders", status_code=status.HTTP_201_CREATED)
def create_order(order: OrderIn) -> Order:
    created = Order(id=uuid4(), **order.model_dump())
    _orders[created.id] = created
    return created


@app.get("/orders")
def list_orders() -> list[Order]:
    return list(_orders.values())


@app.get("/orders/{order_id}")
def get_order(order_id: UUID) -> Order:
    order = _orders.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")
    return order


@app.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: UUID) -> Response:
    if _orders.pop(order_id, None) is None:
        raise HTTPException(status_code=404, detail="order not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
