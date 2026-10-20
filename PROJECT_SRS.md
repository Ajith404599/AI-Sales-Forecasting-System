# PROJECT_SRS.md

# AI-Powered Sales Forecasting and Business Performance Analytics System

## 1. Purpose

Extend the existing team repository into a complete, integrated sales
analytics system. Preserve existing teammate modules and database
relationships. Do not rewrite working teammate functionality unless
required for integration.

## 2. Mandatory Technology Stack

-   Frontend: Streamlit
-   Frontend styling: custom CSS and safe HTML embedded in Streamlit,
    plus Streamlit components
-   Backend: FastAPI REST API
-   Database: MySQL 8+
-   ORM/database layer: follow the existing repository's
    SQLAlchemy/PyMySQL architecture
-   AI/ML: pandas, NumPy, scikit-learn
-   Model persistence: joblib `.pkl`
-   Charts: Plotly
-   Authentication: JWT + hashed passwords
-   Configuration/secrets: environment variables; never hard-code
    production secrets

## 3. Non-Negotiable UI Requirement

The frontend framework MUST remain Streamlit, but the application must
visually resemble a polished modern SaaS/business website rather than a
default Streamlit demo.

Use custom CSS/HTML styling inside Streamlit where appropriate. Build: -
polished landing page - top navigation on public pages - professional
Sign In and Create Account pages - authenticated app shell with
sidebar/topbar - responsive KPI cards - polished forms and tables -
charts - badges/status indicators - consistent spacing, typography,
border radius, shadows and hover states - empty/loading/error/success
states - consistent design across every page

Hide unnecessary default Streamlit chrome where practical. Do not
replace Streamlit with React, Flask templates, Django templates, or a
separate static HTML frontend.

## 4. Existing Team Code

Treat the current GitHub repository as the integration baseline.
Preserve teammate-owned modules, especially Products and existing
supporting modules. Reuse existing product IDs and relationships. Do not
create a second incompatible product/user/auth system.

Before modifying an existing file: 1. inspect its current
implementation; 2. preserve compatible routes and database
relationships; 3. extend rather than duplicate functionality; 4. keep
existing tests working where possible.

## 5. User-Owned Modules to Complete

### 5.1 Authentication

Implement/integrate: - Sign In - Create Account - password hashing - JWT
access tokens - role-aware access - account status - logout/session
handling - last login - three failed-login-attempt protection with
temporary lock - useful remaining-attempt and lock messages - duplicate
username/email checks - public signup defaults to Sales Analyst; public
users cannot self-create Admin accounts

### 5.2 Dashboard

Professional dashboard containing real database-driven values: - live
date/time - logged-in user greeting - total revenue - total units sold -
total sales transactions - total active products - average sale value -
top-selling product - recent sales - revenue/sales trend charts -
FastAPI status - database status - active ML model status - last model
training timestamp

No fake KPI values.

### 5.3 Sales Management

Create/complete sales CRUD integrated with teammate Products: - add
sale - list/search/filter sales - update sale - delete sale with
appropriate permissions - product selection from existing Products
table - quantity - unit price/selling price - sale date/time -
calculated total amount - user who created the record - validation and
meaningful API errors

Sales must reference the existing product primary key through a foreign
key.

### 5.4 AI Sales Forecasting

Forecast future sales using historical sales records stored in MySQL.

The ML system must be real and reproducible. Never return hard-coded
predictions.

Training data source: MySQL -\> historical sales + required product/date
attributes -\> preprocessing/feature engineering -\> model training.

Candidate algorithms: 1. Linear Regression as a baseline 2. Random
Forest Regressor 3. Gradient Boosting Regressor

The architecture should make it easy to add other suitable regressors
later.

Possible features, when supported by available data: -
product/category - date - day of week - month - quarter - year - unit
price - historical quantity sold - lagged sales values - rolling
averages - recent trend features

Do NOT create leakage by using future information to predict the past.

For forecasting, use chronological/time-aware train/test validation
instead of an ordinary random split whenever the data is time ordered.

Prediction target: future quantity sold (or the project's final agreed
sales-demand target). Keep the target consistent across training, API,
database and UI.

### 5.5 Model Evaluation and Selection

Evaluate candidate models using real held-out data.

Store/display: - MAE - RMSE - R² - algorithm/model name - model
version - target - number of training records - training timestamp -
model file - active/inactive status

Select the best model using a documented metric rule. Do not fabricate
metrics.

Persist the complete fitted preprocessing/model pipeline using joblib as
a `.pkl` file so the prediction endpoint can load the exact trained
pipeline.

### 5.6 Daily Model Retraining

Implement safe automatic daily retraining.

Expected behavior: 1. read the latest eligible historical sales records
from MySQL; 2. validate that sufficient clean data exists; 3. build
time-aware features; 4. train candidate algorithms; 5. evaluate them; 6.
select the best valid candidate; 7. save a versioned `.pkl`; 8. store
actual metrics in MySQL; 9. mark the successful model active; 10. keep
the previous working model available if retraining fails; 11. record
training status/errors.

Do not retrain merely because a Streamlit page is refreshed.

Provide BOTH: - a protected manual retrain FastAPI endpoint/button for
Admin; - a standalone retraining command/script that can be invoked once
daily by Windows Task Scheduler, cron, or another external scheduler.

The app must show the last successful training date and current active
model.

### 5.7 Forecast API

FastAPI must provide a protected prediction endpoint that: - loads the
active persisted pipeline/model; - validates input; - generates a
forecast; - returns model/version information with the result; - stores
the prediction in prediction history.

### 5.8 Prediction History

Persist forecasts in MySQL, including: - prediction ID - product ID when
applicable - requested forecast date/horizon - predicted quantity -
model/version - prediction timestamp - user ID - optional actual value
later for comparison

Streamlit page: - searchable/filterable history - date filters - product
filter - model/version filter - clear table and charts where useful

### 5.9 Model Performance Page

Professional Streamlit page showing: - active model - version - MAE -
RMSE - R² - training records - training date - comparison of candidate
models - training history - active/inactive model status - Admin retrain
control - retraining success/failure feedback

## 6. Database Requirements

Extend the EXISTING schema instead of replacing it.

Required logical entities (reuse existing equivalents if already
present): - users - login_attempts or equivalent - products
(teammate-owned existing table) - sales - prediction_history -
model_metrics / model_runs - audit logs if already present

Use: - primary keys - foreign keys - indexes on frequently filtered
fields - timestamps - sensible NOT NULL constraints - appropriate
decimal types for currency - cascade/restrict behavior chosen
deliberately

Do not duplicate Products.

## 7. Suggested API Groups

Preserve existing routes when compatible. The completed backend should
logically expose: - `/auth/...` - `/products/...` (existing teammate
module) - `/sales/...` - `/analytics/...` - `/forecast/...` or existing
AI route - `/predictions/...` - `/models/...` - `/health`

All protected endpoints must validate JWTs on the backend. Never rely
only on hidden Streamlit buttons for authorization.

## 8. Frontend Pages

Public: - Home - Features - About - Sign In - Create Account

Authenticated: - Dashboard - Sales Management - Products (existing
teammate page/module) - AI Sales Forecasting - Prediction History -
Model Performance - Profile/Settings where already supported - Logout -
existing teammate pages as applicable

Navigation must feel like one unified website.

## 9. Website Visual Direction

Aim for a modern analytics SaaS dashboard: - strong hero section on
Home - professional business copy - metric cards - clear visual
hierarchy - charts with titles and readable axes - compact professional
forms - consistent buttons - sidebar/topbar navigation - responsive
columns - no raw HTML appearing as text - no developer/debug information
in normal UI - no basic `st.title`-only pages - avoid excessive emojis -
use CSS classes and reusable UI helpers rather than duplicating huge
style blocks

## 10. Security

-   hash passwords
-   JWT expiration
-   environment-based secret key
-   no passwords/tokens in source control
-   `.env` ignored by Git
-   validate request data with Pydantic
-   parameterized/ORM database access
-   role checks for privileged actions
-   do not expose password hashes through APIs
-   sensible CORS configuration
-   handle DB/API errors without leaking sensitive internals

## 11. Code Quality

-   preserve the current repository structure unless a change is
    justified
-   modular code
-   schemas separate from ORM models where current architecture does
    this
-   reusable services
-   comments/docstrings where useful
-   type hints
-   no hard-coded demo metrics/predictions
-   no duplicate business logic in Streamlit; Streamlit should call
    FastAPI
-   FastAPI owns business logic and database operations
-   add/update tests for important endpoints and ML service behavior

## 12. Completion Criteria

The project is complete only when: 1. MySQL schema initializes
successfully. 2. FastAPI starts without errors. 3. Streamlit starts
without errors. 4. signup/login/logout work. 5. failed-login protection
works. 6. teammate Products remains functional. 7. sales CRUD works and
references Products. 8. dashboard reads real database data. 9. ML trains
from MySQL sales history. 10. candidate algorithms are evaluated with
real metrics. 11. best fitted pipeline is saved as `.pkl`. 12.
prediction API loads the persisted model. 13. prediction history is
saved. 14. Model Performance displays real metrics. 15. manual
retraining works. 16. the daily retraining script can run independently.
17. failure during retraining does not destroy the last working model.
18. Streamlit pages visually resemble one cohesive professional website.
19. existing teammate functionality is not unnecessarily broken. 20.
tests/documentation are updated.

## 13. GitHub Copilot Implementation Instruction

Work through this specification systematically. First inspect the
existing repository and produce a concise implementation plan
identifying what already exists, what can be reused, and what is
missing. Then implement missing functionality incrementally.

Do NOT regenerate the entire repository from scratch. Do NOT delete
working teammate code. Do NOT create duplicate Products/auth/database
systems. Do NOT invent database columns without checking the current
schema/models. Do NOT use hard-coded analytics or fake ML results. Do
NOT train the model on every Streamlit rerun. Do NOT replace Streamlit
with another frontend.

After each major module: - verify imports; - verify FastAPI route
registration; - verify database compatibility; - update/add tests; -
state which files were changed.

## 14. Prompt to Give GitHub Copilot

Read `PROJECT_SRS.md` completely before editing any code. Inspect the
entire existing repository, especially the current FastAPI routes,
SQLAlchemy models, MySQL schema, Streamlit frontend, Products module,
Sales/AI code, tests, and requirements files. Treat existing teammate
code as the integration baseline.

Implement all missing requirements from `PROJECT_SRS.md` using Streamlit
as the frontend, FastAPI as the backend, MySQL as the database, and
scikit-learn/joblib for AI/ML. The Streamlit frontend must look like a
polished real SaaS website using reusable custom CSS/HTML styling while
remaining fully Streamlit-based. Complete my modules: authentication,
professional dashboard, sales management, AI sales forecasting,
prediction history, model performance, and safe daily ML retraining from
current MySQL sales data.

Use real database data and real calculated ML metrics only. Train and
compare Linear Regression, Random Forest Regressor, and Gradient
Boosting Regressor using time-aware evaluation, select and persist the
best valid fitted pipeline as a versioned `.pkl`, expose
prediction/retraining APIs, and store model metrics and prediction
history in MySQL. Daily retraining must be implemented as an
independently runnable job suitable for Windows Task Scheduler/cron, not
as code that runs on every Streamlit refresh. Preserve the last working
model if a retraining attempt fails.

Do not overwrite or duplicate teammate-owned Products or other working
modules. Integrate with them. Before coding, show a file-by-file gap
analysis and implementation plan. Then implement incrementally and keep
the application runnable after each stage.
