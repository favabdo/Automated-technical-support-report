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


# UTF-8 Fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


app = FastAPI()


# ---------------- CONFIG ----------------
CHATWOOT_URL = "<YOUR_CHATWOOT_INSTANCE_URL>"  # e.g. https://company.chatwoot.com
ACCOUNT_ID = "<YOUR_ACCOUNT_ID>"              # Chatwoot Account ID
ACCESS_TOKEN = "<YOUR_ACCESS_TOKEN>"          # Chatwoot API token (read permissions required)


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

Return:
- "Resolved" or "Not Resolved"
- Arabic summary:
  'تم حل مشكلة...' or 'لم يتم حل مشكلة...'

If unclear, classify as:
"لم يتم تعريف مشكله" or "سيتم التواصل مع العميل قريبا"

Chat:
{chat_history}
"""


# ---------------- AI PROVIDERS ----------------
def try_groq(prompt):
    for i, key in enumerate(GROQ_API_KEYS, 1):
        try:
            print(f"🔄 Groq key {i}...")
            client = Groq(api_key=key)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except:
            continue
    return None


def try_gemini(prompt):
    for i, key in enumerate(GEMINI_API_KEYS, 1):
        try:
            print(f"🔄 Gemini key {i}...")
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            return model.generate_content(prompt).text.strip()
        except:
            continue
    return None


def try_cerebras(prompt):
    for i, key in enumerate(CEREBRAS_API_KEYS, 1):
        try:
            print(f"🔄 Cerebras key {i}...")
            client = Cerebras(api_key=key)
            response = client.chat.completions.create(
                model="llama-3.3-70b",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except:
            continue
    return None


# ---------------- MAIN AI ----------------
def analyze_chat(chat_history):

    prompt = build_prompt(chat_history)

    print("[1] Groq...")
    result = try_groq(prompt)
    if result:
        return result

    print("[2] Gemini...")
    result = try_gemini(prompt)
    if result:
        return result

    print("[3] Cerebras...")
    result = try_cerebras(prompt)
    if result:
        return result

    return "⚠️ All AI providers failed"


# ---------------- WEBHOOK ----------------
@app.post("/webhook")
async def chatwoot_webhook(request: Request):

    payload = await request.json()
    status = payload.get("status")

    if status == "resolved":

        conv_id = payload.get("id")

        customer_name = payload.get("meta", {}).get("sender", {}).get("name", "Unknown")
        customer_phone = payload.get("meta", {}).get("sender", {}).get("phone_number", "No Phone")
        agent_name = payload.get("meta", {}).get("assignee", {}).get("name", "Unassigned")

        cairo_tz = timezone(timedelta(hours=3))

        resolved_dt = datetime.now(cairo_tz)

        print("\n==============================")
        print("🎯 RESOLVED")
        print("Customer:", customer_name)
        print("Phone:", customer_phone)
        print("Agent:", agent_name)
        print("Conv ID:", conv_id)

        api_url = f"{CHATWOOT_URL}/api/v1/accounts/{ACCOUNT_ID}/conversations/{conv_id}/messages"

        headers = {
            "api_access_token": ACCESS_TOKEN,
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(api_url, headers=headers)

            if response.status_code == 200:

                messages = response.json().get("payload", [])

                full_chat = ""

                for msg in reversed(messages):
                    content = msg.get("content")
                    sender = msg.get("sender")
                    name = sender.get("name") if sender else "System"

                    if content:
                        full_chat += f"[{name}]: {content}\n"

                ai_result = analyze_chat(full_chat)

                print("🤖 RESULT:", ai_result)

        except Exception as e:
            print("ERROR:", str(e))

    return {"status": "success"}


# ---------------- RUN ----------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)