from fastapi import FastAPI
from ..email_action_agent import EmailAgent

app = FastAPI()

@app.post("/send_email")
async def send_email(instruction: str, provider: str = "gmail"):
    agent = EmailAgent(provider)
    agent.send_email(instruction)
    return {"status": "sent"}