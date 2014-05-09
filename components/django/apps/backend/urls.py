from django.conf.urls import patterns, url, include

urlpatterns = patterns('backend.urls',
    url(r'^hooks/', include('backend.hooks.urls'))
)