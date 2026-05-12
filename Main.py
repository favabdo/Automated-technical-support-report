from fastapi import FastAPI, Request
import uvicorn
import requests
import sys
import io
import arabic_reshaper
from bidi.algorithm import get_display
import google.generativeai as genai

# UTF-8 Fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

app = FastAPI()

# ---------------- CONFIG ----------------
CHATWOOT_URL = "company.chatwoot.com"  # Replace with your Chatwoot instance URL
ACCOUNT_ID = "<YOUR_ACCOUNT_ID>"      # Replace with your Chatwoot Account ID
ACCESS_TOKEN = "<YOUR_ACCESS_TOKEN>"    # Replace with your Chatwoot API Access Token (must have read permissions)

GOOGLE_API_KEYS = [
    "<YOUR_GOOGLE_API_KEY_1>",
    "<YOUR_GOOGLE_API_KEY_2>",
    "<YOUR_GOOGLE_API_KEY_3>"
]

# ---------------- ARABIC FIX ----------------
def fix_arabic_display(text):
    if not text:
        return text
    try:
        return get_display(arabic_reshaper.reshape(text))
    except:
        return text


# ---------------- GEMINI AI ----------------
def analyze_with_gemini(chat_history):

    print("\n--- Gemini Start ---")

    api_key_used = None

    # اختيار أول key شغال
    for key in GOOGLE_API_KEYS:
        try:
            genai.configure(api_key=key)
            api_key_used = key
            print("✅ API Key OK")
            break
        except Exception as e:
            print("❌ Key failed:", str(e))

    if not api_key_used:
        return "No valid API key"

    prompt = f"""
You are a technical support assistant for monitoring the quality of solutions and the efficiency of the agent. 
If there are any spelling mistakes in the writing, you can overlook them. Just make sure the issue has been resolved or not. 
If more than one issue has been resolved, write them all. 
You are receiving a chat from the ChatWoot platform.
 We need to know the chat summary in terms of the status: was the issue resolved or not, and what type of issue it was.
   Return two things to me: "Resolved" or "Not Resolved." Return the summary as follows:
'تم حل مشكلة...' or 'لم يتم حل مشكلة...'

Chat:
{chat_history}
"""

    try:
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        response = model.generate_content(prompt)

        if response and hasattr(response, "text"):
            print("✅ Gemini Success")
            return response.text.strip()

        return "Empty response"

    except Exception as e:
        print("❌ Primary error:", str(e))

        # fallback
        try:
            print("🔄 Fallback model...")

            model = genai.GenerativeModel('models/gemini-1.5-pro')
            response = model.generate_content(prompt)

            return response.text.strip()

        except Exception as e2:
            print("❌ Fallback error:", str(e2))
            return f"Error in AI: {str(e)}"


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

        print("\n" + "="*50)
        print(fix_arabic_display("🎯 STATUS: RESOLVED"))
        print(f"{fix_arabic_display('👤 Customer')} : {customer_name}")
        print(f"{fix_arabic_display('📞 Phone')}    : {customer_phone}")
        print(f"{fix_arabic_display('👨‍💻 Agent')}    : {agent_name}")
        print(f"🆔 Conv ID   : {conv_id}")
        print("-"*50)

        # ---------------- CHATWOOT API (UNCHANGED AS YOU WANTED) ----------------
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
                    print(fix_arabic_display("📝 CHAT LOG:"))

                    for msg in reversed(messages_list):
                        content = msg.get("content")
                        sender = msg.get("sender")

                        s_name = sender.get("name") if sender else "System"

                        if content:
                            line = f"[{s_name}]: {content}"
                            print(fix_arabic_display(line))
                            full_chat_text += line + "\n"

                    print("-"*50)

                    # ---------------- AI ----------------
                    ai_result = analyze_with_gemini(full_chat_text)

                    print(fix_arabic_display(f"🤖 الخلاصة: {ai_result}"))

            else:
                print(f"❌ Chatwoot API Error: {response.status_code}")
                print(response.text)

        except Exception as e:
            print("⚠️ Error:", str(e))

    return {"status": "success"}


# ---------------- RUN ----------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)