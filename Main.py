from fastapi import FastAPI, Request
import uvicorn
import requests
import sys
import io
import arabic_reshaper
from bidi.algorithm import get_display
from groq import Groq
import google.generativeai as genai
from cerebras.cloud.sdk import Cerebras
from datetime import datetime, timezone, timedelta
import pyodbc

# UTF-8 Fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

app = FastAPI()

# تأكد من وجود الجدول عند بدء التشغيل
@app.on_event("startup")
async def startup_event():
    init_db()

# ---------------- CONFIG ----------------
CHATWOOT_URL = "<YOUR_CHATWOOT_INSTANCE_URL>"   # e.g. https://company.chatwoot.com
ACCOUNT_ID = "<YOUR_ACCOUNT_ID>"                # Chatwoot account ID
ACCESS_TOKEN = "<YOUR_CHATWOOT_ACCESS_TOKEN>"   # must have API access permissions


# ---------------- GROQ KEYS ----------------
GROQ_API_KEYS = [
    "<GROQ_API_KEY_1>",
    "<GROQ_API_KEY_2>",
    "<GROQ_API_KEY_3>",
    "<GROQ_API_KEY_4>",
    "<GROQ_API_KEY_5>",
]


# ---------------- GEMINI KEYS ----------------
GEMINI_API_KEYS = [
    "<GEMINI_API_KEY_1>",
    "<GEMINI_API_KEY_2>",
    "<GEMINI_API_KEY_3>",
    "<GEMINI_API_KEY_4>",
    "<GEMINI_API_KEY_5>",
]


# ---------------- CEREBRAS KEYS ----------------
CEREBRAS_API_KEYS = [
    "<CEREBRAS_API_KEY_1>",
    "<CEREBRAS_API_KEY_2>",
    "<CEREBRAS_API_KEY_3>",
    "<CEREBRAS_API_KEY_4>",
]


# ---------------- DATABASE CONFIG ----------------
DB_CONN_STR = (
    "DRIVER={SQL Server};"
    "SERVER=<YOUR_DB_SERVER_IP_OR_HOST>;"
    "DATABASE=<YOUR_DATABASE_NAME>;"
    "Trusted_Connection=yes;"
)

TABLE_NAME = "<YOUR_REPORTS_TABLE_NAME>"
CUSTOMER_TABLE = "<YOUR_CUSTOMERS_TABLE_NAME>"


# ---------------- CREATE TABLES IF NOT EXISTS ----------------
def init_db():
    try:
        conn = pyodbc.connect(DB_CONN_STR)
        cursor = conn.cursor()

        cursor.execute(f"""
            IF NOT EXISTS (
                SELECT * FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_NAME = '{TABLE_NAME}'
            )
            BEGIN
                CREATE TABLE {TABLE_NAME} (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    customer_id INT,
                    customer_name NVARCHAR(255),
                    customer_phone NVARCHAR(50),
                    classification NVARCHAR(500),
                    agent_id INT,
                    agent_name NVARCHAR(255),
                    conv_id NVARCHAR(50),
                    resolved_date BIGINT,
                    resolved_time NVARCHAR(20),
                    summary NVARCHAR(MAX),
                    created_at DATETIME DEFAULT GETDATE()
                )
            END
        """)

        cursor.execute(f"""
            IF NOT EXISTS (
                SELECT * FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_NAME = '{CUSTOMER_TABLE}'
            )
            BEGIN
                CREATE TABLE {CUSTOMER_TABLE} (
                    customer_id INT PRIMARY KEY,
                    customer_name NVARCHAR(255),
                    customer_phone NVARCHAR(50)
                )
            END
        """)

        conn.commit()
        conn.close()
        print("✅ DB ready")

    except Exception as e:
        print(f"❌ DB init failed: {str(e)}")


# ---------------- SAVE CUSTOMER ----------------
def save_customer(customer_id, customer_name, customer_phone):
    try:
        conn = pyodbc.connect(DB_CONN_STR)
        cursor = conn.cursor()

        cursor.execute(f"""
            IF NOT EXISTS (
                SELECT 1 FROM {CUSTOMER_TABLE} WHERE customer_id = ?
            )
            BEGIN
                INSERT INTO {CUSTOMER_TABLE} (customer_id, customer_name, customer_phone)
                VALUES (?, ?, ?)
            END
        """, (customer_id, customer_id, customer_name, customer_phone))

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"❌ Customer save failed: {str(e)}")


# ---------------- SAVE TO DB ----------------
def save_to_db(customer_id, customer_name, customer_phone,
               classification, agent_id, agent_name,
               conv_id, resolved_date, resolved_time, summary):

    try:
        conn = pyodbc.connect(DB_CONN_STR)
        cursor = conn.cursor()

        cursor.execute(f"""
            INSERT INTO {TABLE_NAME}
            (customer_id, customer_name, customer_phone, classification,
             agent_id, agent_name, conv_id, resolved_date, resolved_time, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            customer_id,
            customer_name,
            customer_phone,
            classification,
            agent_id,
            agent_name,
            str(conv_id),
            resolved_date,
            resolved_time,
            summary
        ))

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"❌ DB insert failed: {str(e)}")


# ---------------- ARABIC FIX ----------------
def fix_arabic_display(text):
    if not text:
        return text
    try:
        return get_display(arabic_reshaper.reshape(text))
    except:
        return text


# ---------------- PROMPT ----------------
def build_prompt(chat_history):
    return f"""
You are a technical support assistant for monitoring the quality of solutions and the efficiency of the agent.
Return:
الخلاصة + التصنيف فقط (Arabic only)

Chat:
{chat_history}
"""


# ---------------- AI FUNCTIONS ----------------
def try_groq(prompt):
    for i, key in enumerate(GROQ_API_KEYS, 1):
        try:
            client = Groq(api_key=key)
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )
            return res.choices[0].message.content.strip()
        except:
            continue
    return None


def try_gemini(prompt):
    for i, key in enumerate(GEMINI_API_KEYS, 1):
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            return model.generate_content(prompt).text.strip()
        except:
            continue
    return None


def try_cerebras(prompt):
    for i, key in enumerate(CEREBRAS_API_KEYS, 1):
        try:
            client = Cerebras(api_key=key)
            res = client.chat.completions.create(
                model="llama-3.3-70b",
                messages=[{"role": "user", "content": prompt}]
            )
            return res.choices[0].message.content.strip()
        except:
            continue
    return None


# ---------------- MAIN AI ----------------
def analyze_chat(chat_history):
    prompt = build_prompt(chat_history)

    return (
        try_groq(prompt)
        or try_gemini(prompt)
        or try_cerebras(prompt)
        or "ALL PROVIDERS FAILED"
    )


# ---------------- WEBHOOK ----------------
@app.post("/webhook")
async def chatwoot_webhook(request: Request):

    payload = await request.json()
    status = payload.get("status")

    if status == "resolved":

        conv_id = payload.get("id")
        customer_id = payload.get("meta", {}).get("sender", {}).get("id")
        customer_name = payload.get("meta", {}).get("sender", {}).get("name", "Unknown")
        customer_phone = payload.get("meta", {}).get("sender", {}).get("phone_number", "No Phone")

        agent_id = payload.get("meta", {}).get("assignee", {}).get("id")
        agent_name = payload.get("meta", {}).get("assignee", {}).get("name", "Unassigned")

        cairo_tz = timezone(timedelta(hours=3))
        resolved_dt = datetime.now(cairo_tz)

        api_url = f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/conversations/{conv_id}/messages"

        headers = {
            "api_access_token": ACCESS_TOKEN
        }

        try:
            response = requests.get(api_url, headers=headers)

            if response.status_code == 200:

                messages = response.json().get("payload", [])
                chat_text = ""

                for msg in reversed(messages):
                    if msg.get("content"):
                        chat_text += f"{msg.get('content')}\n"

                ai_result = analyze_chat(chat_text)

                save_customer(customer_id, customer_name, customer_phone)

                save_to_db(
                    customer_id,
                    customer_name,
                    customer_phone,
                    "AUTO",
                    agent_id,
                    agent_name,
                    conv_id,
                    int(resolved_dt.strftime("%Y%m%d")),
                    resolved_dt.strftime("%I:%M %p"),
                    ai_result
                )

        except Exception as e:
            print(e)

    return {"status": "success"}


# ---------------- RUN ----------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)