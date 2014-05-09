from django.conf import settings
from django.contrib import admin
from django.conf.urls import patterns, url, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

admin.autodiscover()

urlpatterns = patterns('',
	url(r'^admin/', include(admin.site.urls)),
	url(r'^', include('camaste.urls',)),
	url(r'^backend/', include('backend.urls', namespace='backend')),
)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()

    # Serve user uploaded media
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
    )