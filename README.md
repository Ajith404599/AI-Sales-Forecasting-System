# Product & Analytics Management System

A full-stack enterprise analytics platform powered by **FastAPI** (Backend) and **Streamlit** (Frontend) with MySQL database support.

---

## ⚡ Quick Start (Single Command)

You can run both the Backend (FastAPI) and Frontend (Streamlit) together with a single command from the project root:

### Using Python:
```bash
python run.py
```

### Using PowerShell (Windows):
```powershell
.\run.ps1
```

### Using Command Prompt / Double Click (Windows):
```cmd
run.bat
```

### Using Bash (Linux / macOS):
```bash
chmod +x run.sh
./run.sh
```

---

## 🌐 Service URLs

Once running, access the services at:
- **Frontend Dashboard (Streamlit):** [http://localhost:8501](http://localhost:8501)
- **Backend API (FastAPI):** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## ⚙️ Optional Launch Arguments

`run.py` accepts several custom parameters:

```bash
# Custom ports
python run.py --backend-port 8000 --frontend-port 8501

# Run Streamlit in headless mode (doesn't auto-open browser tab)
python run.py --headless

# Disable backend auto-reload
python run.py --no-reload

# View all options
python run.py --help
```

## Existing MySQL Database Upgrade

For an existing database, apply `app/migrations/001_phase1_auth_sales.sql` once before starting the updated backend. It adds authentication state to `users`, permits the `analyst` role, and indexes sales by creator without replacing existing products, sales, or IDs. Back up the database first; do not apply this one-time migration more than once.

Set `SECRET_KEY` in `app/backend/.env` to a generated random value before deployment. Public account creation assigns the `analyst` role; after three incorrect passwords an account is locked for 15 minutes. Managers and Admins can update or delete sales; staff can update only sales they created.

## Sales Forecasting and Daily Training

Apply `app/migrations/001_phase1_auth_sales.sql`, then `app/migrations/002_phase2_forecasting.sql`, `app/migrations/003_phase3_full_name.sql`, and `app/migrations/004_auth_sessions.sql` to an existing MySQL database. The forecasting service trains on daily product quantities aggregated from `sales`, joined to the existing `products` table. It uses shifted lag/rolling features, evaluates the final 20% of dates chronologically, and selects the candidate with the lowest holdout RMSE (MAE breaks ties). The stored MAE, RMSE, and R² are calculated from those held-out records.

The Login History page reads the authenticated user's paired sign-in/session-end records from `GET /auth/history`; access tokens are limited to 15 minutes. Apply the auth-session migration before deploying this history endpoint.

The selected fitted preprocessing/model pipeline is stored as `sales_forecast_<version>.pkl` under `app/backend/model_artifacts` by default. Set `MODEL_ARTIFACT_DIR` to a persistent writable location when deploying. Only Admins can call `POST /models/retrain`; `POST /forecast/predict` uses the active artifact and writes each result to MySQL prediction history.

Run a daily job independently of Streamlit. In Windows Task Scheduler, set the program to the project `.venv\Scripts\python.exe`, the arguments to `app\backend\train_daily.py`, and **Start in** to the project root; configure the desired daily trigger. On cron, use a command such as `0 2 * * * /path/to/project/.venv/bin/python /path/to/project/app/backend/train_daily.py`. The job reads its MySQL settings from `app/backend/.env` or environment variables, prints a JSON result, and exits nonzero on failure. A failed run is recorded in `model_runs`; the active model is switched only after a new version has trained, passed prediction validation, and been atomically written.

---

## 🛑 Stopping Services

Press `Ctrl + C` in the terminal at any time. The runner will gracefully terminate both the FastAPI server and the Streamlit application cleanly without leaving orphaned background processes.
