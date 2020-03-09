/**
 * Created by gaimeng on 2015/11/3.
 * Some themes for test
 */

//----------------------------theme--------------------------------------

var default2dTheme = {
    name: "2d", //theme's name
    background: "#F2F2F2", //background color

    //building's style
    building: {
        color: "#000000",
        opacity: 0.1,
        transparent: true,
        depthTest: false
    },

    //floor's style
    floor: {
        color: "#E0E0E0",
        opacity: 1,
        transparent: false
    },

    //selected room's style
    selected: "#ffff55",

    // object style
    objectStyle: function(type){
        var result = {
                    color: "#c49c94",
                    opacity: 0.7,
                    transparent: true
        };
        switch(type){
            case "outwall":
                result['color'] = "#423255";
                break;
            case "roomwall":
                result['color'] = "#e8a53a";
                break;
            case "obstacle":
                result['color'] = "#a8834d";
                break;
            case "mid_goal":
                result['color'] = "#c0cbff"
                break;
            case "final_goal":
                result['color'] = "#96cb47"
                break
        }
        return result;
    },
    

    //rooms' style
    // room: function (type, category) {
    //     var roomStyle;
    //     if(!category) {
    //         switch (type) {

    //             case 100: //hollow. u needn't change this color. because i will make a hole on the model in the final version.
    //                 return {
    //                     color: "#F2F2F2",
    //                     opacity: 0.8,
    //                     transparent: true
    //                 }
    //             default :
    //                 break;
    //         }
    //     }

    //     switch(category) {
    //         case 1: // final goal
    //             roomStyle = {
    //                 color: "#5dff00",
    //                 opacity: 0.5,
    //                 transparent: true
    //             };
    //             break;
    //         case 2: // mid goal
    //             roomStyle = {
    //                 color: "#91c8ff",
    //                 opacity: 0.5,
    //                 transparent: true
    //             };
    //             break;
    //         default :
    //             roomStyle = {
    //                 color: "#c49c94",
    //                 opacity: 0.7,
    //                 transparent: true
    //             };
    //             break;
    //     }
    //     return roomStyle;
    // },

    //room wires' style
    strokeStyle: {
        color: "#666666",
        opacity: 0.5,
        transparent: true,
        linewidth: 1
    },

    getStrokeColor: function(walltype){
        color = this.strokeStyle.color;
        if(walltype=='crossing'){
            color = '#00bfff';
        }else if(walltype=='transition'){
            color = "#00ffc1";
        }
        return color;
    },

    fontStyle:{
        opacity: 1,
        textAlign: "center",
        textBaseline: "middle",
        color: "#333333",
        fontsize: 13,
        fontface: "'Lantinghei SC', 'Microsoft YaHei', 'Hiragino Sans GB', 'Helvetica Neue', Helvetica, STHeiTi, Arial, sans-serif  "
    },

    pubPointImg: {

        "11001": System.imgPath+"/toilet.png",
        "11002": System.imgPath+"/ATM.png",
        "21001": System.imgPath+"/stair.png",
        "22006": System.imgPath+"/entry.png",
        "21002": System.imgPath+"/escalator.png",
        "21003": System.imgPath+"/lift.png"
    }
}
var default3dTheme = {
    name: "3d", //theme's name
    background: "#F2F2F2", //background color

    //building's style
    building: {
        color: "#000000",
        opacity: 0.1,
        transparent: true,
        depthTest: false
    },

    //floor's style
    floor: {
        color: "#E0E0E0",
        opacity: 1,
        transparent: false
    },

    //selected room's style
    selected: "#ffff55",

    // walls' style
    subroom_id: 0,
    wall: function(walltype, id){
        subroom_colors = [
            0xfffac8, 0xf2e282, 0xe7b24c,
            0xe1903e, 0xff724e];
        var wallstyle = { 
            color: 0x00bfff, 
            side:THREE.DoubleSide, 
            transparent: true, 
            opacity:0.7
        }; 
        switch(walltype){
            case 'room':
                wallstyle.color = 0x4bb5d9;
                break;
            case 'subroom':
                opacity = 0.45;
                if(id!=undefined){
                    this.subroom_id = id;
                }
                wallstyle.color = subroom_colors[(this.subroom_id++)%subroom_colors.length];
                break;
            case 'transition':
                wallstyle.opacity = 0.5;
                wallstyle.color = 0x00ffc1;
                break;
            case 'crossing':
                wallstyle.opacity = 0.3;
                wallstyle.color = 0x00bfff;
                break;
        }
        return wallstyle;
    },

    // walls' wireframe style
    wallline: function(walltype){
        var walllinestyle = {
            color: 0x101010,
            opacity: 0.9,
            transparent: true,
            linewidth: 2
        }
        switch(walltype){
            case 'room':
                break;
            case 'subroom':
                break;
        }
        return walllinestyle;
    },

    objectStyle: function(type){
        var result = {
                    color: "#c49c94",
                    opacity: 0.8,
                    transparent: true
        };
        switch(type){
            case "outwall":
                result['color'] = "#909090";
                break;
            case "roomwall":
                result['color'] = "#e8a53a";
                break;
            case "obstacle":
                result['color'] = "#f9423d";
                result['transparent'] = false;
                break;
            case "mid_goal":
                result['color'] = "#c0cbff"
                result['opacity'] = 0.5;
                break;
            case "final_goal":
                result['color'] = "#96cb47"
                result['opacity'] = 0.5;
                break
        }
        return result;
    },
    //obstacle' style
    // obstacle: function (type, category) {
    //     var roomStyle;
    //     if(!category) {
    //         switch (type) {

    //             case 100: //hollow. u needn't change this color. because i will make a hole on the model in the final version.
    //                 return {
    //                     color: "#F2F2F2",
    //                     opacity: 0.8,
    //                     transparent: true
    //                 }
    //             default :
    //                 break;
    //         }
    //     }

    //     switch(category) {
    //         case 1: // final goal
    //             roomStyle = {
    //                 color: "#00ff00",
    //                 opacity: 0.5,
    //                 transparent: true
    //             };
    //             break;
    //         case 2: // mid goal
    //             roomStyle = {
    //                 color: "#0000ff",
    //                 opacity: 0.5,
    //                 transparent: true
    //             };
    //             break;
    //         default :
    //             roomStyle = {
    //                 color: "#c49c94",
    //                 opacity: 0.7,
    //                 transparent: true
    //             };
    //             break;
    //     }
    //     return roomStyle;
    // },

    //room wires' style
    strokeStyle: {
        color: "#5C4433",
        opacity: 0.5,
        transparent: true,
        linewidth: 2
    },

    fontStyle:{
        color: "#231815",
        fontsize: 40,
        fontface: "Helvetica, MicrosoftYaHei "
    },

    pubPointImg: {
        "11001": System.imgPath+"/toilet.png",
        "11002": System.imgPath+"/ATM.png",
        "21001": System.imgPath+"/stair.png",
        "22006": System.imgPath+"/entry.png",
        "21002": System.imgPath+"/escalator.png",
        "21003": System.imgPath+"/lift.png"
    }
}
