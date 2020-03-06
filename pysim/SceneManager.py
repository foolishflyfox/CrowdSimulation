from matplotlib.path import Path
from .utils import GetMaxRect, MaxRectBound
from threading import Lock

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Grid:
    # 一个 Grid 为正方向，左上角点为(x,y)，边长为size
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
        self.floor_outline = None
        self.obstacle_outlines = []
        self.init_lock = Lock()
        self.gridsize = 0.3
        self.grids = []
    def SetFloorOutline(self, floor_outline):
        self.floor_outline = floor_outline
    def AddObstacleOutlines(self, obstacle_outlines):
        self.obstacle_outlines += obstacle_outlines
    def SetGridSize(self, size):
        self.gridsize = size
    def GridScene(self):
        self.max_rect = GetMaxRect(self.floor_outline)
        top, bottom, left, right = MaxRectBound(self.max_rect)
        px, py = left+self.gridsize/2, top-self.gridsize/2
        path_floor_outline = Path(self.floor_outline)
        while py-self.gridsize > bottom+self.gridsize/2:
            while px+self.gridsize < right-self.gridsize/2:
                # 条件1：在 floor 内
                if path_floor_outline.contains_point((px, py)):
                    px += self.gridsize
                    continue
                # 条件2：不在 obstacle 内

                # 条件3：与obstacle和wall的不重叠

                self.grids.append(Grid(px, py))
                px += self.gridsize
            py -= self.gridsize

    def SceneInit(self):
        self.init_lock.acquire()
        self.GridScene()
        self.init_lock.release()

    def Route(self):
        # 使用迪杰斯特拉的变种，多目标+堆
        pass

    


