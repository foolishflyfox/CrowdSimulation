import math

# 向量相关操作类
class Vector:
    def __init__(self, px=0, py=0):
        self.x = px
        self.y = py

    def lengthSquared(self):
        return self.x*self.x + self.y*self.y

    def length(self):
        return self.lengthSquared()**0.5

    def normalize(self):
        length = self.length()
        if length==0: return
        self.x /= length
        self.y /= length

    def normalized(self):
        length = self.length()
        if length==0:
            return Vector()
        else:
            return Vector(self.x/length, self.y/length)
    
    @staticmethod
    def dotProduct(vct1, vct2):
        return vct1.x*vct2.x + vct1.y*vct2.y
    
    def scale(self, factor):
        self.x *= factor
        self.y *= factor

    def scaled(self, factor):
        return Vector(self.x*factor, self.y*factor)

    # 注意，leftNormalVector 只用于二维情况
    def leftNormalVector(self):
        return Vector(-self.y, self.x)

    def rightNormalVector(self):
        return Vector(self.y, -self.x)

    def polarRadius(self):
        return self.length()

    def polarAngle(self):
        return math.atan2(self.y, self.x)

    def angleTo(self, vct):
        v_angle = self.polarAngle()
        o_angle = vct.polarAngle()
        diff_angle = o_angle - v_angle
        if diff_angle > math.pi:
            diff_angle -= 2*math.pi
        elif diff_angle < -math.pi:
            diff_angle += 2*math.pi
        return diff_angle

    def __add__(self, vct):
        return Vector(self.x+vct.x, self.y+vct.y)

    def __sub__(self, vct):
        return Vector(self.x-vct.x, self.y-vct.y)

    def __mul__(self, factor):
        if type(factor) is not type(self):
            return self.scaled(factor)
        else:
            o = factor
            return Vector(self.x*o.x, self.y*o.y)
    def __rmul__(self, factor):
        return self.scaled(factor)

    def __truediv__(self, divisor):
        return self.scaled(1.0/divisor)

    def __eq__(self, vct):
        return self.x==vct.x and self.y==vct.y

    def __neg__(self):
        return Vector(-self.x, -self.y)

    @staticmethod
    def lineIntersection(p0, p1, p2, p3, intersection=None):
        s1 = Vector(p1.x-p0.x, p1.y-p0.y)
        s2 = Vector(p3.x-p2.x, p3.y-p2.y)

        # 此处与c++中的代码不同，c++中除零后返回 -nan，该函数必定返回False
        div1 = -s2.x*s1.y+s1.x*s2.y
        div2 = -s2.x*s1.y+s1.x*s2.y
        if div1==0 or div2==0:
            return False
        s = (-s1.y*(p0.x-p2.x)+s1.x*(p0.y-p2.y)) / div1
        t = (s2.x*(p0.y-p2.y)-s2.y*(p0.x-p2.x)) / div2

        if s>=0 and s<=1 and t>=0 and t<=1:
            if intersection is not None:
                intersection.x = p0.x + t*s1.x
                intersection.y = p0.y + t*s1.y
            return True
        return False

    # 求点C到线段AB的最短距离
    @staticmethod
    def dot2lineDistance(A, B, C):
        AC = C - A
        AB = B - A
        cross = Vector.dotProduct(AC, AB)
        if cross <=0:
            return AC.length()
        AB_square = AB.lengthSquared()
        if cross >= AB_square:
            return (C-B).length()
        r = cross / AB_square
        D = A + AB * r
        return (D-C).length()

    # 求 p0-p1 线段到 p2-p3 线段的最短距离
    @staticmethod
    def lineDistance(p0, p1, p2, p3):
        if Vector.lineIntersection(p0, p1, p2, p3):
            return 0
        return min(Vector.dot2lineDistance(p0, p1, p2),
                Vector.dot2lineDistance(p0, p1, p3),
                Vector.dot2lineDistance(p2, p3, p0),
                Vector.dot2lineDistance(p2, p3, p1))

    # theta 为弧度
    def rotate(self, theta):
        xt = self.x*math.cos(theta) - self.y*math.sin(theta)
        yt = self.y*math.cos(theta) + self.x*math.sin(theta)
        self.x, self.y = xt, yt

    def rotated(self, theta):
        return Vector(self.x*math.cos(theta) - self.y*math.sin(theta),
                    self.y*math.cos(theta) + self.x*math.sin(theta))

    def __str__(self):
        # return f"({self.x}, {self.y})"
        return "(%.3f, %.3f)" % (self.x, self.y)


    


    
