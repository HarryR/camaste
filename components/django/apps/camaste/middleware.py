import re
from django.utils.html import strip_spaces_between_tags
from django.conf import settings
 
class XForwardedForMiddleware(object):
    def process_request(self, request):
        if request.META.has_key("HTTP_X_FORWARDED_FOR"):
            request.META["HTTP_X_PROXY_REMOTE_ADDR"] = request.META["REMOTE_ADDR"]
            parts = request.META["HTTP_X_FORWARDED_FOR"].split(",", 1)
            request.META["REMOTE_ADDR"] = parts[0]

RE_MULTISPACE = re.compile(r"\s{2,}")
RE_REMOVE = re.compile(r"(\n|<!--.+?-->)")
class MinifyHTMLMiddleware(object):
    """
    Strip comments, newlines and excess space from the output HTML.
    """
    def process_response(self, request, response):
        if 'text/html' in response['Content-Type'] and settings.COMPRESS_HTML:
            response.content = strip_spaces_between_tags(response.content.strip())
            response.content = RE_MULTISPACE.sub(" ", response.content)
            response.content = RE_REMOVE.sub("", response.content)
        return response