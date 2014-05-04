__all__ = ('ContactView',)

from django.views.generic import TemplateView

class ContactView(TemplateView):
    template_name = "camaste/contact.html"