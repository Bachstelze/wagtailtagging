from __future__ import unicode_literals

from django.db import models
from django.forms import CheckboxInput
from django.db.models import BooleanField
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from wagtail.wagtailcore.models import Page
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailsearch import index

from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver

from wagtail.wagtailimages.models import Image, AbstractImage, AbstractRendition
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from django.contrib.postgres.fields import JSONField

from datetime import date

from wagtail.wagtailcore.fields import StreamField
from wagtail.wagtailcore import blocks
from wagtail.wagtailadmin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.wagtailimages.blocks import ImageChooserBlock

from django.utils.text import slugify

import json
from django.core.files import File


class HomePage(Page):
    """Landing Page of wagtailTagging

    There are only displayed the menu and the first 100 thumbnails with headers.
    You can browse it normal mode or in front mode ?front=true
    """
    def get_last_children(self):
        """returns 100 children pages of Homepage"""
        try:
            return self.get_children().specific().reverse()[0:100]
        except IndexError:
            return []

    def get_last_front_children(self):
        """returns 100 children pages of Homepage with the front flag"""
        try:
            return ImageSelector.objects.filter(front=True).reverse()[0:100]
        except IndexError:
            return []


class StreamPage(Page):
    """just a testing page"""
    body = StreamField([
        ('heading', blocks.CharBlock(classname="full title")),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
    ])
    content_panels = Page.content_panels + [
        StreamFieldPanel('body')
    ]


class ImageSelector(Page):
    """Page of a specific page
    In the ImageSelectorPage a resized image with all its information is displayed
    Has like the Homepage two modes: all and front
    """
    main_image = models.ForeignKey(
        'home.CustomImage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    front = models.BooleanField(default=False, editable=True)
    date = models.DateField("Post date", default=date.today)
    intro = models.CharField(max_length=250, blank=True)
    body = RichTextField(blank=True)

    search_fields = Page.search_fields + (
        index.SearchField('intro'),
        index.SearchField('body'),
    )

    content_panels = Page.content_panels + [
        FieldPanel('front', widget=CheckboxInput),
        FieldPanel('date'),
        FieldPanel('intro'),
        ImageChooserPanel('main_image'),
        FieldPanel('body', classname="full")
    ]
    api_fields = ('main_image', 'body', 'front', 'date', 'intro')

    def get_prev_front_sibling(self):
        """method for javascript navigation
        :return previous ImageSelector with a front flag"""
        for image_page in self.get_prev_siblings().specific():
            if image_page.front:
                return image_page
        return None

    def get_next_front_sibling(self):
        """method for javascript navigation
        :return next ImageSelector with a front flag"""
        print 'get next'
        for image_page in self.get_next_siblings().specific().reverse():
            if image_page.front:
                return image_page
        return None

    def get_next_cutted_siblings(self):
        """:return next 50 siblings to display thumbnails"""
        next_siblings = self.get_next_siblings().specific().reverse()
        len_next = len(next_siblings)
        start = len_next-50 if len_next-50 > 0 else 0
        return next_siblings[start:len_next]

    def get_prev_cutted_siblings(self):
        """:return previous 50 siblings to display thumbnails"""
        return self.get_prev_siblings().specific()[0:50]

    def get_next_cutted_front_siblings(self):
        """:return next 50 siblings with front flag to display thumbnails"""
        result = []
        for image_page in self.get_next_siblings().specific().reverse():
            if image_page.front:
                result.append(image_page)
            if len(result) > 50:
                break
        return result

    def get_prev_cutted_front_siblings(self):
        """:return previous 50 siblings with front flag to display thumbnails"""
        result = []
        for image_page in self.get_prev_siblings().specific():
            if image_page.front:
                result.append(image_page)
            if len(result) > 50:
                break
        return result


class BlankedImage(AbstractImage):
    """Modelclass to store the clippings made in drawing.html

    Attributes:
        full_image  ForeignKey to the main image
        left        left position value from the scope in the main image
        top         top position value from the scope in the main image
    """
    image_type = models.ForeignKey(ContentType)
    image_id = models.PositiveIntegerField()
    image_object = GenericForeignKey('image_type', 'image_id')
    left = models.IntegerField(default=0)
    top = models.IntegerField(default=0)
    admin_form_fields = Image.admin_form_fields + (

    )


class BlankedRendition(AbstractRendition):
    image = models.ForeignKey(BlankedImage, related_name='renditions')

    class Meta:
        unique_together = (
            ('image', 'filter', 'focal_point_key'),
        )


class CustomImage(AbstractImage):
    """Own imageclass

    Attributes:
        json        JSONField to get the informations from edit.html
        selections  JSONField to display the selections made in edit.html in the Rest-API
        thumb_url   CharField could be used for javscript loading of an ImageSelectorPage
        resize_url   CharField could be used for javscript loading of an ImageSelectorPage

    """
    blanked_image = models.ForeignKey(BlankedImage, null=True, blank=True)
    json = JSONField(blank=True, null=True, default={})
    selections = JSONField(blank=True, null=True, default={})
    has_page = BooleanField(default=False)
    thumb_url = models.CharField(max_length=250, blank=True)
    resize_url = models.CharField(max_length=250, blank=True)
    blanked_url = models.CharField(max_length=250, blank=True)
    admin_form_fields = Image.admin_form_fields + (
        'json',
    )

    api_fields = ('selections', 'filename', 'thumb_url', 'resize_url', 'blanked_url', 'tags')

    # search_fields = Page.search_fields + ( # Inherit search_fields from Page
    #     index.SearchField('selections'),
    #     index.FilterField('date'),
    # )

    def get_selections(self):
        return json.dumps(self.selections)


class CustomRendition(AbstractRendition):
    image = models.ForeignKey(CustomImage, related_name='renditions')

    class Meta:
        unique_together = (
            ('image', 'filter', 'focal_point_key'),
        )


class CroppedImage(AbstractImage):
    """Modelclass to store the selections made in edit.html

    Attributes:
        full_image  ForeignKey to the main image
        left        left position value from the scope in the main image
        top         top position value from the scope in the main image
    """
    full_image = models.ForeignKey(CustomImage, default=1)
    blanked_image = models.ForeignKey(BlankedImage, null=True, blank=True)
    blanked_url = models.CharField(max_length=250, blank=True)
    left = models.IntegerField(default=0)
    top = models.IntegerField(default=0)
    admin_form_fields = Image.admin_form_fields + (

    )


class CroppedRendition(AbstractRendition):
    image = models.ForeignKey(CroppedImage, related_name='renditions')

    class Meta:
        unique_together = (
            ('image', 'filter', 'focal_point_key'),
        )


def update_blanked_image(file_path, image_object, object_id):
    # Open an existing file using Python's built-in open() and save it to the model BlankedImage
    f = open(file_path)
    blanked_file = File(f)

    blanked_model_object = BlankedImage.objects.create(image_object=image_object, file=blanked_file)
    image_object.blanked_image = blanked_model_object
    image_object.blanked_image.save()

    if object_id == -1:
        image_object.selections["blanked_url"] = file_path
    else:
        image_object.full_image.selections[str(object_id)]["blanked_url"] = file_path
        image_object.full_image.save()

    image_object.blanked_url = file_path
    image_object.save()


@receiver(post_save, sender=CustomImage)
def post_save_image(sender, instance, **kwargs):
    """own hook, is called after an image is saved
    if the save call comes from edit.html create_cropped_image() is called.
    Else the call comes from the image uploader, so a new ImageSelectorPage is created.
    """
    if instance.json and 'endrecursion' in instance.json:
        # every create_cropped_image() call saves the image once again
        print 'end recursion'
    elif instance.json and not ('endrecursion' in instance.json):
        print 'create cropped'
        create_cropped_image(sender, instance)
    elif not instance.has_page:
        create_page(sender, instance)


def create_page(sender, instance):
    """a new ImageSelectorPage is created"""
    raw_title = instance.title.split(".")[0]
    title = raw_title[0].upper()+raw_title[1:]
    title = title.replace("_", " ")

    page_creation = ImageSelector.objects.get(id=4)
    new_page_creation = page_creation.copy(
        update_attrs={'title': title, 'slug': instance.id})
    new_page_creation.main_image = instance
    new_page_creation.front = False
    new_page_creation.intro = ""
    new_page_creation.body = ""
    new_page_creation.save()

    page_object = ImageSelector.objects.get(slug=instance.id)
    slug = '%s-%s-%s' % (raw_title, page_object.id, instance.id)

    new_page_creation.slug = slugify(slug, allow_unicode=False)
    new_page_creation.set_url_path(new_page_creation.get_parent())
    new_page_creation.save()

    instance.has_page = True

    # predefinition of the thumb and resized image
    if not instance.thumb_url:
        filter_spec = "fill-200x200"
        rendition_file = instance.get_rendition(filter_spec).file
        # set url for the rest api
        instance.thumb_url = 'media/images/'+rendition_file.path.split("/")[-1]

        filter_spec = "max-1500x800"
        rendition_file = instance.get_rendition(filter_spec).file
        # set url for the rest api
        instance.resize_url = 'media/images/'+rendition_file.path.split("/")[-1]
        print 'thumb created'

    instance.save()


def create_cropped_image(sender, instance):
    """
    if the create_json_message is set the model gets updated
    this could be:
    creation of a new section as a CroppedImage
    alteration of an existing section
    deletion of an existing section
    :param sender: the main model class of the parent image
    :param instance: the precise parent image object
    """
    print instance.json

    if instance.json:
        json_message = instance.json
        old_focal_point_x = instance.focal_point_x
        old_focal_point_y = instance.focal_point_y
        old_focal_point_width = instance.focal_point_width
        old_focal_point_height = instance.focal_point_height

        for selection_id in json_message['create']:
            selection = json_message['create'][selection_id]
            print selection

            height = int(selection["height"])
            width = int(selection["width"])
            left = int(selection["x"])
            top = int(selection["y"])

            # fill focal point with selection values to crop the image
            instance.focal_point_width = width
            instance.focal_point_height = height
            instance.focal_point_x = left + width/2
            instance.focal_point_y = top + height/2

            if width > 5 and height > 5:
                # crop the image
                filter_spec = "fill-"+str(width)+"x"+str(height)+"-c100"
                rendition_file = instance.get_rendition(filter_spec).file
                print("model file:")
                print(rendition_file)
                print(type(rendition_file))

                # set url for the rest api
                selection["url"] = 'media/images/'+rendition_file.path.split("/")[-1]

                if int(selection_id) > 0:  # alter selection
                    print 'alter selection'
                    cropped = CroppedImage.objects.get(id=selection_id)
                    cropped.file = rendition_file
                    # set json in CustomImage for the rest api
                    instance.selections[selection_id] = selection
                else:  # create selection
                    print 'create section'
                    cropped = CroppedImage.objects.create(full_image=instance, file=rendition_file)
                    # set json in CustomImage for the rest api
                    instance.selections[cropped.id] = selection
                cropped.left = left
                cropped.top = top
                # add new tags
                for tag in selection['tags']:
                    cropped.tags.add(tag)
                cropped.save()

                print instance.selections

            # set old focal point
            instance.focal_point_width = old_focal_point_width
            instance.focal_point_height = old_focal_point_height
            instance.focal_point_x = old_focal_point_x
            instance.focal_point_y = old_focal_point_y

        for deletion in json_message['delete']:
            CroppedImage.objects.get(id=deletion).delete()
            # delete selection in json
            print instance.selections
            instance.selections.pop(str(deletion))

        instance.json = {'endrecursion': True}
        instance.save()


# Delete the source image file when an image is deleted
@receiver(pre_delete, sender=CustomImage)
def image_delete(sender, instance, **kwargs):
    instance.file.delete(False)
    for cropped_id in instance.selections.keys():
        CroppedImage.objects.get(id=cropped_id)


# Delete the rendition image file when a rendition is deleted
@receiver(pre_delete, sender=CustomRendition)
def rendition_delete(sender, instance, **kwargs):
    instance.file.delete(False)


# Delete the source image file when an image is deleted
@receiver(pre_delete, sender=CroppedImage)
def image_delete(sender, instance, **kwargs):
    instance.file.delete(False)


# Delete the rendition image file when a rendition is deleted
@receiver(pre_delete, sender=CroppedRendition)
def rendition_delete(sender, instance, **kwargs):
    instance.file.delete(False)


# Delete the source image file when an image is deleted
@receiver(pre_delete, sender=BlankedImage)
def image_delete(sender, instance, **kwargs):
    instance.file.delete(False)


# Delete the rendition image file when a rendition is deleted
@receiver(pre_delete, sender=BlankedRendition)
def rendition_delete(sender, instance, **kwargs):
    instance.file.delete(False)
