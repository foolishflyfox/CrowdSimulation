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
    def __init__(self, distance=float('inf')):
        self.distance = distance
        # 下一个格点的索引 (i, j)
        self.next = None
        # self.x = x
        # self.y = y

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
        self.indoor_walls = []
        self.obstacle_outlines = []
        self.goal_outlines = []
        self.init_lock = Lock()
        self.gridsize = 0.6
        self.grids = [[]]
        self.init_poses = []
        # scene 的移动和缩放参数
        self.xcenter = 0.0
        self.ycenter = 0.0
        self.scale = 1.0
        # 存放 agents 的解析结果
        self.agents_config = None
        # 存放所有的 agent
        self.agents = []
        # 行人半径
        self.agent_radius = 0.25
        # 网格化参数
        self.grid_left = 0
        self.grid_right = 0
        self.grid_bottom = 0
        self.grid_top = 0
        self.grid_xnum = 0
        self.grid_ynum = 0
        self.grid_index_dist = {}

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
    def AddIndoorWall(self, indoor_wall):
        self.indoor_walls += indoor_wall
    def AddObstacleOutline(self, obstacle_outline):
        self.obstacle_outlines.append(obstacle_outline)
    def AddGoalOutline(self, goal_outline):
        self.goal_outlines.append(goal_outline)
    def SetGridSize(self, size):
        self.gridsize = max(size, self.gridsize)
    # tag: 场景网格化
    def GridScene(self):
        self.grid_index_dist.clear()
        self.max_rect = GetMaxRect(self.floor_outline)
        top, bottom, left, right = MaxRectBound(self.max_rect)
        path_floor_outline = Path(self.floor_outline)
        path_obstacle_outlines = []
        path_goal_outlines = []
        for obstacle_outline in self.obstacle_outlines:
            path_obstacle_outlines.append(Path(obstacle_outline))
        for goal_outline in self.goal_outlines:
            path_goal_outlines.append(Path(goal_outline))
            for x, y in goal_outline:
                if x < left: left = x
                elif x > right: right = x
                if y < bottom: bottom = y
                elif y > top: top = y
        self.grid_left = left+self.gridsize
        self.grid_right = right-self.agent_radius*1.2
        self.grid_top = top-self.gridsize
        self.grid_bottom = bottom+self.agent_radius*1.2
        self.grid_xnum = int((self.grid_right-self.grid_left)/self.gridsize)+1
        self.grid_ynum = int((self.grid_top-self.grid_bottom)/self.gridsize)+1
        # px, py = left+self.gridsize, top-self.gridsize
        # while py+0.000001 > bottom+self.agent_radius*1.2:
        self.grids = [[None]*self.grid_xnum for i in range(self.grid_ynum)]
        for i in range(self.grid_ynum):
            py = self.grid_top - i*self.gridsize
            for j in range(self.grid_xnum):
                px = self.grid_left + j*self.gridsize
                # 判断是否在 goal 中
                in_goal = False
                for path_goal_outline in path_goal_outlines:
                    if path_goal_outline.contains_point((px, py)):
                        in_goal = True
                        break
                if in_goal:
                    self.grids[i][j] = Grid(0)
                    self.grid_index_dist[(i, j)] = 0
                    continue
                # 条件1：在 floor 内
                if not path_floor_outline.contains_point((px, py)):
                    continue
                # 条件2：不在 obstacle 内
                in_obstacle = False
                for path_obstacle_outline in path_obstacle_outlines:
                    if path_obstacle_outline.contains_point((px, py)):
                        in_obstacle = True
                        break
                if in_obstacle:
                    continue
                # 条件3：与obstacle和wall的距离不能太近
                close_to_wall = False
                for k in range(1, len(self.obstacle_bounds), 2):
                    lineP1 = self.obstacle_bounds[k-1]
                    lineP2 = self.obstacle_bounds[k]
                    if ShortestDist(lineP1, lineP2, (px, py)) < self.agent_radius:
                        close_to_wall = True
                        break
                if close_to_wall:
                    continue
                self.init_poses.append((px, py))
                self.grids[i][j] = Grid()

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
            free_grids = set([i for i in range(len(self.init_poses))])
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
                for j in range(len(self.init_poses)):
                    x = self.init_poses[j].x
                    y = self.init_poses[j].y
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
                    'x': self.init_poses[i][0],
                    'y': self.init_poses[i][1]
                })
                agent_id += 1
            self.init_poses.clear()


    def GetAgents(self):
        # 确保初始化操作已经完成
        self.init_lock.acquire()
        self.init_lock.release()
        web_agents = {
            # 行人为半径为 0.25m 的圆或球
            'radius': self.agent_radius*self.scale,
            'values': []
        }
        for agent in self.agents:
            web_agents['values'].append((agent['id'], 
                (agent['x']-self.xcenter)*self.scale,
                (agent['y']-self.ycenter)*self.scale))
        return web_agents

    def Route(self):
        dict_calc = {(-1,1):2**0.5, (1,-1):2**0.5, (1,1): 2**0.5,
                     (-1,-1):2**0.5, (1,0):1, (0,1):1,
                     (-1,0):1, (0,-1):1, (0,0):0}
        print("Route Begin")
        # 使用迪杰斯特拉的变种，多目标
        while len(self.grid_index_dist):
            min_dist = float('inf')
            select_index = None
            # 找到距离目标最近的格点
            for t_index in self.grid_index_dist:
                if self.grid_index_dist[t_index] < min_dist:
                    min_dist = self.grid_index_dist[t_index]
                    select_index = t_index
            # 更新周围的8个格点
            cur_i, cur_j = select_index
            del self.grid_index_dist[select_index]
            for i in range(-1, 2):
                for j in range(-1, 2):
                    ti = cur_i + i
                    tj = cur_j + j
                    if ti<0 or tj<0 or ti>=self.grid_ynum or tj>=self.grid_xnum:
                        continue
                    if self.grids[ti][tj]==None or self.grids[ti][tj].distance <= min_dist:
                        continue
                    tdist = min_dist+dict_calc[(i,j)]*self.gridsize
                    if self.grids[ti][tj].distance <= tdist:
                        continue
                    is_block = False
                    # 判断是否有障碍物阻隔
                    for k in range(1, len(self.indoor_walls), 2):
                        if IsIntersected(self.indoor_walls[k-1], self.indoor_walls[k],
                            (self.grid_left+self.gridsize*cur_j, self.grid_top-self.gridsize*cur_i),
                            (self.grid_left+self.gridsize*tj, self.grid_top-self.gridsize*ti)):
                            is_block = True
                            break
                    if is_block:
                        continue
                    self.grids[ti][tj].distance = tdist
                    self.grids[ti][tj].next = (cur_i, cur_j)
                    self.grid_index_dist[(ti, tj)] = tdist
        print("Route Finish")

    def GetRoute(self):
        web_route = []
        
        # f = open('t.txt', 'w')
        for i in range(0, self.grid_ynum):
            for j in range(0, self.grid_xnum):
                if self.grids[i][j]!=None and self.grids[i][j].next!=None:
                    next_i = self.grids[i][j].next[0]
                    next_j = self.grids[i][j].next[1]
                    # print(i, j, next_i, next_j, file=f)
                    # 方向起始坐标
                    web_route.append(self.grid_left+j*self.gridsize)
                    web_route.append(self.grid_top-i*self.gridsize)
                    # 方向终止坐标
                    web_route.append(self.grid_left+next_j*self.gridsize)
                    web_route.append(self.grid_top-next_i*self.gridsize)
        # f.close()
        # web_route = [0, 0, -2, -2, -3, -3, 0, -2]
        for i in range(0, len(web_route), 2):
            web_route[i] = (web_route[i]-self.xcenter)*self.scale
            web_route[i+1] = (web_route[i+1]-self.ycenter)*self.scale
        return web_route



    def SceneInit(self):
        self.init_lock.acquire()
        self.GridScene()
        self.InitAgents()
        self.Route()
        self.init_lock.release()

    # tag: 设置 agents 配置
    def SetAgentsConfig(self, agents_config):
        self.agents_config = agents_config

    


