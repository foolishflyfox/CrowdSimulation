import os.path
import xml.dom.minidom
import json
import random
from flask import render_template

from utils import GetLosseMaxRect, GetMaxRect, MaxRectBound

# 将一个 subroom 解析成一个 FuncArea 对象
# subroom 是一个 xml.dom.minidom.Element 类型
def parseSubroom(subroom):
    # 如果属性不存在，getAttribute 返回一个空字符串
    s_subroom_id = subroom.getAttribute('id')
    polygons = subroom.getElementsByTagName('polygon')
    obstacles = subroom.getElementsByTagName('obstacle')
    sub_funcareas = []
    for polygon in polygons:
        t_caption = polygon.getAttribute('caption')
        sub_funcarea = {}
        if(s_subroom_id):
            sub_funcarea['_id'] = int(s_subroom_id)
        sub_funcarea['Wall'] = 'subroom'
        sub_funcarea['Open'] = True
        sub_funcarea['Outline'] = [[]]
        points = []
        vertexs = polygon.getElementsByTagName('vertex')
        for vertex in vertexs:
            points.append(float(vertex.getAttribute('px')))
            points.append(float(vertex.getAttribute('py')))
        sub_funcarea['Outline'][0].append(points)
        sub_funcareas.append(sub_funcarea)
    for obstacle in obstacles:
        json_obstacle = {}
        t_caption = polygon.getAttribute('caption')
        if obstacle.getAttribute('id'):
            json_obstacle['_id'] = int(obstacle.getAttribute('id'))
        if polygon.getAttribute('closed') in ['', '1']:
            json_obstacle['Open'] = False
        else:
            json_obstacle['Open'] = True
        json_obstacle['Outline'] = [[]]
        points = []
        polygons = obstacle.getElementsByTagName('polygon')
        if(len(polygons)==0): continue
        vertexs = polygons[0].getElementsByTagName('vertex')
        for vertex in vertexs:
            points.append(float(vertex.getAttribute('px')))
            points.append(float(vertex.getAttribute('py')))
        json_obstacle['Outline'][0].append(points)
        sub_funcareas.append(json_obstacle)
        
    return sub_funcareas

# crossings 是不同 subroom 之间的通路
def parseCrossings(crossings):
    json_crossings = []
    crossings = crossings.getElementsByTagName('crossing')
    for crossing in crossings:
        json_crossing = {}
        if crossing.getAttribute('id'):
            json_crossing['_id'] = int(crossing.getAttribute('id'))
        json_crossing['Wall'] = 'crossing'
        json_crossing['Open'] = True
        json_crossing['Outline'] = [[]]
        points = []
        vertexs = crossing.getElementsByTagName('vertex')
        for vertex in vertexs:
            points.append(float(vertex.getAttribute('px')))
            points.append(float(vertex.getAttribute('py')))
        json_crossing['Outline'][0].append(points)
        json_crossings.append(json_crossing)
    return json_crossings

# transition 是不同 room 之间的通路
def parseTransitions(transitions):
    json_transitions = []
    transitions = transitions.getElementsByTagName('transition')
    for transition in transitions:
        json_transition = {}
        if transition.getAttribute('id'):
            json_transition['_id'] = int(transition.getAttribute('id'))
        json_transition['Wall'] = 'transition'
        json_transition['Open'] = True
        json_transition['Outline'] = [[]]
        points = []
        vertexs = transition.getElementsByTagName('vertex')
        for vertex in vertexs:
            points.append(float(vertex.getAttribute('px')))
            points.append(float(vertex.getAttribute('py')))
        json_transition['Outline'][0].append(points)
        json_transitions.append(json_transition)
    return json_transitions

def parseGoals(goals):
    json_goals = []
    goals = goals.getElementsByTagName('goal')
    for goal in goals:
        goal_funcarea = {}
        if goal.getAttribute('id'):
            goal_funcarea['_id'] = int(goal.getAttribute('id'))
        if goal.getAttribute('final')=="false": goal_funcarea['Category'] = 2
        else: goal_funcarea['Category'] = 1
        goal_funcarea['Open'] = False
        goal_funcarea['Outline'] = [[]]
        points = []
        polygons = goal.getElementsByTagName('polygon')
        if len(polygons)==0: continue
        polygon = polygons[0]
        for vertex in polygon.getElementsByTagName('vertex'):
            points.append(float(vertex.getAttribute('px')))
            points.append(float(vertex.getAttribute('py')))
        goal_funcarea['Outline'][0].append(points)
        json_goals.append(goal_funcarea)
    return json_goals

def parseTriangulateFile(filepath):
    if not os.path.exists(filepath):
        return []
    json_triangles = []
    edges = set()
    with open(filepath) as f:
        for line in f:
            x1, y1, x2, y2 = [float(s) for s in line.split(' ')]
            if x1 < x2:
                edges.add((x1, y1, x2, y2))
            elif x2 < x1:
                edges.add((x2, y2, x1, y1))
            else:
                if y1 < y2:
                    edges.add((x1, y1, x2, y2))
                else:
                    edges.add((x2, y2, x1, y1))
    for x1,y1,x2,y2 in edges:
        json_triangle = {}
        json_triangle['Wall'] = 'triangle'
        json_triangle['Open'] = True
        json_triangle['Outline'] = [[[x1, y1, x2, y2]]]
        json_triangles.append(json_triangle)
    return json_triangles
    

# 求FuncAreas的外边界
def GetFloorOutline(FuncAreas):
    dots = []
    for FuncArea in FuncAreas:
        # print("funcarea :", FuncArea['Outline'][0][0])
        # print('aaaa:', FuncArea['Outline'][0][0])
        i = 0
        t_outline = FuncArea['Outline'][0][0]
        while i < len(t_outline):
            # dots.append((int(t_outline[i]), int(t_outline[i+1])))
            dots.append((t_outline[i], t_outline[i+1]))
            i += 2
    # result = graham_scan(dots)
    # result = GetLosseMaxRect(dots)
    result = GetMaxRect(dots)

    return result

# 构建 Floor 对象
def CreateFloor(FuncAreas):
    Floor = {"_id":1, "Name":"F1", "High":5, "FuncAreas":[],
        "PubPoint":[]}
    # print(FuncAreas)
    for FuncArea in FuncAreas:
        Floor['FuncAreas'].append(FuncArea)
    Floor['Outline'] = [[GetFloorOutline(Floor['FuncAreas'])]]
    return Floor

# 构建 Building 对象
def CreateBuilding(Floors):
    building = {"Outline":[[[]]]}
    return building

def CreateMapJsonFile(geoxml_path, geojson_path, jupedsim=None):
    result = {'data':{'Floors':[]}}
    Floors = result['data']['Floors']

    dom = xml.dom.minidom.parse(geoxml_path)
    geometry = dom.documentElement
    # 一个 map 只能有一个rooms
    rooms = geometry.getElementsByTagName('rooms')[0]
    room_list = rooms.getElementsByTagName('room')
    
    FuncAreas = []
    for room in room_list:
        subrooms = room.getElementsByTagName('subroom')
        for subroom in subrooms:
            sub_funcareas = parseSubroom(subroom)
            FuncAreas += sub_funcareas
        crossingses = room.getElementsByTagName('crossings')
        for crossings in crossingses:
            json_crossings = parseCrossings(crossings)
            FuncAreas += json_crossings
    transitionses = geometry.getElementsByTagName('transitions')
    for transitions in transitionses:
        json_transitions = parseTransitions(transitions)
        FuncAreas += json_transitions

    # 获取 <routing> 中的 <goal> 信息
    simdir = os.path.dirname(geoxml_path)
    if jupedsim is None:
        inipath = f"{simdir}/ini.xml"
        jupedsim = xml.dom.minidom.parse(inipath).documentElement
    routings = jupedsim.getElementsByTagName('routing')
    for routing in routings:
        goalses = routing.getElementsByTagName('goals')
        for goals in goalses:
            json_goals = parseGoals(goals)
            FuncAreas += json_goals

    # 获取三角形化的信息
    triangles = parseTriangulateFile(f"{simdir}/triangulate_result.txt")
    FuncAreas += triangles

    Floor = CreateFloor(FuncAreas)

    # 调整位置和大小的参数，使显示的场景更加适合界面
    t_left = MaxRectBound(Floor['Outline'][0][0], 'left')
    t_right = MaxRectBound(Floor['Outline'][0][0], 'right')
    t_bottom = MaxRectBound(Floor['Outline'][0][0], 'bottom')
    t_top = MaxRectBound(Floor['Outline'][0][0], 'top')
    xcenter = (t_left+t_right)/2
    ycenter = (t_bottom+t_top)/2
    xlen = (t_right-t_left)
    ylen = (t_top-t_bottom)
    mlen = max(xlen, ylen)
    scale = 2000/mlen
    
    for i in range(len(Floor['FuncAreas'])):
        j = 0
        outline = Floor['FuncAreas'][i]['Outline'][0][0]
        while j+1 < len(outline):
            outline[j] = (outline[j]-xcenter)*scale
            outline[j+1] = (outline[j+1]-ycenter)*scale
            j += 2
    # 扩大Floor的边界
    outline = GetFloorOutline(Floor['FuncAreas'])
    margin_rate = 1.0/20
    for i in range(len(outline)):
        outline[i] *= (1+margin_rate)
    Floor['Outline'][0][0] = outline
    # print(Floor)
    # 调整 Floor 的 High 属性以改变墙的高度
    Floor['High'] = min(xlen, ylen)*scale/50

    Floors.append(Floor)
    result['data']['building'] = CreateBuilding(Floors)
    # print(json.dumps(result, indent=2))
    with open(geojson_path, 'w') as output:
        json.dump(result, output, indent=2)
    

def map_xml2json(simname, showtype=True):
    simdir = f"./simulations/{simname}"
    inipath = f"{simdir}/ini.xml"
    dom = xml.dom.minidom.parse(inipath)
    jupedsim = dom.documentElement
    geometry = jupedsim.getElementsByTagName('geometry')[0]
    geoname_xml = geometry.firstChild.data
    geoname_json = os.path.splitext(geoname_xml)[0]+'.json'
    geoxml_path = f"{simdir}/{geoname_xml}"
    geojson_path = f"{simdir}/{geoname_json}"
    if(not os.path.isfile(geojson_path)):
        CreateMapJsonFile(geoxml_path, geojson_path, jupedsim)
    return render_template('./simulate.html', datafile=geojson_path, showtype=showtype)
    
    


