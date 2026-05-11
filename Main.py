from fastapi import FastAPI, Request
import uvicorn
import requests

app = FastAPI()

# --- Configuration ---
CHATWOOT_URL = "company.chatwoot.com"  # Replace with your Chatwoot instance URL
ACCOUNT_ID = "<YOUR_ACCOUNT_ID>"
ACCESS_TOKEN = "<YOUR_ACCESS_TOKEN>"

@app.post("/webhook")
async def chatwoot_webhook(request: Request):
    payload = await request.json()
    
    # 1. Check status
    status = payload.get("status")

    if status == "resolved":
        conv_id = payload.get("id")
        customer_name = payload.get("meta", {}).get("sender", {}).get("name", "Unknown")
        customer_phone = payload.get("meta", {}).get("sender", {}).get("phone_number", "No Phone")
        agent_name = payload.get("meta", {}).get("assignee", {}).get("name", "Unassigned")

        # Your Requested Structure for Printing Customer Info
        print("\n" + "="*50)
        print("🎯 STATUS CHANGED: RESOLVED")
        print(f"👤 Customer  : {customer_name}")
        print(f"📞 Phone     : {customer_phone}")
        print(f"👨‍💻 Agent     : {agent_name}")
        print(f"🆔 Conv ID   : {conv_id}")
        print("-" * 50)

        # 2. Fetch Full Conversation Messages from API (The Working Method)
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
                # Use the flexible parsing logic that worked for you
                messages_list = data.get('payload') if isinstance(data, dict) else data
                
                if messages_list:
                    print("📝 FULL CONVERSATION LOG:")
                    for msg in reversed(messages_list):
                        content = msg.get("content")
                        sender_info = msg.get("sender")
                        s_name = sender_info.get("name") if sender_info else "System"
                        
                        if content:
                            print(f"[{s_name}]: {content}")
                
                print("="*50 + "\n")
            else:
                print(f"❌ API Error: Status {response.status_code}")
        except Exception as e:
            print(f"⚠️ Connection Error: {str(e)}")

    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)