from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import urllib3
import re
import os
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
CORS(app)

# Fallback basic API file. Operations have been moved to Bot.
@app.route('/', methods=['GET'])
def index():
    return "API is running"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
