# main.py
from flask import Flask, request, jsonify
from utils.state import QueryState
from agents.external_agent import ExternalAgent
from agents.internal_agent import InternalAgent

app = Flask(__name__)

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

if __name__ == "__main__":
    app.run(debug=True)