__all__ = ('PerformerHomeView', 'PerformerSignupView', 'BroadcastView')

from django import forms
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, FormView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from camaste.models import Performer, Account


##############################################################################


class PerformerSignupForm(forms.Form):
    name = forms.CharField(max_length=30)

class PerformerSignupView(FormView):
    template_name = 'camaste/performer/signup.html'

    def get_form_class(self):
        return PerformerSignupForm 

    def is_already_performer(self, request):        
        return request.user.is_model or len(Performer.objects.filter(account=request.user)[:1]) > 0

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if self.is_already_performer(request):
            return HttpResponseRedirect(reverse('performer_home'))
        return super(PerformerSignupView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        performer = Performer()
        performer.account = self.request.user
        performer.name = form.cleaned_data.get("name")
        performer.approve()
        performer.save()
        return HttpResponseRedirect(reverse('performer_home'))


##############################################################################


class PerformerHomeView(TemplateView):
    template_name = "camaste/performer/home.html"


##############################################################################


class BroadcastView(TemplateView):
    template_name = "camaste/performer/broadcast.html"