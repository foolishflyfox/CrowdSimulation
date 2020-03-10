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
