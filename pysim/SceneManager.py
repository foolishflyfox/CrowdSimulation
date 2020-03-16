from matplotlib.path import Path
from .utils import GetMaxRect, MaxRectBound, ShortestDist, IsIntersected
from .ped_agent import Agent
from threading import Lock
import random
import threading
import queue
import time

# TODO: 设置了 xml 的 scale 参数之后 map.Loader 不能正常工作

# tag: 用于将行人运动信息发送给客户端的线程类
class SendStateThread(threading.Thread):
    def __init__(self, socketio, scene_manager):
        threading.Thread.__init__(self)
        self.socketio = socketio
        self.scene_manager = scene_manager
        self.running = True
    def run(self):
        while self.running:
            # print('send state...')
            t0 = time.time()
            web_agents = self.scene_manager.state_queue.get()
            self.scene_manager.timer += self.scene_manager.interval
            web_agents['timer'] = "%.1f s" % self.scene_manager.timer
            self.socketio.emit('sim_state', web_agents)

            sleep_time = self.scene_manager.interval-(time.time()-t0)
            if sleep_time > 0:
                time.sleep(sleep_time)
    def Pause(self):
        self.running = False


# tag: 用于更新行人运动状态的线程类
class UpdateStateThread(threading.Thread):
    def __init__(self, scene_manager):
        threading.Thread.__init__(self)
        self.scene_manager = scene_manager
    def run(self):
        # cnt = 1
        while self.scene_manager.moveAgents():
            pass
        print("Simulation Finished")


class Grid:
    # 一个 Grid 为正方形，中心为(x,y)
    def __init__(self, distance=float('inf')):
        self.distance = distance
        # 下一个格点的索引 (i, j)
        self.next = None
        # 存放位于该 grid 范围的 agents，key 为agent的id
        # value 为 Agent 类型
        self.agents = {}
        # 存放于该 grid 临近的 obstacles
        self.obstacles = []

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
        # 仿真参数
        self.interval = 0.025
        self.state_queue = queue.Queue(2/self.interval)
        # 仿真线程
        self.send_state_thread = None
        self.update_state_thread = None
        # 仿真时间计时器
        self.timer = 0.0
        # 含有 agent 的grid的索引集合
        self.agent_grids = set()
        

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
        # 网格元素数组初始化
        self.grid_left = left+self.gridsize
        self.grid_right = right-self.agent_radius*1.2
        self.grid_top = top-self.gridsize
        self.grid_bottom = bottom+self.agent_radius*1.2
        self.grid_xnum = int((self.grid_right-self.grid_left)/self.gridsize)+1
        self.grid_ynum = int((self.grid_top-self.grid_bottom)/self.gridsize)+1
        self.grids = [[None]*self.grid_xnum for i in range(self.grid_ynum)]

        for i in range(self.grid_ynum):
            py = self.grid_top - i*self.gridsize
            for j in range(self.grid_xnum):
                px = self.grid_left + j*self.gridsize
                # 判断是否在 goal 中, 在 goal 中的 grid 不能为初始化位置
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
                t_obstacles = []
                for k in range(1, len(self.obstacle_bounds), 2):
                    lineP1 = self.obstacle_bounds[k-1]
                    lineP2 = self.obstacle_bounds[k]
                    dist_to_obstacle = ShortestDist(lineP1, lineP2, (px, py))
                    if dist_to_obstacle < self.agent_radius:
                        close_to_wall = True
                        break
                    # tag: 向 grid 中添加临近的 obstacle
                    # if dist_to_obstacle < self.agent_radius*4:
                    if dist_to_obstacle < self.agent_radius+self.gridsize:
                        t_obstacles.append((lineP1, lineP2))
                if close_to_wall:
                    continue
                self.init_poses.append((px, py))
                self.grids[i][j] = Grid()
                self.grids[i][j].obstacles = t_obstacles

    # tag: 初始化行人位置
    def InitAgents(self):
        if not self.agents_config: return
        custom_poses = self.agents_config['custom']
        agent_id = 1
        self.agents.clear()
        
        choose_grids = set()
        free_grids = set([i for i in range(len(self.init_poses))])
        
        area_infos = []
        # 设置通过 custom 方式指定的行人初始化位置
        for pos in custom_poses:
            tx = pos[0]
            ty = pos[1]
            left = tx-self.gridsize/2
            right = tx+self.gridsize/2
            top = ty+self.gridsize/2
            bottom = ty-self.gridsize/2
            area_infos.append({
                "path": Path([(left, bottom), (right, bottom), 
                            (right, top), (left, top)]),
                "count": 1,
                "grid_index": []
            })
        # 设置通过 room 指定的行人初始化参数
        for room_cfg in self.agents_config['room']:
            room_id = room_cfg['id']
            if room_id not in self.room_outlines:
                continue
            area_infos.append({
                "path": Path(self.room_outlines[room_id]),
                "count": room_cfg['count'],
                "grid_index": []
            })
        # 设置通过 area 指定的行人初始化参数
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
                x = self.init_poses[j][0]
                y = self.init_poses[j][1]
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
            i_grid = round((self.grid_top-self.init_poses[i][1])/self.gridsize)
            j_grid = round((self.init_poses[i][0]-self.grid_left)/self.gridsize)
            t_agent = Agent(agent_id, self.init_poses[i][0], self.init_poses[i][1], 
                            self, j_grid, i_grid)
            self.agents.append(t_agent)
            # 将 agent 加入到 grid 中, 加快附近 agent 的搜索速度
            self.grids[i_grid][j_grid].agents[agent_id] = t_agent
            agent_id += 1
            self.agent_grids.add((i_grid, j_grid))

        self.init_poses.clear()


    def GetAgents(self):
        # 获取锁, 确保初始化操作已经完成
        self.init_lock.acquire()
        self.init_lock.release()
        web_agents = {
            # 行人为半径为 0.25m 的圆或球
            'radius': self.agent_radius*self.scale,
            'values': []
        }
        for agent in self.agents:
            web_agents['values'].append((agent.id, 
                (agent.p.x-self.xcenter)*self.scale,
                (agent.p.y-self.ycenter)*self.scale))
        return web_agents

    # TODO: 添加随机化信息
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
                            self.getPosFromGridIndex(cur_j, cur_i),
                            self.getPosFromGridIndex(tj, ti)):
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
        for i in range(0, self.grid_ynum):
            for j in range(0, self.grid_xnum):
                if self.grids[i][j]!=None and self.grids[i][j].next!=None:
                    next_i = self.grids[i][j].next[0]
                    next_j = self.grids[i][j].next[1]
                    # 方向起始坐标
                    web_route.append(self.grid_left+j*self.gridsize)
                    web_route.append(self.grid_top-i*self.gridsize)
                    # 方向终止坐标
                    web_route.append(self.grid_left+next_j*self.gridsize)
                    web_route.append(self.grid_top-next_i*self.gridsize)
        for i in range(0, len(web_route), 2):
            web_route[i] = (web_route[i]-self.xcenter)*self.scale
            web_route[i+1] = (web_route[i+1]-self.ycenter)*self.scale
        return web_route

    # tag: 场景初始化
    def SceneInit(self):
        self.init_lock.acquire()
        self.GridScene()
        self.InitAgents()
        self.Route()
        self.init_lock.release()
        
        # for i in range(self.grid_ynum):
        #     for j in range(self.grid_xnum):
        #         if self.grids[i][j]:
        #             print(" %d " % len(self.grids[i][j].obstacles), end="")
        #         else:
        #             print("   ", end="")
        #     print("")

    # tag: 设置 agents 配置
    def SetAgentsConfig(self, agents_config):
        self.agents_config = agents_config

    # tag: 收到客户端的 Start 消息
    def StartSimulate(self, interval, socketio):
        self.interval = interval
        if(self.update_state_thread==None):
            self.update_state_thread = UpdateStateThread(self)
            self.update_state_thread.start()

        self.send_state_thread = SendStateThread(socketio, self)
        self.send_state_thread.start()

    # tag: 收到客户端的 Pause 消息
    def PauseSimulate(self):
        if self.send_state_thread:
            self.send_state_thread.Pause()
            # self.send_state_thread.join()
            self.send_state_thread = None
            print("Pause Simulation")

    def getGridIndexFromPos(self, x, y):
        xindex = round((x-self.grid_left)/self.gridsize)
        yindex = round((self.grid_top-y)/self.gridsize)
        return xindex, yindex

    def getPosFromGridIndex(self, xindex, yindex):
        x = self.grid_left+self.gridsize*xindex
        y = self.grid_top-self.gridsize*yindex
        return x, y

    # tag: 获取某点的目标
    def getDestination(self, cur_agent):
        # xindex, yindex = self.getGridIndexFromPos(x, y)
        xindex = cur_agent.xgrid
        yindex = cur_agent.ygrid
        
        cur_grid = self.grids[yindex][xindex]
        # 当前位置没有纳入规划范围(可能是不可达的)
        if cur_grid==None:
            return (cur_agent.x, cur_agent.y)
        # print(xindex, yindex, cur_grid.distance)
        # 到达目标位置
        if cur_grid.distance==0:
            return None
        next_index = cur_grid.next
        # 当前位置没有下一跳的节点
        if next_index==None:
            return (cur_agent.x, cur_agent.y)
        xindex_next = next_index[1]
        yindex_next = next_index[0]
        return self.getPosFromGridIndex(xindex_next, yindex_next)

    # 获取某点附近的 agents
    def getNeighbors(self, cur_agent):
        # xindex, yindex = self.getGridIndexFromPos(px, py)
        xindex = cur_agent.xgrid
        yindex = cur_agent.ygrid
        neighbors = []
        for i in range(-1, 2):
            for j in range(-1, 2):
                ty = yindex+i
                tx = xindex+j
                if tx<0 or ty<0 or tx>=self.grid_xnum or ty>=self.grid_ynum:
                    continue
                if self.grids[ty][tx] is None:
                    continue
                neighbors += list(self.grids[ty][tx].agents.values())
        return neighbors

    def getObstacles(self, cur_agent):
        # xindex, yindex = self.getGridIndexFromPos(px, py)
        xindex = cur_agent.xgrid
        yindex = cur_agent.ygrid
        if self.grids[yindex][xindex] is None: return []
        return self.grids[yindex][xindex].obstacles

    def updateAgentGrid(self, cur_agent):
        xgrid, ygrid = self.getGridIndexFromPos(cur_agent.p.x, cur_agent.p.y)
        if cur_agent.xgrid==xgrid and cur_agent.ygrid==ygrid:
            return
        if xgrid<0 or xgrid>=self.grid_xnum or ygrid<0 or ygrid>=self.grid_ynum:
            return
        if self.grids[ygrid][xgrid] is None:
            return
        del self.grids[cur_agent.ygrid][cur_agent.xgrid].agents[cur_agent.id]
        cur_agent.xgrid = xgrid
        cur_agent.ygrid = ygrid
        self.grids[ygrid][xgrid].agents[cur_agent.id] = cur_agent

    def moveAgents(self):
        web_agents = {
            'radius': self.agent_radius*self.scale,
            'values': []
        }
        # new_agent_grids = set()
        # agents_list = []
        # ori_index = []

        new_agents = []
        for cur_agent in self.agents:
            if cur_agent.reached:
                if cur_agent.id in self.grids[cur_agent.ygrid][cur_agent.xgrid].agents:
                    del self.grids[cur_agent.ygrid][cur_agent.xgrid].agents[cur_agent.id]
                continue
            cur_agent.computeForces()
            cur_agent.move(self.interval)
            web_agents['values'].append((cur_agent.id,
                (cur_agent.p.x-self.xcenter)*self.scale,
                (cur_agent.p.y-self.ycenter)*self.scale))
            new_agents.append(cur_agent)
        self.agents = new_agents
        
        self.state_queue.put(web_agents)
        if len(web_agents['values'])!=0:
            return True
        else:
            return False
    

    def DebugGridInfo(self):
        grid_info = {}
        for t_agent in self.agents:
            grid_info[t_agent.id] = {
                'xgrid': t_agent.xgrid,
                'ygrid': t_agent.ygrid,
                'x': "%.2f" %t_agent.p.x,
                'y': "%.2f" %t_agent.p.y
            }
        return grid_info


