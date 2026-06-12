# activate venv: 
# source venv/bin/activate
# deactivate

# Follow the documentation to figure this out:
# https://flask-socketio.readthedocs.io/en/latest/getting_started.html

# https://www.youtube.com/watch?v=mkXdvs8H7TA

# Go through this example: https://medium.com/the-research-nest/how-to-log-data-in-real-time-on-a-web-page-using-flask-socketio-in-python-fb55f9dad100
# in a seperate file will have a thread that sends the data here, this file accesses that data and puts on webpage

# Architechture: 
# Rover runs a server file which sends the data
# This webpage is a client only, only recieves that data, refreshing the ui each
# time new data received

# Need to set up, rover side server
# updating ui for the recieved data + work out logging info

from flask import Flask, render_template, url_for
from flask_socketio import SocketIO, send, emit
import time
import threading
from threading import Lock

app = Flask(__name__)
# app.config['SECRET'] = "secret!"
# socketio = SocketIO(app, cors_allowed_origins="*")
# thread = None
# thread_lock = Lock()

# def background_thread():
#     """Example of how to send server generated events to clients."""
#     count = 0
#     while True:
#         data = "chicken" 
#         socketio.emit("telemetry", data)
#         #time.sleep(0.1)
#         socketio.sleep(3)
        # count += 1
        # price = ((requests.get(url)).json())['data']['amount']
        # socketio.emit('my_response',
        #               {'data': 'Bitcoin current price (USD): ' + price, 'count': count})

# Receiving data, can then send this data on the webpage
# @socketio.on('message')
# def handle_message(data):
#     print('received message: ' + data)

@app.route('/')
def index():
    return render_template('dash.html')

if __name__ == "__main__":
    app.run(debug=True)
    #socketio.run(app, debug=True)