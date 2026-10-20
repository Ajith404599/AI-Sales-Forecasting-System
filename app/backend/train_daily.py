import json
import sys

from app.core.database import Base, SessionLocal, engine
from app.services.forecasting_service import train_and_activate_model
import app.models


def main() -> int:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        result = train_and_activate_model(db)
        print(json.dumps(result, default=str, sort_keys=True))
        return 0 if result["training_status"] == "succeeded" else 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())