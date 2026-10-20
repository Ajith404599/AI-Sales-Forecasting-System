"""API route modules for authentication, products, sales, analytics, models, and audit logs."""
from app.api import auth, products, sales, analytics, users, audit, ai, forecast, predictions, models

__all__ = ["auth", "products", "sales", "analytics", "users", "audit", "ai", "forecast", "predictions", "models"]
