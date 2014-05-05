from django.conf.urls import patterns, url
from camaste import frontend

urlpatterns = patterns('camaste.views',
    url(r'^$', frontend.HomePageView.as_view(), name='home'),
    url(r'^contact$', frontend.ContactView.as_view(), name='contact'),

    # General site authentication
    url(r'^register$', frontend.RegisterView.as_view(), name='register'),
    url(r'^login$', frontend.LoginView.as_view(), name='login'),
    url(r'^logout$', frontend.logout, name='logout'),
    url(r'^activate/(?P<username>[a-zA-Z0-9]{3,30})/(?P<token>[A-Z]{15})$', frontend.activate, name='activate'),

    # Account
    url(r'^account$', frontend.AccountView.as_view(), name='account'),

    # Performer
    url(r'^broadcast$', frontend.BroadcastView.as_view(), name='broadcast'),
    url(r'^model/home$', frontend.PerformerHomeView.as_view(), name='performer_home'),
    url(r'^model/signup$', frontend.PerformerSignupView.as_view(), name='performer_signup'),
)