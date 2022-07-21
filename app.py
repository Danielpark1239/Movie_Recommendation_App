from flask import Flask, render_template
import requests
import json

app = Flask(__name__)

@app.route('/')
def get_recs():
    return render_template('index.html')