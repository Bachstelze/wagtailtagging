from django import forms
from django.forms.models import modelform_factory

from wagtail.wagtailadmin import widgets
from wagtail.wagtailimages.forms import BaseImageForm, formfield_for_dbfield


def get_image_form(model):
    """overwritten method from the lib
    added the JSONField as HiddenInput
    """
    fields = model.admin_form_fields
    if 'collection' not in fields:
        # force addition of the 'collection' field, because leaving it out can
        # cause dubious results when multiple collections exist (e.g adding the
        # document to the root collection where the user may not have permission) -
        # and when only one collection exists, it will get hidden anyway.
        fields = list(fields) + ['collection']

    return modelform_factory(
        model,
        form=BaseImageForm,
        fields=fields,
        formfield_callback=formfield_for_dbfield,
        # set the 'file' widget to a FileInput rather than the default ClearableFileInput
        # so that when editing, we don't get the 'currently: ...' banner which is
        # a bit pointless here
        widgets={
            'tags': widgets.AdminTagWidget,
            'file': forms.FileInput(),
            'focal_point_x': forms.HiddenInput(attrs={'class': 'focal_point_x'}),
            'focal_point_y': forms.HiddenInput(attrs={'class': 'focal_point_y'}),
            'focal_point_width': forms.HiddenInput(attrs={'class': 'focal_point_width'}),
            'focal_point_height': forms.HiddenInput(attrs={'class': 'focal_point_height'}),
            'json': forms.HiddenInput(attrs={'class': 'json_field'})
        })
