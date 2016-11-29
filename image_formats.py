# image_formats.py
from wagtail.wagtailimages.formats import Format, register_image_format

register_image_format(Format('standard', 'Standard', 'richtext-image standard', 'width-500'))