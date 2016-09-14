from flask import Flask, render_template

from handlers.handler_500px import photos

app = Flask(__name__)

@app.route("/")
def index():
    results = photos(search='greyhound')
    return render_template('index.html', results=results)

if __name__ == "__main__":
    app.run()
