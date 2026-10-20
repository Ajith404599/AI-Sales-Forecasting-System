import re
from typing import Dict, Any, List
from google import genai
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings

DATABASE_SCHEMA_CONTEXT = """
Database Schema:
1. products (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(150),
    category VARCHAR(100),
    base_price DECIMAL(10,2),
    description TEXT,
    active_status BOOLEAN,
    created_at TIMESTAMP
)

2. users (
    user_id INT PRIMARY KEY,
    username VARCHAR(50),
    email VARCHAR(100),
    role ENUM('admin', 'manager', 'staff'),
    is_active BOOLEAN,
    created_at TIMESTAMP
)

3. sales (
    sale_id INT PRIMARY KEY,
    product_id INT REFERENCES products(product_id),
    user_id INT REFERENCES users(user_id),
    quantity INT,
    unit_price DECIMAL(10,2),
    discount_amount DECIMAL(10,2),
    total_amount DECIMAL(10,2),
    sale_date TIMESTAMP
)

4. audit_logs (
    log_id INT PRIMARY KEY,
    user_id INT REFERENCES users(user_id),
    action VARCHAR(50),
    module VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP
)
"""

SYSTEM_SQL_PROMPT = f"""
You are an expert MySQL database administrator and BI analyst for a retail platform.
Given a user's question, generate a single executable MySQL query.

{DATABASE_SCHEMA_CONTEXT}

STRICT SAFETY RULES:
1. Output ONLY a valid SQL query starting with SELECT.
2. DO NOT output markdown code blocks (e.g. no ```sql or ```).
3. Absolutely NO mutation statements (NO DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE, REPLACE).
4. Use standard MySQL functions (e.g., DATE_FORMAT, IFNULL, ROUND, SUM, COUNT, AVG).
5. If the user asks for a chart or breakdown, aggregate appropriately (GROUP BY) and ORDER BY relevant metric.
"""


def get_gemini_client():
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured in .env file.")
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def sanitize_sql(sql: str) -> str:
    cleaned = re.sub(r"```(sql)?", "", sql).strip("` \n;")
    # Safety assertion
    first_token = cleaned.split()[0].upper() if cleaned.split() else ""
    if first_token != "SELECT":
        raise ValueError("Security violation: Only SELECT queries are permitted.")
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "REPLACE"]
    for word in forbidden:
        if re.search(rf"\b{word}\b", cleaned, re.IGNORECASE):
            raise ValueError(f"Security violation: Query contains disallowed keyword '{word}'.")
    return cleaned


def query_text_to_sql(question: str, db: Session) -> Dict[str, Any]:
    client = get_gemini_client()

    # 1. Ask Gemini to formulate the SQL query
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"{SYSTEM_SQL_PROMPT}\nUser Question: {question}\nSQL Query:"
    )
    raw_sql = response.text.strip()
    clean_sql = sanitize_sql(raw_sql)

    # 2. Execute SQL safely
    cursor = db.execute(text(clean_sql))
    rows = [dict(row._mapping) for row in cursor.fetchall()]

    # Convert non-serializable objects (Decimal, datetime) to string/float
    serialized_rows = []
    for r in rows:
        row_dict = {}
        for k, v in r.items():
            if hasattr(v, "isoformat"):
                row_dict[k] = v.isoformat()
            elif hasattr(v, "__float__"):
                row_dict[k] = float(v)
            else:
                row_dict[k] = v
        serialized_rows.append(row_dict)

    # 3. Ask Gemini for an executive explanation
    summary_prompt = f"""
    The user asked: "{question}"
    We executed this SQL: {clean_sql}
    And got these results (truncated to first 10 items): {serialized_rows[:10]}

    Provide a concise, professional, direct 2-3 sentence business summary of the findings.
    Mention specific metrics and key takeaways.
    """
    summary_response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=summary_prompt
    )

    return {
        "sql": clean_sql,
        "results": serialized_rows,
        "summary": summary_response.text.strip()
    }
