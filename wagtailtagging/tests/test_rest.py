from django.core.files.uploadedfile import SimpleUploadedFile
from wagtail.wagtailcore.models import Page

from home.models import HomePage, CustomImage, ImageSelector
import os
from wagtailtagging.settings.base import MEDIA_ROOT, BASE_DIR
from rest_framework.test import APITestCase
from rest_framework.test import APIRequestFactory

class ApiTests(APITestCase):
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

    # def test_image_rest(self):
    #     factory = APIRequestFactory()
    #     request = factory.get('/api/v1/images/1/')