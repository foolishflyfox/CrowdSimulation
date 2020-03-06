from flask import Flask, render_template, request
import os
import _thread
from xml2json import Xml2JsonTranslator
from pysim.SceneManager import SceneManager

app = Flask(__name__, static_url_path='', static_folder='.')

scene_manager = SceneManager()
translator = Xml2JsonTranslator(scene_manager)

@app.route('/')
def index():
    simulation_path = "./simulations"
    simulations = [f for f in os.listdir(simulation_path)
                    if os.path.isdir(f"{simulation_path}/{f}")]
    return render_template('./index.html', simulations=simulations)

@app.route('/simulation', methods=['GET'])
def simulation():
    sim_page = translator.map_xml2json(request.args['simname'], request.args['showtype'])
    _thread.start_new_thread(scene_manager.SceneInit, tuple())
    return sim_page

app.run(host='0.0.0.0', port=8080, debug=True)





