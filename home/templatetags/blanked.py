from django import template
from django.utils.html import format_html

register = template.Library()


@register.simple_tag(takes_context=True)
def get_blanked(context, image_object):
    # render the blanked images to the template
    # the width and height are setted trough javascript given that they depend on the users browser
    blanked = ""
    img = """<img class='blanked_image' data-id='%s'
    title='%s' src='%s' style='%s'>"""
    selections = image_object.selections
    print(selections)
    if 'blanked_url' in selections:  # blanked image for the full image
        css = "top:0px; left:0px;"
        src = '../../'+image_object.selections['blanked_url']
        title = ""
        blanked = img % (-1, title, src, css)
    for selection_id in selections:  # iterate all selections and check if there is a blanked image
        if selection_id.isdigit() and selections[selection_id].has_key("blanked_url"):
            src = '../../'+image_object.selections[selection_id]['blanked_url']
            title = selections[selection_id]["tags"][0]
            blanked += img % (selection_id, title, src, "")
    return format_html(blanked)
