import os.path
import xml.dom.minidom
import json
import random
from flask import render_template

from pysim.utils import *
from pysim.SceneManager import SceneManager

class Xml2JsonTranslator:
    def __init__(self, scene_manager):
        self.wall_id = 1
        self.floorwall_thickness = 0.8
        self.roomwall_thickness = 0.4
        self.scene_manager = scene_manager
    
    # wall 是一个 xml.dom.minidom.Element 类型
    def parseRoomWall(self, wall):
        funcareas = []
        cur_thickness = self.roomwall_thickness
        if wall.getAttribute('thickness')!='':
            cur_thickness = float(wall.getAttribute('thickness'))
        vertexs = []
        for tv in wall.getElementsByTagName('vertex'):
            px = float(tv.getAttribute('px'))
            py = float(tv.getAttribute('py'))
            vertexs.append((px, py))
        
        for i in range(1, len(vertexs)):
            wall_obj = {'id': self.wall_id}
            self.wall_id += 1
            wall_obj['thickness'] = cur_thickness
            wall_obj['Open'] = False
            wall_obj['type'] = "roomwall"
            p1 = vertexs[i-1]
            p2 = vertexs[i]
            normal_unit_v = UnitNormalVector(p1, p2)
            dv = tuple(v * cur_thickness / 2.0 for v in normal_unit_v)
            points = [
                p1[0]+dv[0], p1[1]+dv[1],
                p2[0]+dv[0], p2[1]+dv[1],
                p2[0]-dv[0], p2[1]-dv[1],
                p1[0]-dv[0], p1[1]-dv[1]
            ]
            wall_obj['Outline'] = [[points]]
            funcareas.append(wall_obj)
        return funcareas

    # crossings 是不同 subroom 之间的通路
    def parseCrossing(self, crossing):
        json_crossing = {'Wall': 'crossing', 'Open': True}
        json_crossing['Outline'] = [[[]]]
        for tv in crossing.getElementsByTagName('vertex'):
            px = float(tv.getAttribute('px'))
            py = float(tv.getAttribute('py'))
            json_crossing['Outline'][0][0].append(px)
            json_crossing['Outline'][0][0].append(py)
        return json_crossing

    def parseObstacle(self, obstacle):
        json_obstacle = {}
        json_obstacle['Open'] = False
        points = []
        for vertex in obstacle.getElementsByTagName('vertex'):
            points.append(float(vertex.getAttribute('px')))
            points.append(float(vertex.getAttribute('py')))
        json_obstacle['type'] = "obstacle"
        json_obstacle['Outline'] = [[points]]
        return json_obstacle

    # tag: 解析 xml 中的 outwall
    def parseOutwall(self, outwall):
        funcareas = []
        cur_thickness = self.floorwall_thickness
        xml_obj = outwall.firstChild
        floor_outline = [(float('inf'), float('inf'))]
        wall_obstacles = []
        while xml_obj:
            if xml_obj.nodeName == 'wall':
                wall = xml_obj
                if wall.getAttribute('thickness')!='':
                    cur_thickness = float(wall.getAttribute('thickness'))
                else:
                    cur_thickness = self.floorwall_thickness
                vertexs = []
                for tv in wall.getElementsByTagName('vertex'):
                    px = float(tv.getAttribute('px'))
                    py = float(tv.getAttribute('py'))
                    vertexs.append((px, py))
                    if (px, py) != floor_outline[-1]:
                        floor_outline.append((px, py))
                for i in range(1, len(vertexs)):
                    wall_obj = {'id': self.wall_id}
                    self.wall_id += 1
                    wall_obj['thickness'] = cur_thickness
                    wall_obj['Open'] = False
                    wall_obj['type'] = 'outwall'
                    p1 = vertexs[i-1]
                    p2 = vertexs[i]
                    normal_unit_v = UnitNormalVector(p1, p2)
                    dv = tuple(v * cur_thickness / 2.0 for v in normal_unit_v)
                    points = [
                        p1[0]+dv[0], p1[1]+dv[1],
                        p2[0]+dv[0], p2[1]+dv[1],
                        p2[0]-dv[0], p2[1]-dv[1],
                        p1[0]-dv[0], p1[1]-dv[1]
                    ]
                    wall_obstacles.append((p1[0]+dv[0], p1[1]+dv[1]))
                    wall_obstacles.append((p2[0]+dv[0], p2[1]+dv[1]))
                    wall_obstacles.append((p1[0]-dv[0], p1[1]-dv[1]))
                    wall_obstacles.append((p2[0]-dv[0], p2[1]-dv[1]))
                    wall_obj['Outline'] = [[points]]
                    funcareas.append(wall_obj)
            elif xml_obj.nodeName == 'transition':
                transition = xml_obj
                json_transition = {'Wall': 'transition', 'Open': True}
                json_transition['Outline'] = [[[]]]
                for tv in transition.getElementsByTagName('vertex'):
                    px = float(tv.getAttribute('px'))
                    py = float(tv.getAttribute('py'))
                    json_transition['Outline'][0][0].append(px)
                    json_transition['Outline'][0][0].append(py)
                    if (px, py) != floor_outline[-1]:
                        floor_outline.append((px, py))
                funcareas.append(json_transition)
            xml_obj = xml_obj.nextSibling
        del floor_outline[0]
        self.scene_manager.SetFloorOutline(floor_outline)
        self.scene_manager.AddObstacleOutlines(wall_obstacles)
        return funcareas

    def parseGoals(self, goals):
        json_goals = []
        goals = goals.getElementsByTagName('goal')
        for goal in goals:
            goal_funcarea = {}
            if goal.getAttribute('id'):
                goal_funcarea['_id'] = int(goal.getAttribute('id'))
            if goal.getAttribute('final')=="false":
                goal_funcarea['type'] = 'mid_goal'
            else: 
                goal_funcarea['type'] = 'final_goal'
            goal_funcarea['Open'] = False
            goal_funcarea['Outline'] = [[]]
            points = []
            for vertex in goal.getElementsByTagName('vertex'):
                points.append(float(vertex.getAttribute('px')))
                points.append(float(vertex.getAttribute('py')))
            goal_funcarea['Outline'][0].append(points)
            json_goals.append(goal_funcarea)
        return json_goals

    # 求FuncAreas的外边界
    def GetFloorOutline(self, FuncAreas):
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
    def CreateFloor(self, FuncAreas):
        Floor = {"_id":1, "Name":"F1", "High":5, "FuncAreas":[],
            "PubPoint":[]}
        # print(FuncAreas)
        for FuncArea in FuncAreas:
            Floor['FuncAreas'].append(FuncArea)
        Floor['Outline'] = [[self.GetFloorOutline(Floor['FuncAreas'])]]
        return Floor

    # 构建 Building 对象
    def CreateBuilding(self, Floors):
        building = {"Outline":[[[]]]}
        return building

    # tag: 解析 xml 中的 agents
    def parseAgents(self, agents):
        agents_config = {
            'custom': [],
            'room': [],
            'floor': []
        }
        # 解析手动设置的agent
        customs = agents.getElementsByTagName('custom')
        for custom in customs:
            for vertex in custom.getElementsByTagName('vertex'):
                px = float(vertex.getAttribute('px'))
                py = float(vertex.getAttribute('py'))
                agents_config['custom'].append((px, py))
        return agents_config

    def CreateMapJsonFile(self, inipath, outpath):
        result = {'data':{'Floors':[]}}
        Floors = result['data']['Floors']

        dom = xml.dom.minidom.parse(inipath)
        sim = dom.documentElement
        geometry = sim.getElementsByTagName('geometry')[0]
        
        if len(sim.getElementsByTagName('scene')):
            scene = sim.getElementsByTagName('scene')[0]
            if len(scene.getElementsByTagName('floorwall')):
                floorwall = scene.getElementsByTagName('floorwall')[0]
                s = floorwall.getAttribute('thickness')
                if s!='': self.floorwall_thickness = float(s)
            if len(scene.getElementsByTagName('roomwall')):
                roomwall = scene.getElementsByTagName('roomwall')[0]
                s = roomwall.getAttribute('thickness')
                if s!='': self.roomwall_thickness = float(s)

        if len(sim.getElementsByTagName('parameters')):
            parameter = sim.getElementsByTagName('parameters')[0]
            if len(parameter.getElementsByTagName('gridsize')):
                gridsize = parameter.getElementsByTagName('gridsize')[0]
                s_size = gridsize.getAttribute('value')
                if s_size:
                    self.scene_manager.SetGridSize(float(s_size))
        
        floor = geometry.getElementsByTagName('floor')[0]

        FuncAreas = []

        for room in floor.getElementsByTagName('room'):
            walls = room.getElementsByTagName('wall')
            for wall in walls:
                wall_funcareas = self.parseRoomWall(wall)
                FuncAreas += wall_funcareas
            crossings = room.getElementsByTagName('crossing')
            for crossing in crossings:
                json_crossing = self.parseCrossing(crossing)
                FuncAreas.append(json_crossing)

        for obstacle in floor.getElementsByTagName('obstacle'):
            json_obstacle = self.parseObstacle(obstacle)
            FuncAreas.append(json_obstacle)

        FuncAreas += self.parseOutwall(floor.getElementsByTagName('outwall')[0])

        goalses = floor.getElementsByTagName('goals')
        for goals in goalses:
            json_goals = self.parseGoals(goals)
            FuncAreas += json_goals

        Floor = self.CreateFloor(FuncAreas)

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
        self.scene_manager.SetSceneDeformation(xcenter, ycenter, scale)
        # 扩大Floor的边界
        outline = self.GetFloorOutline(Floor['FuncAreas'])
        margin_rate = 1.0/20
        for i in range(len(outline)):
            outline[i] *= (1+margin_rate)
        Floor['Outline'][0][0] = outline
        # print(Floor)
        # 调整 Floor 的 High 属性以改变墙的高度
        Floor['High'] = min(xlen, ylen)*scale/50

        Floors.append(Floor)
        result['data']['building'] = self.CreateBuilding(Floors)
        # print(json.dumps(result, indent=2))
        with open(outpath, 'w') as output:
            json.dump(result, output, indent=2)

        if len(sim.getElementsByTagName('agents')):
            agents = sim.getElementsByTagName('agents')[0]
            self.scene_manager.SetAgentsConfig(self.parseAgents(agents))
    

    def map_xml2json(self, simname, showtype=True):
        simdir = f"./simulations/{simname}"
        inipath = f"{simdir}/ini.xml"
        outpath = simdir+'/geo.json'

        # dom = xml.dom.minidom.parse(inipath)
        # sim = dom.documentElement
        # geometry = sim.getElementsByTagName('geometry')
        # floor = geometry.getElementsByTagName('floor')[0]
        
        # if(not os.path.isfile(outpath)):
        self.CreateMapJsonFile(inipath, outpath)
        return render_template('./simulate.html', datafile=outpath, showtype=showtype)
    
    


