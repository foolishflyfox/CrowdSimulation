from flask import Flask, render_template, request
import os
from xml2json import Xml2JsonTranslator

app = Flask(__name__, static_url_path='', static_folder='.')
translator = Xml2JsonTranslator()

@app.route('/')
def index():
    simulation_path = "./simulations"
    simulations = [f for f in os.listdir(simulation_path)
                    if os.path.isdir(f"{simulation_path}/{f}")]
    return render_template('./index.html', simulations=simulations)

@app.route('/simulation', methods=['GET'])
def simulation():
    return translator.map_xml2json(request.args['simname'], request.args['showtype'])

app.run(host='0.0.0.0', port=8080, debug=True)

    




