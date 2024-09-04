import logging

from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def hello_world():
    return "hello"

@app.route('/printer')
def printer():
    app.logger.info(request.get_json())
    return request.get_json()
