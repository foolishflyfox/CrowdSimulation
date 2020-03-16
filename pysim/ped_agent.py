from .ped_vector import Vector
import math
from .utils import ShortestPoint, ShortestDist
import random

class Agent:
    def __init__(self, agent_id, x, y, scene_manager, xgrid, ygrid):
        self.scene_manager = scene_manager
        self.id = agent_id
        # agent 的当前位置
        self.p = Vector(x, y)
        # agent 的当前速度
        self.v = Vector()
        # agent 的当前加速度
        self.a = Vector()
        # agent 所在格点
        self.xgrid = xgrid
        self.ygrid = ygrid
        
        # agent 可以达到的最大速度 m/s
        self.vmax = 1.3
        self.keep_rate = 1.0
        # 下面的社会力参数基于对 pedsim 的调参拟合，并非实际测定
        # 社会力因子 在 0~10 之间
        self.factorsocialforce = 0.3
        self.social_alpha = 3.0
        # 障碍物因子 在 0~10 之间
        self.factorobstacleforce = 1
        self.obstacleForceSigma = 0.8
        # 驱动力因子 在 0~10之间
        self.factordesiredforce = 2.5
        # TODO: 该因子是否还要使用
        self.factorlookaheadforce = 1.0

        self.desiredforce = Vector()
        self.socialforce = Vector()
        self.obstacleforce = Vector()
        self.lookaheadforce = Vector()
        self.myforce = Vector()

        self.agent_radius = 0.25

        self.reached = False
    
    def setPosition(self, px, py):
        self.p.x = px
        self.p.y = py

    def distToNeighbors(self):
        dist = float('inf')
        neighbors = self.scene_manager.getNeighbors(self)
        for other in neighbors:
            if other.id == self.id:
                continue
            dist = min(dist, (self.p-other.p).length())
        return dist


    # 判断是否会与附近的 obstacle 相撞
    def isCollideToObstacle(self):
        obstacles = self.scene_manager.getObstacles(self)
        for obstacle in obstacles:
            if ShortestDist(obstacle[0], obstacle[1], (self.p.x, self.p.y)) < self.agent_radius:
                return True
        return False

    def move(self, h):
        if self.reached: return
        self.a = (self.factordesiredforce*self.desiredforce
            + self.factorsocialforce * self.socialforce
            + self.factorobstacleforce * self.obstacleforce
            + self.factorlookaheadforce * self.lookaheadforce)
        # 计算新的速度
        # self.v = self.keep_rate*self.v + self.a * h
        self.v = self.a * 100
        # 不能超过最大速度
        if self.v.length() > self.vmax:
            self.v = self.v.normalized()*self.vmax
        ori_pos = self.p
        rotate_angles = [0]
        rotate_angles.append(math.pi*(random.randint(0, 1)-0.5)/4)
        rotate_angles.append(rotate_angles[-1]*-1)
        rotate_angles.append(math.pi*(random.randint(0, 1)-0.5)/2)
        rotate_angles.append(rotate_angles[-1]*-1)
        rotate_angles.append(math.pi*(random.randint(0, 1)-0.5))
        rotate_angles.append(rotate_angles[-1]*-1)
        rotate_angles.append(math.pi*(random.randint(0, 1)-0.5)/1.2)
        rotate_angles.append(rotate_angles[-1]*-1)
        for t_theta in rotate_angles:
            move_vector = self.v.rotated(t_theta)*h
            for _ in range(3):
                pre_dist = self.distToNeighbors()
                self.p = ori_pos + move_vector
                if self.isCollideToObstacle():
                    continue
                cur_dist = self.distToNeighbors()
                if cur_dist >= self.agent_radius * 2 or (cur_dist>=pre_dist):
                    self.scene_manager.updateAgentGrid(self)
                    break
                move_vector *= 0.5
            else:
                continue
                # self.p = ori_pos
            break
        else:
            self.p = ori_pos

    # tag: 计算行人收到的合力
    def computeForces(self):
        # 当前位置相邻的 agent
        self.desiredforce = Vector()
        self.socialforce = Vector()
        self.obstacleforce = Vector()
        self.lookaheadforce = Vector()
        if self.reached: 
            return
        self.desiredforce = self.desiredForce()
        # if self.factorsocialforce > 0:
        #     neighbors = self.scene_manager.getNeighbors(self.p.x, self.p.y)
        #     self.socialforce = self.socialForce(neighbors)
        # obstacles = self.scene_manager.getObstacles(self.p.x, self.p.y)
        # if self.factorobstacleforce > 0 and len(obstacles) > 0:
        #     self.obstacleforce = self.obstacleForce(obstacles)

    # 计算agent和下一个被分配的waypoint之间的作用力的方向(不包含大小)
    def desiredForce(self):
        destination = self.scene_manager.getDestination(self)
        # print("destination :", destination, ", from :", self.p)
        if destination is None:
            self.reached = True
            return Vector(0, 0)
        return Vector(destination[0]-self.p.x, destination[1]-self.p.y).normalized()

    def socialForce(self, neighbors):
        # 定义位置向量与速度向量的相对重要性（Moussaid-Helbing 2009）
        lambdaImportance = 1.0
        # 定义速度的互作用 （Mossaid-Helbing 2009）
        gamma = 0.35
        n = 2
        # 角度的互作用
        n_prime = 3
        force = Vector()

        agent_radius = 0.25
        for other_agent in neighbors:
            # 不考虑自身对自己产生的社会力
            if other_agent.id == self.id:
                continue
            # # 计算两个 agent 之间的位置差异
            # diff = other_agent.p - self.p
            # diffDirection = diff.normalized()
            # # 计算本agent i相对于agent j的相对速度
            # velDiff = self.v - other_agent.v

            # interactionVector = lambdaImportance * velDiff + diffDirection
            # interactionLength = interactionVector.length()
            # interactionDirection = interactionVector / interactionLength

            # theta = interactionDirection.angleTo(diffDirection)
            # thetaSign = 0 if theta==0 else (theta/abs(theta))

            # B = gamma * interactionLength
            # forceVelocityAmount = -math.exp(-diff.length()/B-(n_prime*B*theta)**2)
            # forceAngleAmount = -thetaSign*math.exp(-diff.length()/B-(n*B*theta)**2)

            # forceVelocity = forceVelocityAmount * interactionDirection
            # forceAngle = forceAngleAmount * interactionDirection.leftNormalVector()
            # force += forceVelocity + forceAngle

            diff = other_agent.p - self.p
            diffDirection = diff.normalized()
            diffLength = diff.length()
            force += -math.exp((diffLength-agent_radius)/self.social_alpha)*diffDirection
        return force

    # 计算最近的障碍物对本agent的作用力
    def obstacleForce(self, obstacles):
        min_dist = float('inf')
        min_diff = None
        for obstacle in obstacles:
            closest_point = ShortestPoint(obstacle[0], obstacle[1], (self.p.x, self.p.y))
            diff = self.p - Vector(closest_point[0], closest_point[1])
            t_dist = diff.length()
            if t_dist < min_dist:
                min_dist = t_dist
                min_diff = diff
        if min_diff is None: return Vector()
        distance = min_dist - self.agent_radius
        # print("distance with obstacle :", distance)
        # force_amount = math.exp(-distance/self.obstacleForceSigma)
        force_amount = math.exp(distance/self.obstacleForceSigma)
        return force_amount * min_diff.normalized()


