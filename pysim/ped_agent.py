from .ped_vector import Vector
import math
from .utils import ShortestPoint

class Agent:
    def __init__(self, agent_id, x, y, scene_manager):
        self.scene_manager = scene_manager
        self.id = agent_id
        # agent 的当前位置
        self.p = Vector(x, y)
        # agent 的当前速度
        self.v = Vector()
        # agent 的当前加速度
        self.a = Vector()
        
        # agent 可以达到的最大速度 m/s
        self.vmax = 1.3
        # 下面的社会力参数基于对 pedsim 的调参拟合，并非实际测定
        # 社会力因子 在 0~10 之间
        self.factorsocialforce = 2.1
        # 障碍物因子 在 0~10 之间
        self.factorobstacleforce = 1.0
        # 驱动力因子 在 0~10之间
        self.factordesiredforce = 1.3
        # TODO: 该因子是否还要使用
        self.factorlookaheadforce = 1.0

        self.desiredforce = Vector()
        self.socialforce = Vector()
        self.obstacleforce = Vector()
        self.lookaheadforce = Vector()
        self.myforce = Vector()

        self.obstacleForceSigma = 0.8
        self.agent_radius = 0.25

        self.reached = False
    
    def setPosition(self, px, py):
        self.p.x = px
        self.p.y = py

    def move(self, h):
        if self.reached: return
        p_desired = self.p + self.v*h
        self.p = p_desired
        self.a = (self.factordesiredforce*self.desiredforce
            + self.factorsocialforce * self.socialforce
            + self.factorobstacleforce * self.obstacleforce
            + self.factorlookaheadforce * self.lookaheadforce)
        # 计算新的速度
        self.v = self.v + self.a * h
        # 不能超过最大速度
        if self.v.length() > self.vmax:
            self.v = self.v.normalized()*self.vmax

    # tag: 计算行人收到的合力
    def computeForces(self):
        # 当前位置相邻的 agent
        self.desiredforce = Vector()
        self.socialforce = Vector()
        self.obstacleforce = Vector()
        self.lookaheadforce = Vector()
        self.desiredforce = self.desiredForce()
        if self.reached: return
        if self.factorsocialforce > 0:
            neighbors = self.scene_manager.getNeighbors(self.p.x, self.p.y)
            self.socialforce = self.socialForce(neighbors)
        obstacles = self.scene_manager.getObstacles(self.p.x, self.p.y)
        if self.factorobstacleforce > 0 and len(obstacles) > 0:
            self.obstacleforce = self.obstacleForce(obstacles)

    # 计算agent和下一个被分配的waypoint之间的作用力的方向(不包含大小)
    def desiredForce(self):
        destination = self.scene_manager.getDestination(self.p.x, self.p.y)
        if destination is None:
            self.reached = True
            return Vector(0, 0)
        return Vector(destination[0]-self.p.x, destination[1]-self.p.y).normalized()

    def socialForce(self, neighbors):
        # 定义位置向量与速度向量的相对重要性（Moussaid-Helbing 2009）
        lambdaImportance = 2.0
        # 定义速度的互作用 （Mossaid-Helbing 2009）
        gamma = 0.35
        n = 2
        # 角度的互作用
        n_prime = 3
        force = Vector()
        for other_agent in neighbors:
            # 不考虑自身对自己产生的社会力
            if other_agent.id == self.id:
                continue
            # 计算两个 agent 之间的位置差异
            diff = other_agent.p - self.p
            diffDirection = diff.normalized()
            # 计算本agent i相对于agent j的相对速度
            velDiff = self.v - other_agent.v

            interactionVector = lambdaImportance * velDiff + diffDirection
            interactionLength = interactionVector.length()
            interactionDirection = interactionVector / interactionLength

            theta = interactionDirection.angleTo(diffDirection)
            thetaSign = 0 if theta==0 else (theta/abs(theta))

            B = gamma * interactionLength
            forceVelocityAmount = -math.exp(-diff.length()/B-(n_prime*B*theta)**2)
            forceAngleAmount = -thetaSign*math.exp(-diff.length()/B-(n*B*theta)**2)

            forceVelocity = forceVelocityAmount * interactionDirection
            forceAngle = forceAngleAmount * interactionDirection.leftNormalVector()

            force += forceVelocity + forceAngle
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
        force_amount = math.exp(-distance/self.obstacleForceSigma)
        return force_amount * min_diff.normalized()


