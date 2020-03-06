import math
import sys
 
def cross_multi(v1, v2):
    """
    计算两个向量的叉乘
    :param v1:
    :param v2:
    :return:
    """
    return v1[0]*v2[1] - v1[1]*v2[0]


# 获取宽松的边界
def GetLosseMaxRect(points):
    return GetMaxRect(points, 1)

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

def MaxRectBound(outline, type): 
    result = 0
    if(type=='left'):
        result = outline[0]
    elif(type=='right'):
        result = outline[2]
    elif(type=='bottom'):
        result = outline[1]
    elif(type=='top'):
        result = outline[5]
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
