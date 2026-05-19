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
import pymssql
import os

os.environ['PYTHONUNBUFFERED'] = '1'
# UTF-8 Fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    init_db()

# ---------------- CONFIG ----------------
CHATWOOT_URL = os.getenv("CHATWOOT_URL")
ACCOUNT_ID   = os.getenv("ACCOUNT_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# ---------------- GROQ KEYS ----------------
GROQ_API_KEYS = [
    os.getenv("GROQ_KEY_1"),
    os.getenv("GROQ_KEY_2"),
    os.getenv("GROQ_KEY_3"),
    os.getenv("GROQ_KEY_4"),
    os.getenv("GROQ_KEY_5"),
]

# ---------------- GEMINI KEYS ----------------
GEMINI_API_KEYS = [
    os.getenv("GEMINI_KEY_1"),
    os.getenv("GEMINI_KEY_2"),
    os.getenv("GEMINI_KEY_3"),
    os.getenv("GEMINI_KEY_4"),
    os.getenv("GEMINI_KEY_5"),
]

# ---------------- CEREBRAS KEYS ----------------
CEREBRAS_API_KEYS = [
    os.getenv("CEREBRAS_KEY_1"),
    os.getenv("CEREBRAS_KEY_2"),
    os.getenv("CEREBRAS_KEY_3"),
    os.getenv("CEREBRAS_KEY_4"),
]

# ---------------- DATABASE CONFIG ----------------
DB_SERVER   = os.getenv("DB_SERVER")
DB_NAME     = os.getenv("DB_NAME")
DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT     = int(os.getenv("DB_PORT", "1433"))

TABLE_NAME     = "Customer_service_reports_by_A"
CUSTOMER_TABLE = "customer_detail_by_A"


# ---------------- CREATE TABLES IF NOT EXISTS ----------------
def init_db():
    try:
        conn = pymssql.connect(server=DB_SERVER, user=DB_USER, password=DB_PASSWORD, database=DB_NAME, port=DB_PORT, tds_version="4.2", charset="UTF-8")
        cursor = conn.cursor()

        cursor.execute(f"""
            IF NOT EXISTS (
                SELECT * FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_NAME = '{TABLE_NAME}'
            )
            BEGIN
                CREATE TABLE {TABLE_NAME} (
                    id               INT IDENTITY(1,1) PRIMARY KEY,
                    customer_id      INT,
                    customer_name    NVARCHAR(255),
                    customer_phone   NVARCHAR(50),
                    classification   NVARCHAR(500),
                    agent_id         INT,
                    agent_name       NVARCHAR(255),
                    conv_id          NVARCHAR(50),
                    resolved_date    BIGINT,
                    resolved_time    NVARCHAR(20),
                    summary          NVARCHAR(MAX),
                    created_at       DATETIME DEFAULT GETDATE()
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
                    customer_id    INT PRIMARY KEY,
                    customer_name  NVARCHAR(255),
                    customer_phone NVARCHAR(50)
                )
            END
        """)

        conn.commit()
        conn.close()
        print(f"✅ DB ready — tables '{TABLE_NAME}' & '{CUSTOMER_TABLE}' exist or just created")
    except Exception as e:
        print(f"❌ DB init failed: {str(e)}")


# ---------------- SAVE CUSTOMER (مرة واحدة بس) ----------------
def save_customer(customer_id, customer_name, customer_phone):
    try:
        conn = pymssql.connect(server=DB_SERVER, user=DB_USER, password=DB_PASSWORD, database=DB_NAME, port=DB_PORT, tds_version="4.2", charset="UTF-8")
        cursor = conn.cursor()
        cursor.execute(f"""
            IF NOT EXISTS (
                SELECT 1 FROM {CUSTOMER_TABLE} WHERE customer_id = %d
            )
            BEGIN
                INSERT INTO {CUSTOMER_TABLE} (customer_id, customer_name, customer_phone)
                VALUES (%d, %s, %s)
            END
        """, (customer_id, customer_id, customer_name, customer_phone))
        conn.commit()
        conn.close()
        print(f"✅ Customer check done — id: {customer_id}")
    except Exception as e:
        print(f"❌ Customer save failed: {str(e)}")


# ---------------- INSERT RECORD ----------------
def save_to_db(customer_id, customer_name, customer_phone, classification, agent_id, agent_name, conv_id, resolved_date, resolved_time, summary):
    try:
        conn = pymssql.connect(server=DB_SERVER, user=DB_USER, password=DB_PASSWORD, database=DB_NAME, port=DB_PORT, tds_version="4.2", charset="UTF-8")
        cursor = conn.cursor()
        cursor.execute(f"""
            INSERT INTO {TABLE_NAME}
                (customer_id, customer_name, customer_phone, classification, agent_id, agent_name, conv_id, resolved_date, resolved_time, summary)
            VALUES (%d, %s, %s, %s, %d, %s, %s, %d, %s, %s)
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
        print(f"✅ Record saved to DB — conv_id: {conv_id} | customer_id: {customer_id}")
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
If there are any spelling mistakes in the writing, you can overlook them. Just make sure the issue has been resolved or not.
If more than one issue has been resolved, write them all.
You are receiving a chat from the ChatWoot platform.

You MUST respond in EXACTLY this format — no extra text before or after:
You are required to enter correct and fluent Arabic.
الخلاصة: وصف تفصيلي للمشكلة بناءً على تاريخ المحادثة.
التصنيف: تم حل مشكلة:ملخص المشكله / لم يتم حل مشكلة:ملخص المشكله / العميل لا يرد / سيتم التواصل مع العميل قريباً(من خلال كلام العميل او مهندس الدعم) / لم يتم تعريف مشكلة / لم يتم تعريف حل

Rules:
- الخلاصة: must be a detailed description of the problem using the chat history (Never summarize welcome messages, agent assignments, or review or reopen conversations; instead, include only the actual transcript of the conversation between the client and the agent. Strive to be as concise as possible, but never compromise on accuracy, clarity, and comprehensiveness.).
- التصنيف: pick the most accurate category based on the chat.
- Always write in Arabic.
- Do NOT add any extra lines or explanations outside the two lines above.

Chat:
{chat_history}
"""


# ---------------- PARSE AI RESULT ----------------
def parse_ai_result(raw_text):
    summary = ""
    classification = ""
    try:
        for line in raw_text.splitlines():
            line = line.strip()
            if line.startswith("الخلاصة:"):
                summary = line.replace("الخلاصة:", "").strip()
            elif line.startswith("التصنيف:"):
                classification = line.replace("التصنيف:", "").strip()
    except Exception:
        summary = raw_text
        classification = "غير محدد"

    if not summary:
        summary = raw_text
    if not classification:
        classification = "غير محدد"

    return summary, classification


# ---------------- GROQ ----------------
def try_groq(prompt):
    for i, key in enumerate(GROQ_API_KEYS, 1):
        if not key:
            continue
        try:
            print(f"🔄 Groq key {i}/{len(GROQ_API_KEYS)}...")
            client = Groq(api_key=key)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            result = response.choices[0].message.content.strip()
            print(f"✅ Groq key {i} success")
            return result
        except Exception as e:
            print(f"❌ Groq key {i} failed: {str(e)}")
            continue
    return None


# ---------------- GEMINI ----------------
def try_gemini(prompt):
    for i, key in enumerate(GEMINI_API_KEYS, 1):
        if not key:
            continue
        try:
            print(f"🔄 Gemini key {i}/{len(GEMINI_API_KEYS)}...")
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            result = response.text.strip()
            print(f"✅ Gemini key {i} success")
            return result
        except Exception as e:
            print(f"❌ Gemini key {i} failed: {str(e)}")
            continue
    return None


# ---------------- CEREBRAS ----------------
def try_cerebras(prompt):
    for i, key in enumerate(CEREBRAS_API_KEYS, 1):
        if not key:
            continue
        try:
            print(f"🔄 Cerebras key {i}/{len(CEREBRAS_API_KEYS)}...")
            client = Cerebras(api_key=key)
            response = client.chat.completions.create(
                model="llama-3.3-70b",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            result = response.choices[0].message.content.strip()
            print(f"✅ Cerebras key {i} success")
            return result
        except Exception as e:
            print(f"❌ Cerebras key {i} failed: {str(e)}")
            continue
    return None


# ---------------- MAIN AI FUNCTION ----------------
def analyze_chat(chat_history):
    print("\n--- AI Analysis Start ---")
    prompt = build_prompt(chat_history)

    print("\n[1] Trying Groq...")
    result = try_groq(prompt)
    if result:
        return result

    print("\n[2] Groq exhausted → Trying Gemini...")
    result = try_gemini(prompt)
    if result:
        return result

    print("\n[3] Gemini exhausted → Trying Cerebras...")
    result = try_cerebras(prompt)
    if result:
        return result

    print("\n❌ All AI providers exhausted")
    return "الخلاصة: تم انتهاء جميع الـ API keys المعرفة ولم يتم التحليل\nالتصنيف: تم حل المشكلة"


@app.get("/health")
async def health_check():
    return {"status": "alive"}


# ---------------- WEBHOOK ----------------
@app.post("/webhook")
async def chatwoot_webhook(request: Request):

    payload = await request.json()
    status = payload.get("status")

    if status == "resolved":

        conv_id        = payload.get("id")
        customer_id    = payload.get("meta", {}).get("sender", {}).get("id")
        customer_name  = payload.get("meta", {}).get("sender", {}).get("name", "Unknown")
        customer_phone = payload.get("meta", {}).get("sender", {}).get("phone_number", "No Phone")
        agent_id       = payload.get("meta", {}).get("assignee", {}).get("id")
        agent_name     = payload.get("meta", {}).get("assignee", {}).get("name", "Unassigned")

        cairo_tz = timezone(timedelta(hours=3))

        resolved_at_raw = payload.get("resolved_at") or payload.get("updated_at")
        if resolved_at_raw:
            try:
                resolved_dt = datetime.fromtimestamp(int(resolved_at_raw), tz=cairo_tz)
            except Exception:
                try:
                    resolved_dt = datetime.fromisoformat(str(resolved_at_raw).replace("Z", "+00:00")).astimezone(cairo_tz)
                except Exception:
                    resolved_dt = datetime.now(cairo_tz)
        else:
            resolved_dt = datetime.now(cairo_tz)

        resolved_date = int(resolved_dt.strftime("%Y%m%d"))
        resolved_time = resolved_dt.strftime("%I:%M %p")

        print("\n" + "="*50)
        print(fix_arabic_display("🎯 STATUS: RESOLVED"))
        print(f"🪪 Customer ID: {customer_id}")
        print(f"👤 Customer : {customer_name}")
        print(f"📞 Phone    : {customer_phone}")
        print(f"🪪 Agent ID  : {agent_id}")
        print(f"👨‍💻 Agent    : {agent_name}")
        print(f"🆔 Conv ID   : {conv_id}")
        print(f"📅 Date      : {resolved_date}")
        print(f"🕐 Time      : {resolved_time}")

        api_url = f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/conversations/{conv_id}/messages"

        headers = {
            "api_access_token": ACCESS_TOKEN,
            "api-access-token": ACCESS_TOKEN,
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(api_url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                messages_list = data.get('payload') if isinstance(data, dict) else data

                full_chat_text = ""

                if messages_list:
                    for msg in reversed(messages_list):
                        content = msg.get("content")
                        sender  = msg.get("sender")
                        s_name  = sender.get("name") if sender else "System"

                        if content:
                            full_chat_text += f"[{s_name}]: {content}\n"

                    ai_raw = analyze_chat(full_chat_text)
                    summary, classification = parse_ai_result(ai_raw)

                    print(f"📋 الخلاصة    : {summary}")
                    print(f"🏷️  التصنيف    : {classification}")
                    print("="*50 + "\n")

                    save_customer(
                        customer_id=customer_id,
                        customer_name=customer_name,
                        customer_phone=customer_phone
                    )

                    save_to_db(
                        customer_id=customer_id,
                        customer_name=customer_name,
                        customer_phone=customer_phone,
                        classification=classification,
                        agent_id=agent_id,
                        agent_name=agent_name,
                        conv_id=conv_id,
                        resolved_date=resolved_date,
                        resolved_time=resolved_time,
                        summary=summary
                    )

            else:
                print(f"❌ Chatwoot API Error: {response.status_code}")

        except Exception as e:
            print("⚠️ Error:", str(e))

    return {"status": "success"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)