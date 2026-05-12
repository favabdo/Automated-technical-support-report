from fastapi import FastAPI, Request
import uvicorn
import requests
import sys
import io
import arabic_reshaper
from bidi.algorithm import get_display

# 1. Force Terminal to use UTF-8 Encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

app = FastAPI()


# --- Configuration ---
CHATWOOT_URL = "company.chatwoot.com"  # Replace with your Chatwoot instance URL
ACCOUNT_ID = "<YOUR_ACCOUNT_ID>"      # Replace with your Chatwoot Account ID
ACCESS_TOKEN = "<YOUR_ACCESS_TOKEN>"    # Replace with your Chatwoot API Access Token (must have read permissions)

def fix_arabic_display(text):
    """Function to fix Arabic text shaping and direction for Terminal"""
    if not text:
        return text
    try:
        # Reshape (connect letters) + Bidi (right-to-left direction)
        reshaped_text = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped_text)
        return bidi_text
    except Exception:
        return text

@app.post("/webhook")
async def chatwoot_webhook(request: Request):
    payload = await request.json()
    
    # Check status
    status = payload.get("status")

    if status == "resolved":
        conv_id = payload.get("id")
        customer_name = payload.get("meta", {}).get("sender", {}).get("name", "Unknown")
        customer_phone = payload.get("meta", {}).get("sender", {}).get("phone_number", "No Phone")
        agent_name = payload.get("meta", {}).get("assignee", {}).get("name", "Unassigned")

        # Basic Info Display with Arabic Support
        print("\n" + "="*50)
        print(fix_arabic_display("🎯 STATUS CHANGED: تم الحل (RESOLVED)"))
        print(f"{fix_arabic_display('👤 Customer')}  : {fix_arabic_display(customer_name)}")
        print(f"{fix_arabic_display('📞 Phone')}     : {customer_phone}")
        print(f"{fix_arabic_display('👨‍💻 Agent')}     : {fix_arabic_display(agent_name)}")
        print(f"🆔 Conv ID    : {conv_id}")
        print("-" * 50)

        # API Request for Full Conversation
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
                
                if messages_list:
                    print(fix_arabic_display("📝 FULL CONVERSATION LOG (سجل المحادثة):"))
                    for msg in reversed(messages_list):
                        content = msg.get("content")
                        sender_info = msg.get("sender")
                        s_name = sender_info.get("name") if sender_info else "System"
                        
                        if content:
                            # Process full line for Arabic display
                            full_line = f"[{s_name}]: {content}"
                            print(fix_arabic_display(full_line))
                
                print("="*50 + "\n")
            else:
                print(f"❌ API Error: Status {response.status_code}")
        except Exception as e:
            print(f"⚠️ Connection Error: {str(e)}")

    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)