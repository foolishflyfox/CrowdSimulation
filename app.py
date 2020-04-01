from flask import Flask, render_template, request
import os
import _thread
from flask_socketio import SocketIO, emit

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

# app.run(host='0.0.0.0', port=8080, debug=True)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# 前端 js 调用 io.connect 后发送, io.connect 返回值为websocket对象
# 连接时间处理函数可以返回 False 以拒绝连接
@socketio.on('connect')
def client_connect():
    print('client connect')

@socketio.on('disconnect')
def client_disconnect():
    print('client disconnect')

# 对应前端 socket.send('xxxx')
@socketio.on('message')
def handle_message(message):
    print('received message: ' + message)

# 对应前端 socket.emit('my event', json_obj)
@socketio.on('sim_event')
def handle_my_custom_event(event):
    print('client event: ' + str(event))
    if(event['name']=='load_agents'):
        web_agents= scene_manager.GetAgents()
        emit('load_agents', web_agents)
    elif(event['name']=='load_route'):
        web_route = scene_manager.GetRoute()
        emit('load_route', web_route)
    elif(event['name']=='start_sim'):
        # scene_manager.interval = event['interval']
        scene_manager.StartSimulate(event['interval'], socketio)
    elif(event['name']=='pause_sim'):
        scene_manager.PauseSimulate()

# 调试程序，查看行人信息
@socketio.on('debug_event')
def handle_debug_request(event):
    if(event['name']=='grid_info'):
        grid_info = scene_manager.DebugGridInfo()
        emit('grid_info', grid_info)

# 该函数调用将会被阻塞直到按下 Ctrl+C
socketio.run(app, host='0.0.0.0', port=8080, debug=False)

print("Web App Closed")

