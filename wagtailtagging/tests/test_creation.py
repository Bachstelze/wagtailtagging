from collections import OrderedDict

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from wagtail.wagtailcore.models import Page

from home.models import HomePage, CustomImage, ImageSelector, CroppedImage
import os
from wagtailtagging.settings.base import MEDIA_ROOT, BASE_DIR
from rest_framework.test import APIClient

class CreationTestCase(TestCase):
    def setUp(self):
        self.images = [f for f in os.listdir(MEDIA_ROOT + '/original_images') ]
        self.image_files = []
        self.count = 0
        self.count += len([name for name in os.listdir('./media/images')])
        self.count += len([name for name in os.listdir('./media/original_images')])
        for page in Page.objects.all():
            if page.is_root():
                root = page
                break
        slug = "landingPage"
        path = "test/" + slug
        home_page = HomePage(path=path, depth=2, slug=slug, title="HomePage")
        root.add_child(instance=home_page)
        home_page.save()
        for i in range(4):
            self.create_page(i, home_page)
        for image in self.images[:10]:
            self.create_image(image)
        main_image = ImageSelector.objects.get(id=10).main_image
        print 'main image id'
        print main_image.id
        json_dic = {"create":
                        {"-1":{"tags":["Wasserfall"],"x":759,"y":425,"width":268,"height":537}},
                    "delete":[],
                    "alter":[]}
        main_image.json = json_dic
        main_image.save()

    def tearDown(self):
        print 'tearDown called'
        for image in self.image_files:
            file_name = image.file.name.split("/")[-1]
            #print MEDIA_ROOT+"/original_images/"+file_name
            if os.path.exists(MEDIA_ROOT+"/original_images/"+file_name):
                os.remove(os.path.join(MEDIA_ROOT+ '/original_images',file_name))
                #print 'deleted: '+MEDIA_ROOT+"/original_images/"+file_name
            if os.path.exists(MEDIA_ROOT+"/images/"+file_name):
                os.remove(os.path.join(MEDIA_ROOT+ '/images',file_name))
                #print 'deleted: '+MEDIA_ROOT+"/images/"+file_name

            image_object = CustomImage.objects.get(file="original_images/"+file_name)
            os.remove(os.path.join(BASE_DIR,str(image_object.thumb_url)))
            #print 'deleted: '+str(image_object.thumb_url)
            os.remove(os.path.join(BASE_DIR,str(image_object.resize_url)))
            #print 'deleted: '+str(image_object.resize_url)
            image_object.delete()

        count_after = len([name for name in os.listdir('./media/images')])
        count_after += len([name for name in os.listdir('./media/original_images')])

        self.assertEqual(self.count, count_after)
        print 'size of files: ', count_after

    def create_page(self, index, parent):
        slug = "test-"+str(index)
        path = "test/" + slug
        detail_page = ImageSelector(path=path, depth=3, slug=slug, title="page")
        parent.add_child(instance=detail_page)
        detail_page.save()
        return detail_page

    def create_image(self, file_name):
        image_path = MEDIA_ROOT + "/original_images/" + file_name
        image_file =  SimpleUploadedFile(
            name=file_name,
            content=open(image_path, 'rb').read(),
            content_type='image/jpeg')
        firstImage = CustomImage.objects.create(file=image_file, title='firstImage.jpg')
        firstImage.save()

        self.image_files.append(firstImage.file)

    def test_default(self):
        #test page attributes
        test_page = ImageSelector.objects.get(id=10)
        main_image = test_page.main_image
        self.assertIsNotNone(test_page.main_image)
        self.assertIsNotNone(test_page.date)
        self.assertFalse(test_page.specific.front)
        self.assertIsNone(test_page.specific.get_prev_front_sibling())
        self.assertIsNone(test_page.specific.get_next_front_sibling())
        self.assertTrue(len(test_page.specific.get_next_cutted_siblings()) > 0)
        self.assertTrue(len(test_page.specific.get_prev_cutted_siblings()) > 0)
        self.assertEqual(len(test_page.specific.get_next_cutted_front_siblings()),0)
        self.assertEqual(len(test_page.specific.get_prev_cutted_front_siblings()),0)

        #test image existens
        new_images = [name for name in os.listdir(MEDIA_ROOT + '/original_images') ]
        self.assertIn(test_page.main_image.file.name.split("/")[1], new_images)

        #test cropped image
        test_selections = test_page.main_image.selections
        self.assertGreater(test_selections.keys(),0)
        cropped = CroppedImage.objects.get(id=test_selections.keys()[0])
        self.assertIsNotNone(cropped)

        #test rest api
        client = APIClient()
        response = client.get('/api/v1/images/3/')
        compare_json = {
            u'resize_url': main_image.resize_url,
            u'thumb_url': main_image.thumb_url,
            u'tags': [], u'title': u'firstImage.jpg',
            u'height': main_image.height,
            u'width': main_image.width,
            u'meta':
                OrderedDict([(u'type', u'home.CustomImage'),
                (u'detail_url', u'http://localhost/api/v1/images/3/')]),
            u'selections':
                {u'1': {
                    u'tags': [u'Wasserfall'],
                    u'url': 'media/'+cropped.file.name,
                    u'height': 537, u'width': 268, u'y': 425, u'x': 759}},
            u'filename': main_image.file.name.split("/")[1], u'id': 3}
        self.compare_dicts(compare_json, response.data)

    def compare_dicts(self, a, b):
        for key in a.keys():
            self.assertTrue(b.has_key(key))
            if type(a[key]) is type({}):
                self.assertTrue(type(b[key]) is type({}))
                self.compare_dicts(a[key], b[key])
            else:
                self.assertEqual(a[key], b[key])