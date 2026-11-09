"""FastAPI application entry point for Phone Advisor."""

from fastapi import FastAPI

app = FastAPI(
    title="Phone Advisor API",
    description="API tư vấn điện thoại thông minh bằng NLP và AI Agent",
    version="1.0.0",
)


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    """Endpoint kiểm tra trạng thái hoạt động của hệ thống."""
    return {"status": "ok"}
