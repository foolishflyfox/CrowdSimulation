import math
import sys


# 获取宽松的边界
def GetLosseMaxRect(points):
    return GetMaxRect(points, 1)

# points 为二元组组成的数组
def GetMaxRect(points, margin=0):
    left = sys.maxsize
    bottom = sys.maxsize
    right = -sys.maxsize
    top = -sys.maxsize
    for x, y in points:
        left = min(left, x)
        right = max(right, x)
        bottom = min(bottom, y)
        top = max(top, y)
    return [left-margin, bottom-margin, right+margin, bottom-margin, 
        right+margin, top+margin, left-margin, top+margin]

def MaxRectBound(outline, typename=None): 
    result = 0
    if(typename=='left'):
        result = outline[0]
    elif(typename=='right'):
        result = outline[2]
    elif(typename=='bottom'):
        result = outline[1]
    elif(typename=='top'):
        result = outline[5]
    else:
        # 按上下左右顺序返回
        return (outline[5], outline[1], outline[0], outline[2])
    return result

def UnitNormalVector(point1, point2):
    """
    获取单位法向量
    :param vector: 2个点, e.g. UnitNormalVector((0,0), (0, 1))
    :return: 单位法向量
    """
    line12 = [v2-v1 for v1,v2 in zip(point1, point2)]
    if line12[0]==0 and line12[1]==0:
        return (0,0)
    x, y = line12[0], line12[1]
    normal_len = (y*y+x*x)**0.5
    unit_normal = (y/normal_len, -x/normal_len)
    return unit_normal

# 两个向量的向量积
# e.g. ScalarProduct((1,2),)
def ScalarProduct(vector1, vector2):
    return sum(v1*v2 for v1, v2 in zip(vector1, vector2))

# 找出一条线段中与指定点距离最短的点
# LinePoint1/LinePoint2 分别是线段的两个端点
# Point3 指定点
# 点的类型为一个二元组 (x, y) 或 三元组 (x, y, z)
# e.g. ShortestPoint((0,0), (3,0),(2,5)) => (2.0, 0.0)
# ShortestPoint((0,0,0), (6,6,6), (2,5,7)) => (4.67, 4.67, 4.67)
def ShortestPoint(LinePoint1, LinePoint2, Point3):
    if LinePoint1==LinePoint2:
        return LinePoint1
    vector21 = tuple(v1-v2 for v1, v2 in zip(LinePoint1, LinePoint2))
    vector23 = tuple(v3-v2 for v3, v2 in zip(Point3, LinePoint2))
    lamb = ScalarProduct(vector21, vector23)/ScalarProduct(vector21, vector21)
    if lamb > 1:
        return LinePoint1
    elif lamb < 0:
        return LinePoint2
    else:
        return tuple(i+lamb*j for i, j in zip(LinePoint2,vector21))

# 找出指定点到线段的最短距离
def ShortestDist(LinePoint1, LinePoint2, Point3):
    shortest_point = ShortestPoint(LinePoint1, LinePoint2, Point3)
    vec = tuple(p-p3 for p, p3 in zip(shortest_point, Point3))
    return ScalarProduct(vec, vec)**0.5

# 判断线段AB与线段CD是否相交
def IsIntersected(A, B, C, D):
    Ax, Ay = A
    Bx, By = B
    Cx, Cy = C
    Dx, Dy = D
    # 快速排斥
    if min(Ax,Bx)>max(Cx,Dx) or max(Ax,Bx)<min(Cx,Dx) or \
        min(Ay,By)>max(Cy,Dy) or max(Ay,By)<min(Cy,Dy):
        return False
    # 跨立实验
    eps = 1e-9
    # ac = (Cx-Ax)*(By-Ay)-(Cy-Ay)*(Bx-Ax)
    ac=(Cx-Ax)*(By-Ay)-(Cy-Ay)*(Bx-Ax)
    ad=(Dx-Ax)*(By-Ay)-(Dy-Ay)*(Bx-Ax)
    ca=(Ax-Cx)*(Dy-Cy)-(Ay-Cy)*(Dx-Cx)
    cb=(Bx-Cx)*(Dy-Cy)-(By-Cy)*(Dx-Cx)
    if ac*ad<eps and ca*cb<eps:
        return True
    return False

class Path:
    eps = 1e-6
    PI = 3.141592653589793
    # 判断 x 的符号
    def dcomp(self, x):
        x = x if x>0 else -x
        if x < self.eps:
            return 0
        return 1 if x > 0 else -1
    # points: a list of tuple
    def __init__(self, points):
        self.points = points
        if self.points[0]!=self.points[-1]:
            self.points.append(points[0])
        Xlist = []
        Ylist = []
        for tx, ty in self.points:
            Xlist.append(tx)
            Ylist.append(ty)
        self.maxX = max(Xlist)
        self.minX = min(Xlist)
        self.maxY = max(Ylist)
        self.minY = min(Ylist)
    # 判断 P 是否在图形内（包括边界）
    def contains_point(self, P):
        Px, Py = P
        if (Px>self.maxX or Px<self.minX or
            Py>self.maxY or Py<self.minY):
            return False
        # 射线法
        count = 0
        point1 = self.points[0]
        for i in range(1, len(self.points)):
            point2 = self.points[i]
            # 如果在顶点上
            if (P==point1) or (P==point2):
                return True
            if Py==min(point1[1],point2[1]):
                point1 = point2
                continue
            if ((point1[1]<Py and point2[1]>=Py) or 
                (point1[1]>=Py and point2[1]<Py)):
                # 求水平射線跟 p1,p2 連線 之交點的 x
                # x = p2.x - d
                # d = a*b/c
                # a = p2.y-Py
                # b = p2.x - p1.x
                # c = p2.y - p1.y
                x = point2[0] - (point2[1] - Py) * (point2[0] - point1[0])/(point2[1] - point1[1])
                if x < Px:
                    count += 1
                if x==Px:
                    return True
            point1 = point2
        return count%2!=0
            

