var tags_to_selection = {};
$(document).ready(function() {

    set_selections();
    calculate_tags_to_selection();
    //preload();
});
function set_selections() {
/*
* calculates the size off the displayed image
* the size is transfered to selection boxes or blanked images
*/
    var image = $("#image_container img");
    var current_width = getNumber(image.css("width"),2);
    var current_height = getNumber(image.css("height"),2);

    var width_factor = current_width/original_width;
    var height_factor = current_height/original_height;

    for(var selection_id in selections) {
        //console.log(selections[selection_id]);
        var styles = {
            height: Math.floor(selections[selection_id]["height"]*height_factor),
            width: Math.floor(selections[selection_id]["width"]*width_factor),
            top: Math.floor(selections[selection_id]["y"]*height_factor),
            left: Math.floor(selections[selection_id]["x"]*width_factor),
        }
        //$("#image_container").append("<div class='template-selection'></div>");
        var selection_outline = "<div class='template_selection' data-id='"+selection_id+
            "' title='"+selections[selection_id]['tags']+"'></div>";
        var selector = '*[data-id="'+selection_id+'"]';
        if(!$(selector).length) {
            $(selection_outline).appendTo("#image_container");
        }
        $(selector).css(styles).css("opacity","0");
        console.log(styles);
    }
    console.log(tags_to_selection);
    $("#image_wrapper").css("width", current_width);
}
function calculate_tags_to_selection() {
/*
* out of the selection json printed from django in the document a mapping from
* tags to selection is created
* out of this data all tags with no specific selection (only the document) are calculated
*
* if more data transfer like this rises it should replaced by backbone.js or familar framework
*/
    console.log("only general tags:");
    console.log(tags_to_selection);
    //add tags from the selections
    for(var selection_id in selections) {
        $.each(selections[selection_id]['tags'], function( index, value ){
            if( value in tags_to_selection) {
                tags_to_selection[value].push(selection_id);
            } else {
                tags_to_selection[value] = [selection_id];
            }
        });
    }

    //remove all tags with a selection from the all_tags variable
    for(var tag in tags_to_selection) {
        remove(tag, all_tags);
        console.log(tag);
        console.log("delete tag"+tag);
    }
    //add the tags from the image
    remove("general_tag", all_tags);
    for(var tag_index in all_tags) {
        tags_to_selection[all_tags[tag_index]] = [-1];
        console.log(all_tags[tag_index]);
    }
    console.log(tags_to_selection);
}

function remove(val, array_object) {
/*
* removes the value from the array object
*/
    var i = array_object.indexOf(val);
         return i>-1 ? array_object.splice(i, 1) : [];
};

$(document).on('keydown', function(e) {
/*
* get keyboard input to navigate through the site
*/
    if ( e.keyCode === 39 || e.keyCode === 68 ) {
        if(right_url != "..//#" && right_url != "..//?front=true#") {
            //var stateObj = { title: right_title };
            //history.pushState(stateObj, right_title, right_url);
            window.location.href = right_url;
        }
    } else if ( e.keyCode === 37 || e.keyCode === 65 ) {
        if(left_url != "..//#" && left_url != "..//?front=true#") {
            window.location.href = left_url;
        }
    }
});

function preload() {
/*
* possible feature
* preload the image before and after the current image
* server endpoint for this feature: 'json/method/object_id/'
* allowed methods = ['get_prev_front_sibling','get_next_front_sibling','get_next_cutted_siblings',
               'get_prev_cutted_siblings','get_next_cutted_front_siblings',
               'get_prev_cutted_front_siblings']
*/
var page_id = window.location.href.split("/")[3].split("-")[1];
$.getJSON( "http://127.0.0.1:8000/api/v1/pages/"+page_id+"?format=json", function( data ) {
console.log(data);
  var items = [];
  $.each( data, function( key, val ) {
    items.push( "<li id='" + key + "'>" + val + "</li>" );
  });

//  $( "<ul/>", {
//    "class": "my-new-list",
//    html: items.join( "" )
//  }).appendTo( "body" );
});
}

/*
* displays the selection or blanke image for the selected tag
* if the tag has no specific selection the blanked image for the whole image is displayed
*/
$(".template_tag").hover(function () {//over
    $.each(tags_to_selection[$(this).text()], function(index, value) {
        var selector = '*[data-id="'+value+'"]';
        console.log(selector);
        $(selector).css("opacity","1");
    });
    },
    function () {//out
    $.each(tags_to_selection[$(this).text()], function(index, value) {
        var selector = '*[data-id="'+value+'"]';
        $(selector).css("opacity","0");
    });
    }
);

function getNumber(input, sub) {
/*
* input should be a css value
* return the integer without px declaration
*/
    var len = input.length;
    return parseInt(input.substring(0, len-sub));
}