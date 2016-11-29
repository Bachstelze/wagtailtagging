import os

from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse, NoReverseMatch

from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.utils import permission_denied
from wagtail.wagtailsearch.backends import get_search_backends

from django.contrib.auth.models import User, Group
from rest_framework import viewsets

from wagtailtagging.forms import get_image_form
from wagtail.wagtailimages.models import get_image_model
from wagtail.wagtailredirects.permissions import permission_policy
from wagtail.wagtailredirects.views import permission_checker

from wagtailtagging.serializers import UserSerializer, GroupSerializer
from rest_framework import filters

from django.http import HttpResponse
from home.models import ImageSelector, CustomImage, CroppedImage

from grabbing import get_mask_from_image

import numpy as np
import json
from io import BytesIO


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    filter_backends = (filters.DjangoFilterBackend,)


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    filter_backends = (filters.DjangoFilterBackend,)


@permission_checker.require('change')
def edit(request, image_id):
    """copied function from the lib
    added cropped_images for the edit template
    changed the source of the get_image_form method
    """
    Image = get_image_model()
    ImageForm = get_image_form(Image)

    image = get_object_or_404(Image, id=image_id)

    cropped_images = CroppedImage.objects.filter(full_image=image)

    if not permission_policy.user_has_permission_for_instance(request.user, 'change', image):
        return permission_denied(request)

    if request.POST:
        original_file = image.file
        form = ImageForm(request.POST, request.FILES, instance=image, user=request.user)
        if form.is_valid():
            if 'file' in form.changed_data:
                # if providing a new image file, delete the old one and all renditions.
                # NB Doing this via original_file.delete() clears the file field,
                # which definitely isn't what we want...
                original_file.storage.delete(original_file.name)
                image.renditions.all().delete()

                # Set new image file size
                image.file_size = image.file.size

            form.save()

            # Reindex the image to make sure all tags are indexed
            for backend in get_search_backends():
                backend.add(image)

            messages.success(request, _("Image '{0}' updated.").format(image.title), buttons=[
                messages.button(reverse('wagtailimages:edit', args=(image.id,)), _('Edit again'))
            ])

            if request.POST.get("clipping"):
                return redirect("/admin/clipping/"+image_id)
            return redirect('wagtailimages:index')
        else:
            messages.error(request, _("The image could not be saved due to errors."))
    else:
        form = ImageForm(instance=image, user=request.user)

    # Check if we should enable the frontend url generator
    try:
        reverse('wagtailimages_serve', args=('foo', '1', 'bar'))
        url_generator_enabled = True
    except NoReverseMatch:
        url_generator_enabled = False

    if image.is_stored_locally():
        # Give error if image file doesn't exist
        if not os.path.isfile(image.file.path):
            messages.error(request, _(
                "The source image file could not be found. Please change the source or delete the "
                "image."
            ).format(image.title), buttons=[
                messages.button(reverse('wagtailimages:delete', args=(image.id,)), _('Delete'))
            ])

    return render(request, "wagtailimages/images/edit.html", {
        'image': image,
        'cropped_images': cropped_images,
        'form': form,
        'url_generator_enabled': url_generator_enabled,
        'filesize': image.get_file_size(),
        'user_can_delete': permission_policy.user_has_permission_for_instance(
            request.user, 'delete', image
        ),
    })


@permission_checker.require('change')
def clipping(request, image_id):
    """display the clipping interface in the wagtail admin

    :param request: the query from the browser for the clipping interface
    :param image_id: the id of the desired object
    :returns: render object with the image object and all associated cropped images

    """
    image = get_image_model()

    image = get_object_or_404(image, id=image_id)
    cropped_images = CroppedImage.objects.filter(full_image=image)

    return render(request, "drawing.html", {'image': image, 'cropped_images': cropped_images})


def model_json(request, method, object_id):
    """get the models data for preload the next images
    yet not used

    :param request: the query from the browser for the json data
    :param method: chooses which siblings are returned
    :param object_id: the id of the choosen model object
    :returns: HttpResponse with the json data

    """
    model_object = ImageSelector.objects.filter(id=object_id)
    methods = ['get_prev_front_sibling', 'get_next_front_sibling', 'get_next_cutted_siblings',
               'get_prev_cutted_siblings', 'get_next_cutted_front_siblings',
               'get_prev_cutted_front_siblings']
    if len(model_object) == 0 or method not in methods:
        response_dic = {'object': 'not found!'}
    else:
        model_object = model_object[0]
        if method == 'get_prev_front_sibling':
            response_data = [model_object.get_prev_front_sibling()]
        elif method == 'get_next_front_sibling':
            response_data = [model_object.get_next_front_sibling()]
        elif method == 'get_next_cutted_siblings':
            response_data = model_object.get_next_cutted_siblings()
        elif method == 'get_prev_cutted_siblings':
            response_data = model_object.get_prev_cutted_siblings()
        elif method == 'get_next_cutted_front_siblings':
            response_data = model_object.get_next_cutted_front_siblings()
        elif method == 'get_prev_cutted_front_siblings':
            response_data = model_object.get_prev_cutted_front_siblings()

        response_dic = []
        if response_data:
            for response in response_data:
                if response.main_image:
                    image_id = response.main_image.id
                    response_dic.append({'page_id': response.id, 'image_id': image_id})

    response_data = json.dumps(response_dic)
    # return an HttpResponse with the JSON and the correct MIME type
    return HttpResponse(response_data, content_type='application/json')


def create_clipping(request):
    """creates a blanking mask for the given user input

    :param request: the query from the browser for blanking an image
                    it should have selection dic and mask png image
    :returns: HttpResponse with the blanking mask

    """
    if request.method == 'POST':
        image = request.POST.get('image')

        # check if the blanked image should be saved to the backend
        if request.POST.get('save_clipping') in ['false', False]:
            save = False
        else:
            save = True

        selection = {
            'id': int(request.POST.get('selection[id]')),
            'x': int(round(float(request.POST.get('selection[x]')))),
            'y': int(round(float(request.POST.get('selection[y]')))),
            'width': int(round(float(request.POST.get('selection[width]')))),
            'height': int(round(float(request.POST.get('selection[height]')))),
            'full_width': int(round(float(request.POST.get('selection[full_width]')))),
            'full_height': int(round(float(request.POST.get('selection[full_height]'))))
        }

        # get the image id, the model object and the selection from the model
        edit_url = request.POST.get('edit_url')
        image_id = int(edit_url.split("/")[-2])
        image_object = CustomImage.objects.get(id=image_id)
        original_selection = image_object.selections

        reseized_image = image_object.resize_url

        if selection['id'] == -1:  # no selection -> use the whole image
            cropped_image = reseized_image
        else:  # a specific selecion is used -> get the cropped image and selecion attributes
            image_object = CroppedImage.objects.get(id=selection['id'])
            cropped_image = original_selection[unicode(request.POST.get('selection[id]'))]["url"]

        # calculate the new blanking mask
        mask = get_mask_from_image(image, selection, cropped_image, save, image_object)

        # stream the new mask to the output
        stream = BytesIO()
        flat_mask = []
        for line in mask:
            flat_mask.extend(line)
        np.savetxt(stream, flat_mask, fmt="%u", delimiter=', ', newline=', ')
        stream.seek(0)
        return HttpResponse(stream.read())

    return HttpResponse(
            json.dumps({"nothing to see": "this isn't happening"}),
            content_type="application/json"
        )
