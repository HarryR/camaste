from django.conf import settings
from django.db.models import Q
from django.contrib.auth.models import check_password
from camaste.models import Account

class Backend(object):
    def authenticate(self, username=None, password=None):
        """
        Allows authentication via either username or e-mail address
        """
        user = Account.objects.filter(Q(username=username) | Q(email=username) )[0:1]
        if len(user) == 0:
            return None
        user = user[0]
        if user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return Account.objects.get(pk=user_id)
        except Account.DoesNotExist:
            return None