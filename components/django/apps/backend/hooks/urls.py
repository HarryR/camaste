from django.conf.urls import patterns, url, include
from .nxrtmp import urlpatterns as nxrtmp_urlpatterns

urlpatterns = patterns('backend.hooks',
	url(r'^nxrtmp/', include(nxrtmp_urlpatterns)),
	# TODO: RTMPd or SLS patterns?
)