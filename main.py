# main.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from utils.state import QueryState
from agents.external_agent import ExternalAgent
from agents.internal_agent import InternalAgent

app = Flask(__name__)
CORS(app, origins="*")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    state = QueryState(data["role"], data["mode"], data["query"])
    if state.mode == "external":
        agent = ExternalAgent(state)
    else:
        agent = InternalAgent(state)
    response = agent.get_response()
    return jsonify({"response": response})

@app.get("/health")
def health():
    return jsonify({"status": "Running"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)