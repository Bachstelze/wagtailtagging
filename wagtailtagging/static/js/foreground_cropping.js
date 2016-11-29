var original_canvas;
var first_draw = true;
var zoomLevel = 1;
var localPos = {
    x : 0,
    y : 0
};
var reset_x = 0;
var reset_y = 0;
var background_canvas_value = 100;
var foreground_canvas_value = 48;

$(document).ready(function() {
    var first_selection = get_selection(-1);

    $('#clipping_form').on('submit', function(event){
        event.preventDefault();
        console.log("form submitted!")  // sanity check
        //create_post();
    });
    $('#drop_down').on('change', function() {
        console.log( this.value ); // or $(this).val()
        console.log( $("option:selected", this)[0].id );
        var id = $("option:selected", this)[0].id
        var new_selection = get_selection(id);

        clear_canvas(new_selection);
    });
    $("#original_image").load(function() {
        init_konvas(first_selection);
    });
});

function clear_canvas(selection) {
    //reset old canvas and settings
    $("canvas").remove();
    $('#calculate_button').unbind('click', calculate);
    $('#save_button').unbind('click', save);
    original_canvas = [];
    first_draw = true;

    init_konvas(selection);
}

function get_selection(id) {
    console.log(id);
    var original_image = $("#original_image");
    if(id == -1) {
        var selection = {
            id:-1,
            aspect:1,
            x: 0,
            y: 0,
            width:original_image.data("original-width"),
            height:original_image.data("original-height"),
            full_width:original_image.data("original-width"),
            full_height:original_image.data("original-height")
        };
    } else {
        console.log("set selection of cropped image!");
        var selected = selections[id];
        console.log(selected);
        var selection = {
            id:id,
            aspect:1,
            x: selected["x"],
            y: selected["y"],
            width:selected["width"],
            height:selected["height"],
            full_width:original_image.data("original-width"),
            full_height:original_image.data("original-height")
        }
    }
    console.log(selection);
    return selection;
}

function create_post(message) {
    console.log("create post is working!") // sanity check
    $.ajax({
        url : "../../../get_foreground/", // the endpoint
        type : "POST", // http method
        data : message, // data sent with the post request

        // handle a successful response
        success : function(img) {
            $('#post_text').val(''); // remove the value from the input
            console.log("success"); // another sanity check
            drawImage(img);
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            $('#results').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: "+errmsg+
                " <a href='#' class='close'>&times;</a></div>"); // add the error to the dom
            console.log(xhr.status); // provide a bit more info about the error to the console
        }
    });
};

function drawImage(img){
    var splitted = img.split(", ")
    var canvas = $("canvas")[0];
    var context = canvas.getContext('2d');
    var canvasData = context.getImageData(0, 0, canvas.width, canvas.height);
    console.log("splitted: "+splitted.length*4);
    var new_bitmap = context.createImageData(canvasData);
    if(first_draw) {
        original_canvas = []; // An new empty array
        for (var i = 0, len = canvasData.data.length; i < len; i++) {
            original_canvas[i] = canvasData.data[i];
        }
        // original_canvas = JSON.parse(JSON.stringify(canvasData.data));
        var imageData = canvasData.data;
        first_draw = false;
    } else {
        var imageData = [];
        for (var i = 0, len = canvasData.data.length; i < len; i++) {
            imageData[i] = original_canvas[i];
        }
        console.log("get_old");
    }
    console.log("original: "+canvasData.data.length);
    for(var pixel = 0; pixel<canvasData.data.length; pixel+=4) {
        if(parseInt(splitted[pixel/4]) == 2) {
            if(pixel/4%2 == 0) {
                imageData[pixel] = 10;
                imageData[pixel+1] = 10;
                imageData[pixel+2] = 10;
                imageData[pixel+3] = 255;
            }
//            if(pixel/4%4 == 2) {
//                imageData.data[pixel] = 255;
//                imageData.data[pixel+1] = 255;
//                imageData.data[pixel+2] = 255;
//                imageData.data[pixel+3] = 255;
//            }
        }
    }

    new_bitmap.data = imageData;
    for (var i = 0, len = canvasData.data.length; i < len; i++) {
        new_bitmap.data[i] = imageData[i];
    }
    context.putImageData(new_bitmap, 0, 0);
}

function init_konvas(selection) {
    Konva.showWarnings = true;
    var width = selection["width"];
    var height = selection["height"];
    console.log(width);
    var border = 1175;
    if(width>border) {
        var aspect = height/width;
        var scale = border/width;
        width = border;
        height = border*aspect;

        selection["scale"] = scale;
        selection["border"] = border;
        selection["aspect"] = aspect;
        selection["full_width"] = selection["full_width"]*scale;
        selection["full_height"] = selection["full_height"]*scale;
        selection["x"] = selection["x"]*scale;
        selection["y"] = selection["y"]*scale;

        if(selection["id"] == -1) {
            selection["width"] = width;
            selection["height"] = height;
        }
    }

    // first we need Konva core things: stage and layer
    var stage = new Konva.Stage({
      container: 'container',
      width: width,
      height: height
    });
    setImage(stage, selection);

    var layer = new Konva.Layer();
    stage.add(layer);


    // then we are going to draw into special canvas element
    var canvas = document.createElement('canvas');
    canvas.setAttribute("id", "brush_canvas");
    $("canvas").last().attr("id","brush_canvas");
    canvas.width = width;
    canvas.height = height;
    canvas.style.opacity = 0.5;

    // creted canvas we can add to layer as "Konva.Image" element
    var image = new Konva.Image({
        image: canvas,
        x : 0,
        y : 0,
        stroke: 'rgb(100,200,215)',
        shadowBlur: 0
    });
    layer.add(image);
    layer.moveToTop();
    stage.draw();

    // Good. Now we need to get access to context element
    var context = canvas.getContext('2d');
    context.strokeStyle = "rgb(100,200,215)";
    context.lineJoin = "round";
    context.lineWidth = 20;


    var isPaint = false;
    var lastPointerPosition;
    var mode = 'brush';


    // now we need to bind some events
    // we need to start drawing on mousedown
    // and stop drawing on mouseup
    stage.on('contentMousedown.proto', function(e) {
        if( e.evt.button == 0 ) {
          isPaint = true;
          lastPointerPosition = stage.getPointerPosition();
        }
    });

    stage.on('contentMouseup.proto', function(e) {
        if( e.evt.button == 0 ) {
          isPaint = false;
        }
    });

    // and core function - drawing
    stage.on('contentMousemove.proto', function() {

      if (!isPaint) {
        return;
      }

      if (mode === 'brush') {
        context.globalCompositeOperation = 'source-over';
      }
      if (mode === 'eraser') {
        context.globalCompositeOperation = 'destination-out';
      }
      context.beginPath();

      localPos = {
        x: (lastPointerPosition.x - image.x()+reset_x)/zoomLevel,
        y: (lastPointerPosition.y - image.y()+reset_y)/zoomLevel
      };
      context.moveTo(localPos.x, localPos.y);
      var pos = stage.getPointerPosition();
      localPos = {
        x: (pos.x - image.x()+reset_x)/zoomLevel,
        y: (pos.y - image.y()+reset_y)/zoomLevel
      };
      context.lineTo(localPos.x, localPos.y);
      context.closePath();
      context.stroke();


      lastPointerPosition = pos;
      layer.draw();
    });

    //set eventhandlers to the buttons above the canvas
    $(document).on('click', '#foreground_button', function(){
        mode = 'brush';
        context.strokeStyle = "rgb(48,48,48)";
    });
    $(document).on('click', '#background_button', function(){
        mode = 'brush';
        context.strokeStyle = "rgb(100,200,215)";
    });
    $(document).on('click', '#eraser_button', function(){
        mode = 'eraser';
    });
    $("#brush_size").change(function() {
        context.lineWidth = $( this ).val();
    });

    var data_object = {context:context, canvas:canvas, selection:selection, stage:stage};
    $('#calculate_button').bind('click', data_object, calculate);
    $('#save_button').bind('click', data_object, save);

//     $("canvas").mousedown(function(e){
//        if( e.button == 2 ) {
//            e.preventDefault();
//            alert('Right mouse button!');
//            return false;
//        }
//        return true;
//    });

    $("canvas").on("contextmenu",function(e){
    e.preventDefault();
    if(zoomLevel>1) {
        stage.x(0);
        stage.y(0);
        reset_x = 0;
        reset_y = 0;
        zoom(stage,1);
    } else { // zoomLevel == 1
        zoom(stage,2);
        var pos = stage.getPointerPosition();
        stage.x( - (pos.x)*1);
        stage.y( - (pos.y)*1);
        reset_x = pos.x;
        reset_y = pos.y;
        stage.draw();
    }
        return false;
    });
}

function zoom(stage, level) {
    zoomLevel = level;
    stage.scale({
        x : zoomLevel,
        y : zoomLevel
    });
    stage.draw();

    localPos = {
        x: localPos.x/zoomLevel,
        y: localPos.y/zoomLevel
      };
}
function setImage(stage, selection) {
    console.log("set Image !");
    console.log(selection["id"]);
    var original_image = $("#original_image");

    console.log(original_image.data("original-height"));
    var konva_image = new Konva.Image({
        x: selection["x"]*-1,
        y: selection["y"]*-1,
        image: document.images.original_image,
        width: selection["full_width"],
        height: selection["full_height"]
      });
    var layer = new Konva.Layer();

    var group = new Konva.Group({
//        clip: {
//            x:0,
//            y:0,
//            width: selection["width"],
//            height: selection["height"]
//        },
        draggable: false
    });
    group.add(konva_image);
    layer.add(group);
//    layer.x(selection["x"]*-1);
//    layer.y(selection["y"]*-1);
    stage.add(layer);
    layer.moveDown();
    layer.draw();
}

function calculate_image(selection, canvas, save_clipping) {
    var image = canvas.toDataURL();
    var edit_url = window.location.href;
    var json_selection = JSON.stringify(selection);
    var message = '{ "image" : "'+image+
        '","selection" : '+json_selection +
        ', "edit_url": "'+ edit_url+
        '","save_clipping" : '+save_clipping +
        ' }';
    var message_obj = jQuery.parseJSON( message );
    console.log(message_obj);
    return message_obj;
}

function Create2DArray(rows) {
  var arr = [];

  for (var i=0;i<rows;i++) {
     arr[i] = [];
  }

  return arr;
}

/* functions to bind and unbind to the buttons*/

function calculate(event) {
    var context = event.data.context;
    var canvas = event.data.canvas;
    var selection = event.data.selection;
    var stage = event.data.stage;
    var imgData = context.getImageData(0, 0, canvas.width, canvas.height);
    //var message = calculate_message(imgData, selection);
    var image_message = calculate_image(selection, canvas, false);
    create_post(image_message);
    stage.x(0);
    stage.y(0);
    reset_x = 0;
    reset_y = 0;
    zoom(stage,1);
}

function save(event) {
    var selection = event.data.selection;
    var stage = event.data.stage;

    var context = event.data.context;
    var canvas = event.data.canvas;
    var imgData = context.getImageData(0, 0, canvas.width, canvas.height);
    var canvas_width = canvas.width;
    var canvas_height = canvas.height;

    var stroked = are_selections_stroke(imgData, canvas_width, canvas_height);

    if(!stroked) {//test whether foreground and background are set
        alert("Bitte Vordergrund und Hintergrund markieren!");
    } else {
        var image_message = calculate_image(selection, canvas, true);
        create_post(image_message);
        stage.x(0);
        stage.y(0);
        reset_x = 0;
        reset_y = 0;
        zoom(stage,1);
    }
}
function are_selections_stroke(bitmap, canvas_width, canvas_height) {
    var data = bitmap["data"];
    var is_background_set = false;
    var is_foreground_set = false;

    for(var column_index=0; column_index<canvas_height;column_index++) {
        var row = new Array();
        for(var row_index=0; row_index<canvas_width;row_index++) {
            if(data[(column_index*canvas_width+row_index)*4] == background_canvas_value) {
                is_background_set = true;
                if(is_background_set && is_foreground_set) {
                    return true;
                }
            } else if(data[(column_index*canvas_width+row_index)*4] == foreground_canvas_value) {
                is_foreground_set = true;
                if(is_background_set && is_foreground_set) {
                    return true;
                }
            }
        }
    }
    return false;
    }

function calculate_message(bitmap, selection) {
    /* old function to convert the canvas bitmap to the mask for grabCut
    is now calculated on the server */
    console.log("bitmap shape: "+bitmap.data.length);
    console.log("selection length: "+(selection["width"]*selection["height"])*4);
    var row_length = selection["width"];
    var column_length = selection["height"];
    var mask = Create2DArray(column_length);
    for(var column_index=0; column_index<column_length;column_index++) {
        var row = new Array();
        for(var row_index=0; row_index<row_length;row_index++) {
            if(bitmap["data"][(column_index*row_length+row_index)*4] == 100) {
                row.push(0);
            } else if(bitmap["data"][(column_index*row_length+row_index)*4] == 0) {
                row.push(2);
            } else if(bitmap["data"][(column_index*row_length+row_index)*4] == 48) {
                row.push(1);
            } else if(bitmap["data"][(column_index*row_length+row_index)*4] == 52) {
                row.push(3);
            } else {
                //console.log(bitmap["data"][(column_index*column_length+row_index)*4]);
                //console.log(column_index, row_index);
                row.push(2);
            }
        }
        mask[column_index] = row;
    }
    var json_mask = JSON.stringify(mask);
    var json_selection = JSON.stringify(selection);

    var edit_url = window.location.href;
    var message = '{ "data" : "'+json_mask+
        '","selection" : '+json_selection +
        ', "edit_url": "'+ edit_url+
        '" }';
    var message_obj = jQuery.parseJSON( message );
    console.log(message_obj);
    return message_obj;
}