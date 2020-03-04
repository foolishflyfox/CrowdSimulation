from flask import Flask, render_template, request
import os
from xml2json import map_xml2json

app = Flask(__name__, static_url_path='', static_folder='.')

@app.route('/')
def index():
    simulation_path = "./simulations"
    simulations = os.listdir(simulation_path)
    return render_template('./index.html', simulations=simulations)

@app.route('/simulation', methods=['GET'])
def simulation():
    return map_xml2json(request.args['simname'], request.args['showtype'])

app.run(host='0.0.0.0', port=8080, debug=True)

    




