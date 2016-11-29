from django.conf.urls import include, url
from django.conf import settings
from django.contrib import admin

from wagtail.wagtailadmin import urls as wagtailadmin_urls
from wagtail.wagtaildocs import urls as wagtaildocs_urls
from wagtail.wagtailcore import urls as wagtail_urls
from wagtail.wagtailimages import urls as wagtailimages_urls

from search import views as search_views

from django.contrib.auth.models import User
from rest_framework import routers, serializers, viewsets, filters
from wagtailtagging import views

from wagtail.contrib.wagtailapi import urls as wagtailapi_urls

from wagtailtagging.views import edit, clipping, model_json, create_clipping

# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'is_staff')


# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = (filters.DjangoFilterBackend,)

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'groups', views.GroupViewSet)

urlpatterns = [
    url(r'^django-admin/', include(admin.site.urls)),

    url(r'^admin/clipping/(\d+)/$', clipping, name='clipping'),
    url(r'^admin/images/(\d+)/$', edit, name='edit'),
    url(r'^admin/', include(wagtailadmin_urls)),
    url(r'^documents/', include(wagtaildocs_urls)),

    url(r'^search/$', search_views.search, name='search'),

    url(r'^api/', include(wagtailapi_urls)),

    url(r'^images/', include(wagtailimages_urls)),

    url(r'^json/(\w+)/(\d+)/$', model_json, name='json'),

    url(r'^get_foreground/$', create_clipping, name='clipping'),

    url(r'^', include(wagtail_urls))

    #url(r'^', include(router.urls)), #own restframework, was replaced by the wagtail api
    #url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]


if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from django.views.generic import TemplateView

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
