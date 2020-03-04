<!--
 * @Description: 
 * @Author: Huabin Feng
 * @Email: fenghb@mail.ustc.edu.cn
 * @Date: 2020-02-23 16:26:56
 * @LastEditTime: 2020-02-25 11:55:40
 -->
# data格式说明

```json
{
    "data":{
        "Floors":[
            {
                "_id": 1,
                "Name": "F1",
                "High": 4,
                "FuncAreas":[
                    {
                        "Category": 102,
                        "Outline":[[[
                            200, 200,
                            200, -200,
                            -200, -200
                        ]]],
                        "Center": [100, 200],
                        "Name_en": "3d Name",
                        "Name": "2d Name",
                        // 设置为非闭合
                        "Open": ture,
                        "Wall": "room"
                    }
                ],
                "PubPoint":[],
                "Outline": [[[
                    400, 400,
                    400, -400,
                    -400, -400,
                    -400, 400
                ]]]
            }
            
        ]
        "building":{
            "FrontAngle": -0.437,
            "DefaultFloor":1,
            "Scale3D": 1.3, // 3D 场景的放大倍数
            "TranslateX": 0,
            "TranslateY": 0,
            "TranslateZ": -30,
            "Outline": [[[
                500, 500,
                500, -500,
                -500, -500,
                -500, 500
            ]]]
        }
    }
}
```


