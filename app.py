from flask import Flask, render_template, jsonify
import os

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/game-info")
def game_info():
    return jsonify({
        "name": "Nightfall: Dead Ground",
        "version": "1.0.0",
        "status": "online"
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
