var tag_clicked = false;
var selection_clicked = false;
var tags_to_selection = {};
var selection_to_tags = {};
var current_tags = [];
var current_selections = {};
var clicked_id = 0;
var json_message = {"create":{}, "delete":[], "alter":[]};
var new_selection_id = -1;
//object to save the last clicked mouse position to prevent the creation of null selections
var last_click_position = {
    x : 0,
    y : 0,
    height:0,
    width:0
};
//overwritten lib file
var jcropapi;

function setupJcrop(image, original, focalPointOriginal, fields) {
    image.Jcrop({
        //trueSize: [original.width, original.height],
        bgColor: 'rgb(192, 192, 192)',
        onSelect: function(box) {
            console.log("onSelect");
            selection_clicked = true;
            //get all information to calculate the real size of the selection
            var image = $("div.focal-point-chooser img");
            var original = {
                width: image.data('originalWidth'),
                height: image.data('originalHeight')
            };
            var current = {
                width: getNumber(image.css("width"),2),
                height: getNumber(image.css("height"),2)
            };

            var width_factor = original.width/current.width;
            var height_factor = original.height/current.height;

            var holder = $(".jcrop-holder");
            var holder_height = holder.children().first().css("height");
            var holder_width = holder.children().first().css("width");
            var holder_top = holder.children().first().css("top");
            var holder_left = holder.children().first().css("left");

            last_click_position.width = holder_width;
            last_click_position.height = holder_height;
            last_click_position.x = holder_left;
            last_click_position.y = holder_top;

            //calculate the real size
            var real_height = Math.floor(getNumber(holder_height,2)*height_factor);
            var real_width = Math.floor(getNumber(holder_width,2)*width_factor);
            var real_top = Math.floor(getNumber(holder_top,2)*width_factor);
            var real_left = Math.floor(getNumber(holder_left,2)*width_factor);

            if(clicked_id === 0) {//not an old selection is created, so create an new one
                clicked_id = new_selection_id; //set the the new clicked_id
                new_selection_id--; //all new selections have a negative index
                //create a new html selection element
                var new_selection_div = "<div class='selection selected' data-id='"+clicked_id+"'>";
                $(".focal-point-chooser").append(new_selection_div);
            }
            //create a new javscript object with the selection parameters
            var selection = {
                    "id":clicked_id,
                    "height":real_height,
                    "width" :real_width,
                    "x"   :real_left,
                    "y"  :real_top
                };
            //push it to the current_selection dictionary
            if(real_height != -1 && real_width != -1) {
                pushSelection(clicked_id, selection);
                //updateJSON();
            }
            console.log(JSON.stringify(selection));
        },
        onRelease: function(box) {
            console.log("OnRelease");
            selection_clicked = false;
            clicked_id = 0;
        }
    }, function() {
        jcropapi = this
    });
}

$(function() {
    var $chooser = $('div.focal-point-chooser');
    var $indicator = $('.current-focal-point-indicator', $chooser);
    var $image = $('img', $chooser);

    var original = {
        width: $image.data('originalWidth'),
        height: $image.data('originalHeight')
    }

    var focalPointOriginal = {
        x: $chooser.data('focalPointX'),
        y: $chooser.data('focalPointY'),
        width: $chooser.data('focalPointWidth'),
        height: $chooser.data('focalPointHeight')
    }

    var fields = {
        x: $('input.focal_point_x'),
        y: $('input.focal_point_y'),
        width: $('input.focal_point_width'),
        height: $('input.focal_point_height')
    }

    var left = focalPointOriginal.x - focalPointOriginal.width / 2
    var top = focalPointOriginal.y - focalPointOriginal.height / 2
    var width = focalPointOriginal.width;
    var height = focalPointOriginal.height;

    $indicator.css('left', (left * 100 / original.width) + '%');
    $indicator.css('top', (top * 100 / original.height) + '%');
    $indicator.css('width', (width * 100 / original.width) + '%');
    $indicator.css('height', (height * 100 / original.height) + '%');

    var params = [$image, original, focalPointOriginal, fields];

    setupJcrop.apply(this, params)

    $(window).resize($.debounce(300, function() {
        // jcrop doesn't support responsive images so to cater for resizing the browser
        // we have to destroy() it, which doesn't properly do it,
        // so destory it some more, then re-apply it
        jcropapi.destroy();
        $image.removeAttr('style');
        $('.jcrop-holder').remove();
        setupJcrop.apply(this, params)
    }));
});
//end of overwritten lib file
$(document).ready(function() {
    setSelectionStyle();

    //fill tags_to_selection wuth the informations from the server
    $(".selection").each(function(index) {
        var tags = $(this).data("selection-tags").trim().replace(/\s+/g, ' ').split(" ");
        var selection_id = $(this).data("id");
        $.each(tags, function( index, value ){
            if( value in tags_to_selection) {
                tags_to_selection[value].push(selection_id);
            } else {
                tags_to_selection[value] = [selection_id];
            }
            if(selection_id in selection_to_tags) {
                selection_to_tags[selection_id].push(value);
            } else {
                selection_to_tags[selection_id] = [value];
            }
        });
    });

    console.log(JSON.stringify(tags_to_selection));
    $("#id_json").val(JSON.stringify(json_message));

    //create buttons to save, canel and delete the selections
    var  delete_selection = $('<div/>').attr({
            id:'delete_selection',
            type: 'button',
            onClick:'delete_scope();',
            value:'delete scope',
            class:"custom_button_inactive"}).css("margin","5px").html("delete scope");
    var  reset_all = $('<div/>').attr({
            id:'reset',
            type: 'button',
            onClick:'reset_connections();',
            value:'Cancel',
            class:"custom_button_inactive"}).css("margin","5px").html("cancel");
    var  save = $('<div/>').attr({
            id:'save_connections',
            type: 'button',
            onClick:'save_connections();',
            value:'save connections',
            class:"custom_button_inactive"}).css("margin","5px").html("save connections");

    //inner it to the html dom tree
    $(".divider-after .label").after(delete_selection);
    $(".divider-after .label").after(reset_all);
    $(".divider-after .label").after(save);

    //make the tags clickable
    $(document).on('click', '.tag', function(){
        tag_clicked = true;
        var name = $(this).text();
        console.log("tag clicked: " + name + " , current tags: " + current_tags);
        if($.inArray(name, current_tags) == -1) {//tag was not clicked
            current_tags.push(name);
            updateSelected();
            $(this).css("background-color","#666");
        } else {//tag was clicked
            var index = current_tags.indexOf(name);
            current_tags.splice(index, 1);
            $(this).css("background-color","#43b1b0");
            if (current_tags.length == 0) {
                tag_clicked = false;
            }
        }
        updateButtons();
    });

    //allow some functions with the keyboard
    $(document).on('keypress', function(e) {
        if ( e.keyCode === 46 || e.keyCode === 127) {
            delete_scope();
        } else if ( e.keyCode === 13 ) {
            save_connections();
        }
    });

    //make the selections clickable
    $(document).on('click', '.selection', function(){
        clicked_id = $(this).data("id");
        console.log("clicked selection-id: "+clicked_id);

        //get the size of the selections to pass it to the jcrop-api
        var image = $("div.jcrop-holder img");
        var original = {
            width: image.data('originalWidth'),
            height: image.data('originalHeight')
        };
        var current = {
            width: getNumber(image.css("width"),2),
            height: getNumber(image.css("height"),2)
        };
        var selection = {
            x: getNumber($(this).css("left"),2),
            y: getNumber($(this).css("top"),2),
            width: getNumber($(this).css("width"),2),
            height: getNumber($(this).css("height"),2)
        };
        var selectionBox = [
        selection.x,
        selection.y,
        selection.x+selection.width,
        selection.y+selection.height];

        console.log("selectionBox: "+selectionBox);
        if(!(clicked_id in current_selections)) {//selection wasn't clicked
            jcropapi.setSelect(selectionBox);
            $(this).addClass("selected");
            updateSelected();
        } else {//selection was cklicked
            delete current_selections[clicked_id];
            if(Object.keys(current_selections).length === 0) {
                selection_clicked = false;
            }
            clicked_id = 0;
            $(this).removeClass("selected");
        }
        console.log("current selections: "+JSON.stringify(current_selections));
        updateButtons();
    });

    window.onresize = function() {
        setSelectionStyle();
    };
    $(".jcrop-tracker").mousedown(function(e) {
        last_click_position.mouse_x = e.pageX;
        last_click_position.mouse_y = e.pageY;
    });

    $(".jcrop-tracker").mouseup(function(e) {
        if(last_click_position.mouse_x === e.pageX && last_click_position.mouse_y === e.pageY) {
            release_section();
        }
    });

});//end of $(document).ready

function delete_scope() {
    //deletes the focused selection from html and the javscript data objects
    console.log("delete "+clicked_id);
    if (clicked_id>0) {
        json_message.delete.push(clicked_id);
    }
    if (clicked_id in json_message.create) {
        delete json_message.create[clicked_id];
    }
    if (clicked_id in current_selections) {
        delete current_selections[clicked_id];
    }
    $("#id_json").val(JSON.stringify(json_message));
    var selector = '*[data-id="'+clicked_id+'"]';
    $(selector).remove();
    clicked_id = 0;
    jcropapi.release();
    updateButtons();
}

function save_connections() {
    //saves the hightlighted tags and selections as one connection to the json message
    console.log("save and release selections!");
    updateJSON();
    release_section();
    current_tags = [];
    current_selections = {};
    $(".tag").css("background-color","#43b1b0");
    $(".selected").removeClass("selected");
    updateButtons();
}

function reset_connections() {
    //all focused tags and selections are reseted
    console.log("release selections and don't save!");
    release_section();
    current_tags = [];
    current_selections = {};
    $(".tag").css("background-color","#43b1b0");
    $(".selected").removeClass("selected");
    updateButtons();
}
function release_section() {
    //releases the current selection
    console.log("unfocus selection");
    selection_clicked = false;

    //get the size of the selection holder to inner it to the fitting selector element
    var holder_height = $(".jcrop-holder").children().first().css("height");
    var holder_width = $(".jcrop-holder").children().first().css("width");
    var holder_top = $(".jcrop-holder").children().first().css("top");
    var holder_left = $(".jcrop-holder").children().first().css("left");
    var styles = {
        top : holder_top,
        left: holder_left,
        height: holder_height,
        width: holder_width
    };
    if (holder_height == "0px") {
        styles.height = last_click_position.height;
        styles.width = last_click_position.width;
        styles.top = last_click_position.y;
        styles.left = last_click_position.x;
    }
    var selector = '*[data-id="'+clicked_id+'"]';
    $(selector).css(styles);
    jcropapi.release();
}
function setSelectionStyle() {
    "use strict";
    //sets the size of the html selection elements to the given data size
    var image = $("div.focal-point-chooser img");
    var original = {
        width: image.data('original-width'),
        height: image.data('original-height')
    };
    var current = {
        width: getNumber(image.css("width"),2),
        height: getNumber(image.css("height"),2)
    };
    $(".selection").each(function( index ) {
        var selection_width = $(this).data('selection-width');
        var selection_height = $(this).data('selection-height');

        var style_left = Math.floor($(this).data('selection-x') * current.width / original.width) + 'px';
        var style_top = Math.floor($(this).data('selection-y') * current.height / original.height) + 'px';
        var style_width = Math.floor(selection_width * current.width / original.width) + 'px';
        var style_height = Math.floor(selection_height * current.height / original.height) + 'px';
        //smaller selections have a bigger z-index
        var style_z_index = Math.floor(500 - selection_height/100 - selection_width/100);

        var styles = {
            left: style_left,
            top: style_top,
            width: style_width,
            height: style_height
        };
        //set the styling
        $(this).css(styles);
        $(this).css("z-index",style_z_index);
    });
}
function updateSelected() {
    "use strict";
    //focus the tags and selection with a connection the current focused
    console.log("updateSelected");

    for (var entry_selection in current_selections) {
        if (entry_selection in selection_to_tags) {
            selection_to_tags[entry_selection].forEach(function(tag) {
                if (current_tags.indexOf(tag) == -1) {
                    var selector = ".tag:contains('"+tag+"')";
                    $(selector).trigger("click");
                }
            })
        }
    }
    current_tags.forEach(function(entry_tag) {
        if (entry_tag in tags_to_selection) {
            tags_to_selection[entry_tag].forEach(function(selection_id) {
                if (!(selection_id in current_selections)) {
                    var selector = '*[data-id="'+selection_id+'"]';
                    $(selector).trigger("click");
                }
            });
        }
    });

}
function updateJSON() {
    /*
    write the current selections to the json message
    for each selection a cropped_image object is saved
    var cropped_image = {
        tags:[],
        x:-1,
        y:-1,
        width:-1,
        height:-1
    };*/
    console.log("updateJSON!");
    for (key in current_selections) {
        var cropped_image = {
                tags:current_tags,
                x:current_selections[key]["x"],
                y:current_selections[key]["y"],
                width:current_selections[key]["width"],
                height:current_selections[key]["height"]
        };
        json_message["create"][key] = cropped_image;
        //update tags_to_selection
        current_tags.forEach(function(entry_tag) {
            if (entry_tag in tags_to_selection && tags_to_selection[entry_tag].indexOf(key) == -1) {
                tags_to_selection[entry_tag].push(key);
            } else {
                tags_to_selection[entry_tag] = [key];
            }
            //update selection_to_tags
            if(key in selection_to_tags && selection_to_tags[key].indexOf(entry_tag) == -1) {
                selection_to_tags[key].push(entry_tag);
            } else {
                selection_to_tags[key] = [entry_tag];
            }

        });
    }
    //write the message to the json field
    $("#id_json").val(JSON.stringify(json_message));
    console.log("json_message: "+JSON.stringify(json_message));
}
function updateButtons() {
    //toggles the states of the buttons
    if(current_tags.length > 0) {
        $("#reset").attr("class","custom_button");
    } else {
        $("#save_connections").attr("class","custom_button_inactive");
    }
    if(Object.keys(current_selections).length > 0) {
        $("#reset").attr("class","custom_button");
        $("#delete_selection").attr("class","custom_button");
    } else {
        $("#save_connections").attr("class","custom_button_inactive");
        $("#delete_selection").attr("class","custom_button_inactive");
    }
    if(Object.keys(current_selections).length > 0 && current_tags.length > 0) {
        $("#save_connections").attr("class","custom_button");
    }
    if(Object.keys(current_selections).length == 0 && current_tags.length == 0) {
        $("#reset").attr("class","custom_button_inactive");
    }
}
function pushSelection(selection_id, selection) {
    //pushes the given selection to the json_message
    console.log("pushSelection: "+selection);
    current_selections[String(selection_id)] = selection;
    if (selection_id in json_message["create"]) {
        json_message["create"][selection_id]["width"] = selection["width"];
        json_message["create"][selection_id]["height"] = selection["height"];
        json_message["create"][selection_id]["x"] = selection["x"];
        json_message["create"][selection_id]["y"] = selection["y"];
    }
}
function getNumber(css, sub) {
    var len = css.length;
    return parseInt(css.substring(0, len-sub));
}