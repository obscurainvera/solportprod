from flask import Flask

from app import create_app

app = Flask(__name__)

@app.route('/')
def hello():
    app = create_app()
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)