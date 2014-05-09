__all__ = ('Account', 'Performer', 'Room')

from django.conf import settings
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from redis_cache import get_redis_connection

from datetime import datetime, timedelta
from base64 import b64encode
from os import urandom
import re, json

from camaste.validators import *

def make_token(how_long):
    return re.sub(r'[^A-Za-z]', '', b64encode(urandom(how_long*2))).upper()[0:how_long]



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

    username = models.CharField(max_length=30, unique=True, blank=False, null=False, validators=[is_username])
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
            self.activate_token = make_token(15)
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
        self.reset_token = make_token(15)
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






##############################################################################





class Room (models.Model):
    """
    created = DateTime that room was created    
    is_archived = The room will never be used in future!
    is_online = Is somebody broadcasting in it?
    is_private = Is membership restricted to specific Accounts?
    allow_anons = Allow anonymous users?
    anons_see_chat = Allow anonymous users to see chat?    
    """
    token = models.CharField(max_length=15, blank=False, null=False, unique=True)
    performer = models.ForeignKey(Performer, related_name="rooms")    

    created = models.DateTimeField(null=False, blank=False, auto_now_add=True)

    is_archived = models.BooleanField(default=False)
    is_online = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)
    allow_anons = models.BooleanField(default=False)
    anons_see_chat = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.token is None:            
            self.token = make_token(15)
        super(Room, self).save(*args, **kwargs)

    def allow_access(self, account, access='G'):
        """
        Setup a room access token for the Realtime server to pickup
        """
        assert isinstance(account, Account)
        key = "RAXS.%s." % (self.token, make_token(20))
        con = get_redis_connection('default')
        pipe = con.pipeline()
        pipe.set(key, json.dumps({
                'room': self.token,
                'account': {                
                    'pk': account.pk,
                    'username': account.username,
                    'access': access
                }
            }))
        pipe.pexpire(key, 30 * 1000)
        pipe.execute()
        return key

@receiver(post_save, sender=Room)
def Room__post_save(sender, instance, created, **kwargs):
    room_key = "Room_%s" % (instance.token)

    con = get_redis_connection('default')
    pipe = con.pipeline()
    if room.is_archived:
        pipe.delete(room_key)
    else:
        room_data = {
            'is_online': instance.online,
            'is_private': instance.is_private,
            'allow_anons': instance.allow_anons,
            'anons_see_chat': instance.anons_see_chat
        }
        pipe.set(room_key, json.dumps(room_data))
    pipe.execute()

class RoomMember (models.Model):
    """
    is_banned - Is person banned from the room?
    access - Room Access Level
              * G = Ghost, not shown in user list
              * V = View Only, shown in user list
              * P = Participent, can see and interact with chat
              * P = Performer, can manage all performer aspects of room
              * A = Admin, badassmotherfucker
              * B = Banned
              * Anything else - no access 
    """
    token = models.CharField(max_length=15, blank=False, null=False, unique=True)
    account = models.ForeignKey(Account, related_name="room_memberships")
    room = models.ForeignKey(Room, related_name="members")    
    access = models.CharField(max_length=1, default="N")

    # Members can be banned from the room
    is_banned = models.BooleanField(default=False)
    ban_timestamp = models.DateTimeField(null=True, blank=True)
    ban_reason = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.token is None:            
            self.token = make_token(15)
        super(Room, self).save(*args, **kwargs)


@receiver(post_save, sender=RoomMember)
def RoomMember__post_save(sender, instance, created, **kwargs):
    """
    Synchronise RoomMember information with Redis
    """
    members_key = "Room_%s_Members" % (instance.room.token,)

    con = get_redis_connection('default')
    pipe = con.pipeline()
    if is_banned:
        # Remove membership
        pipe.hdel(members_key, instance.token)
    else:
        # Update membership
        member_data = {
            'token': instance.token,
            'account': {                
                'pk': instance.account.pk,
                'username': instance.account.username,
                'access': instance.access
            }
        }
        pipe.hset(members_key, instance.account.pk, json.dumps(member_data))
    pipe.execute()