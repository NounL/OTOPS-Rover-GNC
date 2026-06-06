# activate venv: 
# source venv/bin/activate
# deactivate

from flask import Flask, render_template, url_for

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('dash.html')

if __name__ == "__main__":
    app.run(debug=True)