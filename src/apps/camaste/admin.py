from django.contrib import admin
from camaste.models import Performer, Account

def performer_approve(modeladmin, request, queryset):
	for o in queryset:
		o.approve()
		o.save()
performer_approve.short_description = "Approve the performers account"

def performer_decline(modeladmin, request, queryset):
	for o in queryset:
		o.decline("Declined by Administrator")
		o.save()
performer_approve.short_description = "Decline the performers account"

class PerformerAdmin(admin.ModelAdmin):
     actions = [performer_approve, performer_decline]

admin.site.register(Performer, PerformerAdmin)