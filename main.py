# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from utils.state import QueryState
from agents.external_agent import ExternalAgent
from agents.internal_agent import InternalAgent

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    role: str
    mode: str
    query: str

@app.post("/chat")
def chat(payload: ChatRequest):
    state = QueryState(payload.role, payload.mode, payload.query)
    if state.mode == "external":
        agent = ExternalAgent(state)
    else:
        agent = InternalAgent(state)
    response = agent.get_response()
    return {"response": response}

@app.get("/health")
def health():
    return {"status": "Running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)