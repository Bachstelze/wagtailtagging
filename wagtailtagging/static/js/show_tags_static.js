var tags_to_selection = {};
$(document).ready(function() {

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
        $("<div class='template_selection' data-id='"+selection_id+"' title='"+selections[selection_id]['tags']+"'></div>").css(styles).appendTo("#image_container");
        console.log(styles);
        $.each(selections[selection_id]['tags'], function( index, value ){
            if( value in tags_to_selection) {
                tags_to_selection[value].push(selection_id);
            } else {
                tags_to_selection[value] = [selection_id];
            }
        });
    }
    console.log(tags_to_selection);
    $("#image_wrapper").css("width", current_width);
    });
$(document).on('keydown', function(e) {
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
$(".template_tag").hover(function () {//over
    $.each(tags_to_selection[$(this).text()], function(index, value) {
        var selector = '*[data-id="'+value+'"]';
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
function set_selection_style() {

}
function getNumber(input, sub) {
    var len = input.length;
    return parseInt(input.substring(0, len-sub));
}