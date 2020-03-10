from matplotlib.path import Path
from .utils import *
from threading import Lock
import random

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Grid:
    # 一个 Grid 为正方形，中心为(x,y)
    def __init__(self, x, y):
        self.left = None
        self.right = None
        self.up = None
        self.down = None
        self.x = x
        self.y = y

# p = Path([(0,0), (0,1), (1, 1), (1,0)])
# print(p.contains_point((0.5,0.5)))
# print(p.intersects_path(Path([(0,0), (0.5, 0.5), (1, 0)])))

class SceneManager:
    def __init__(self):
        self.initializeScene()

    def initializeScene(self):
        self.floor_outline = None
        self.room_outlines = {}
        self.obstacle_bounds = []
        self.obstacle_outlines = []
        self.init_lock = Lock()
        self.gridsize = 0.6
        self.grids = []
        # scene 的移动和缩放参数
        self.xcenter = 0.0
        self.ycenter = 0.0
        self.scale = 1.0
        # 存放 agents 的解析结果
        self.agents_config = None
        # 存放所有的 agent
        self.agents = []

    def SetSceneDeformation(self, xcenter, ycenter, scale):
        self.xcenter = xcenter
        self.ycenter = ycenter
        self.scale = scale
    def SetFloorOutline(self, floor_outline):
        self.floor_outline = floor_outline
    def AddRoomOutline(self, room_id, room_outline):
        self.room_outlines[room_id] = room_outline
    def AddObstacleBound(self, obstacle_bounds):
        self.obstacle_bounds += obstacle_bounds
    def AddObstacleOutline(self, obstacle_outline):
        self.obstacle_outlines.append(obstacle_outline)
    def SetGridSize(self, size):
        self.gridsize = max(size, self.gridsize)
    # tag: 场景网格化
    def GridScene(self):
        self.max_rect = GetMaxRect(self.floor_outline)
        top, bottom, left, right = MaxRectBound(self.max_rect)
        px, py = left+self.gridsize, top-self.gridsize
        path_floor_outline = Path(self.floor_outline)
        path_obstacle_outlines = []
        for obstacle_outline in self.obstacle_outlines:
            path_obstacle_outlines.append(Path(obstacle_outline))
        while py+0.000001 > bottom+self.gridsize:
            px = left+self.gridsize
            while px-0.000001 <= right-self.gridsize:
                # 条件1：在 floor 内
                if not path_floor_outline.contains_point((px, py)):
                    px += self.gridsize
                    continue
                # 条件2：不在 obstacle 内
                in_obstacle = False
                for path_obstacle_outline in path_obstacle_outlines:
                    if path_obstacle_outline.contains_point((px, py)):
                        in_obstacle = True
                        break
                if in_obstacle:
                    px += self.gridsize
                    continue
                # 条件3：与obstacle和wall的距离不能太近
                close_to_wall = False
                for i in range(1, len(self.obstacle_bounds), 2):
                    lineP1 = self.obstacle_bounds[i-1]
                    lineP2 = self.obstacle_bounds[i]
                    if ShortestDist(lineP1, lineP2, (px, py)) < 0.75*self.gridsize:
                        close_to_wall = True
                        break
                if close_to_wall:
                    px += self.gridsize
                    continue

                self.grids.append(Grid(px, py))
                px += self.gridsize
            py -= self.gridsize

    # tag: 初始化行人位置
    def InitAgents(self):
        if not self.agents_config: return
        custom_poses = self.agents_config['custom']
        agent_id = 1
        self.agents.clear()
        
        if custom_poses:
            for pos in custom_poses:
                self.agents.append({
                    'id': agent_id,
                    'x': pos[0],
                    'y': pos[1]
                })
                agent_id += 1
        else:
            choose_grids = set()
            free_grids = set([i for i in range(len(self.grids))])
            # tag: room 和 area 取走相应的位置
            area_infos = []
            for room_cfg in self.agents_config['room']:
                room_id = room_cfg['id']
                if room_id not in self.room_outlines:
                    continue
                area_infos.append({
                    "path": Path(self.room_outlines[room_id]),
                    "count": room_cfg['count'],
                    "grid_index": []
                })
            for area_cfg in self.agents_config['area']:
                left = area_cfg['left']
                right = area_cfg['right']
                bottom = area_cfg['bottom']
                top = area_cfg['top']
                area_infos.append({
                    "path": Path([(left, bottom), (right, bottom), 
                                (right, top), (left, top)]),
                    "count": area_cfg['count'],
                    "grid_index": []
                })
            for i in range(len(area_infos)):
                for j in range(len(self.grids)):
                    x = self.grids[j].x
                    y = self.grids[j].y
                    if area_infos[i]['path'].contains_point((x, y)):
                        area_infos[i]['grid_index'].append(j)
            for i in range(len(area_infos)):
                while area_infos[i]['count']>0 and len(area_infos[i]['grid_index']):
                    t = random.randint(0, len(area_infos[i]['grid_index'])-1)
                    grid_index = area_infos[i]['grid_index'][t]
                    choose_grids.add(grid_index)
                    if grid_index in free_grids:
                        free_grids.remove(grid_index)
                    del area_infos[i]['grid_index'][t]
                    area_infos[i]['count'] -= 1
                for grid_index in area_infos[i]['grid_index']:
                    if grid_index in free_grids:
                        free_grids.remove(grid_index)
                    
            # 其他位置
            self.agents_config['sum'] -= len(choose_grids)
            free_grids = list(free_grids)
            while len(free_grids)>0 and self.agents_config['sum']>0:
                self.agents_config['sum'] -= 1
                t = random.randint(0, len(free_grids)-1)
                choose_grids.add(free_grids[t])
                del free_grids[t]

            for i in choose_grids:
                self.agents.append({
                    'id': agent_id,
                    'x': self.grids[i].x,
                    'y': self.grids[i].y
                })
                agent_id += 1

        

    def GetAgents(self):
        # 确保初始化操作已经完成
        self.init_lock.acquire()
        self.init_lock.release()
        web_agents = {
            # 行人为半径为 0.25m 的圆或球
            'radius': 0.25*self.scale,
            'values': []
        }
        for agent in self.agents:
            web_agents['values'].append((agent['id'], 
                (agent['x']-self.xcenter)*self.scale,
                (agent['y']-self.ycenter)*self.scale))
        return web_agents

    def SceneInit(self):
        self.init_lock.acquire()
        self.GridScene()
        self.InitAgents()
        self.init_lock.release()

    # tag: 设置 agents 配置
    def SetAgentsConfig(self, agents_config):
        self.agents_config = agents_config

    def Route(self):
        # 使用迪杰斯特拉的变种，多目标+堆
        pass

    


