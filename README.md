# 人群仿真web显示

## 系统要求

- python3
    - Flask
    - matplotlib
    - flask-socketio


## 启动web服务

- 启动 web 服务：`python app`，将会在本机的 8080 端口提供web服务
- 地图选择界面：在浏览器中输入`IP地址:8080`，如`localhost:8080`，即可进入地图选择界面

![project select](readme_imgs/project_select.png)

其中仿真工程名从 *simulations* 目录中读取子文件夹，每个子文件夹代表一个仿真项目，包含仿真所需的所有信息，如地图信息、人群初始化信息，模型参数等。可以通过单选按钮选择显示类型，点击开始仿真即可载入地图。

## 地图效果

2D 地图的效果如下：

![demo1 2d map](readme_imgs/demo1-2Dmap.png)

3D 地图的显示效果为：

![demo1 3d map](readme_imgs/demo1-3Dmap.png)

说明：

- 红色为障碍物
- 浅蓝色为房间的出口
- 深绿色为建筑物的出口
- 浅绿色透明区域是安全区域，行人进入该区域及表示安全，并从地图中消失
- 其余对象为墙体

## 地图配置文件说明

上述显示的配置信息在 *simulations/demo1/ini.xml* 中，注意，一个仿真项目必须在 *simulations* 下有其对应的子文件夹，并且该子文件夹中必须有一个名为 *ini.xml* 的配置文件。配置文件格式为：
```xml
<?xml version="1.0" encoding="UTF-8" ?>

<CrowdSimulation>
    <scene>
        <!-- 墙壁全局属性，定义外墙和房间墙的默认厚度，必须定义-->
        <floorwall thickness="1" />
        <roomwall thickness="0.5" />
    </scene>
    <geometry>
        <floor>
            <!-- 楼层的范围定义，由wall和transition构成
            其中的 vertex 必须有序，可以构成一个闭合多边形 -->
            <outwall>
                <!-- thickness 可省略，省略后使用全局属性 -->
                <wall thickness="1.2">
                    <vertex px="-50" py="0"/>
                    ... ...
                </wall>
                <transition>
                    <vertex px="50" py="10"/>
                    ... ...
                </transition>
                ... ...
            </outwall>
            <room>
                <!-- thickness 可省略，省略后使用全局属性 -->
                <wall thickness="0.7">
                    <vertex px="20" py="10"/>
                    ... ...
                </wall>
                <crossing>
                    <vertex px="30" py="10"/>
                    ... ...
                </crossing>
                ... ...
            </room>
            <!-- 障碍物定义 -->
            <obstacle>
                <vertex px="15" py="15"/>
                ... ...
            </obstacle>
            <goals>
                <goal>
                    <vertex px="50" py="10"/>
                    ...
                </goal>
                ...
            </goals>
        </floor>
    </geometry>
</CrowdSimulation>
```
说明：

- `<geometry>` 中当前只能有一个 `<floor>`，后续扩展为多楼层同时仿真是允许多个
- `<floor>` 必须有且只能有一个 `<outwall>`
- `<outwall>` 中可以有多个 `<wall>` 和 `<transition>`
- `<floor>` 中允许有多个 `<room>`
- `<room>` 中允许有多个 `<wall>` 和 `<crossing>`
- `<floor>` 中允许有多个 `<obstacle>`
- `<floor>` 中必须有且只能有一个 `<goals>`
- `<goals>` 中至少要有一个 `<goal>`
- `<wall>`、`<transition>`、`<crossing>`、`<obstacle>`、`<goal>` 中只允许存在 `<vertex>`
- **地图的有效性需要用户保证，程序不进行地图错误检测**

*simulations/ini.xml* 是一个模板，用户可以在其之上进行修改。


