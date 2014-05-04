__all__ = ('Account', 'Performer')

from django.conf import settings
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.db.models.signals import post_save
from django.dispatch import receiver

from datetime import datetime, timedelta
from base64 import b64encode
from os import urandom
import re

from camaste.validators import *


##############################################################################


class AccountManager(BaseUserManager):
    def create_user(self, username, email, full_name, password):
        user = Account()
        user.username = username
        user.email = email
        user.full_name = full_name
        user.is_admin = False        
        user.set_password(password)
        user.activate()
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, full_name, password):
        user = Account()
        user.username = username
        user.email = email
        user.full_name = full_name
        user.is_admin = True        
        user.set_password(password)
        user.activate()
        user.save(using=self._db)
        user.activate()
        user.save(using=self._db)
        return user

class Account (AbstractBaseUser):
    objects = AccountManager()
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ('email', 'full_name')

    username = models.CharField(max_length=30, unique=True, db_index=True, blank=False, null=False, validators=[is_username])
    email = models.EmailField(max_length=254, unique=True, blank=False, null=False)
    full_name = models.CharField(max_length=100, blank=False, null=False)
    is_active = models.BooleanField(default=False)
    is_model = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)    

    #
    # Activation and Password Reset
    #
    # We restrict the user to sending a password reset request to every 15 minutes
    # And the user must be activated before they can login or do a password reset
    # Password resets
    activate_token = models.CharField(max_length=15, blank=False, null=True)
    reset_token = models.CharField(max_length=15, blank=False, null=True)
    reset_until = models.DateTimeField(null=True)
    last_reset = models.DateTimeField(null=True)

    ####

    def __unicode__(self):
        return self.username

    def save(self, *args, **kwargs):
        if not self.pk:
            """
            When the account is first created setup the 'activation token' stuff
            """
            self.is_active = False
            self.activate_token = re.sub(r'[^A-Za-z]', '', b64encode(urandom(50))).upper()[0:15]
        super(Account, self).save(*args, **kwargs)

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    def activate(self):
        self.activate_token = None
        self.is_active = True

    ####

    def reset(self):
        if not self.can_reset():
            return None
        self.reset_token = re.sub(r'[^A-Za-z]', '', b64encode(urandom(50))).upper()[0:15]
        self.last_reset = datetime.now()
        self.reset_until = datetime.now() + timedelta(days=2)      

    def can_request_reset(self):
        reset_expiry = datetime.now() - timedelta(minutes=15)        
        return self.is_active == True and (self.last_reset is None or self.last_reset < reset_expiry)

    def can_reset(self, token):
        return self.reset_until is not None \
           and self.reset_token is not None \
           and self.reset_until > datetime.now() \
           and token == self.reset_token

    @property
    def is_staff(self):
        return self.is_admin


##############################################################################


class PerformerManager (models.Manager):
    def declined(self):
        return self.get_queryset().filter(is_declined=True)
    def approved(self):
        return self.get_queryset().filter(is_approved=True)
    def online(self):
        return self.get_queryset().filter(is_online=True, is_approved=True)
    def public(self):
        return self.get_queryset().filter(is_private=False, is_online=True, is_approved=True)


class Performer (models.Model):
    objects = PerformerManager()

    account = models.ForeignKey(Account)
    name = models.CharField(max_length=30, blank=False, null=False)

    ###
    # Current status / availability
    is_online = models.BooleanField(default=False, db_index=True)
    in_private = models.BooleanField(default=False, db_index=True)
    last_online = models.DateTimeField(default=None, blank=True, null=True)

    ###
    # Approve & Decline
    is_approved = models.BooleanField(default=False)
    is_declined = models.BooleanField(default=False)
    decline_reason = models.CharField(max_length=100, default=None, blank=True, null=True)
    decline_date = models.DateTimeField(null=True, default=None, blank=True)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.account.username)

    def online_ping(self):
        self.is_online = True
        self.last_online = datetime.now()

    def approve(self):
        self.is_declined = False
        self.is_approved = True
        self.decline_date = None    

    def decline(self, reason):
        self.is_approved = False
        self.is_declined = True
        self.decline_reason = reason
        self.decline_date = datetime.now()


@receiver(post_save, sender=Performer)
def Performer__post_save(sender, instance, created, **kwargs):
    """
    When a performer is created ensure that their account is marked as 'is_model'
    """
    if created:
        Account.objects.filter(pk=instance.account.pk).update(is_model=True)        