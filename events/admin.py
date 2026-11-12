
from django.contrib import admin
from .models import (
    Event,
    JoinRequest,
    PlayerPreference,
    PlayerActivity,
    Notification,
    Message,
)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "sport",
        "organizer",
        "location",
        "date",
        "level",
    )


@admin.register(JoinRequest)
class JoinRequestAdmin(admin.ModelAdmin):
    list_display = (
        "player",
        "event",
        "status",
        "created_at",
    )


@admin.register(PlayerPreference)
class PlayerPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "preferred_level",
        "preferred_radius",
        "updated_at",
    )


@admin.register(PlayerActivity)
class PlayerActivityAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "event",
        "activity_type",
        "created_at",
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "recipient",
        "message",
        "event",
        "is_read",
        "created_at",
    )

    list_filter = ("is_read", "created_at")

    search_fields = (
        "recipient__username",
        "message",
        "event__title",
    )

    readonly_fields = ("created_at",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "sender",
        "recipient",
        "body",
        "is_read",
        "created_at",
    )

    list_filter = ("is_read", "created_at")

    search_fields = (
        "sender__username",
        "recipient__username",
        "body",
    )

    readonly_fields = ("created_at",)

from .models import EventReview

@admin.register(EventReview)
class EventReviewAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "player",
        "rating",
        "created_at",
    )

    list_filter = (
        "rating",
        "created_at",
    )

    search_fields = (
        "event__title",
        "player__username",
        "comment",
    )

    ordering = ("-created_at",)