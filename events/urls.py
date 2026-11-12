
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),

    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("create-event/", views.create_event, name="create_event"),

    path(
        "event/<int:event_id>/edit/",
        views.edit_event,
        name="edit_event"
    ),

    path(
        "event/<int:event_id>/cancel/",
        views.cancel_event,
        name="cancel_event"
    ),

    path(
        "event/<int:event_id>/",
        views.event_detail,
        name="event_detail"
    ),

    path(
    "event/<int:event_id>/review/",
    views.review_event,
    name="review_event"
    ),

    path(
        "event/<int:event_id>/join/",
        views.join_event,
        name="join_event"
    ),

    path(
        "organizer-dashboard/",
        views.organizer_dashboard,
        name="organizer_dashboard"
    ),

    path(
        "update-request/<int:request_id>/",
        views.update_join_request,
        name="update_join_request"
    ),

    path("my-events/", views.my_events, name="my_events"),

    path(
        "recommended-events/",
        views.recommended_events,
        name="recommended_events"
    ),

    path(
        "my-preferences/",
        views.my_preferences,
        name="my_preferences"
    ),

    path(
        "notifications/",
        views.notifications,
        name="notifications"
    ),

        path(
        "notifications/mark-all-read/",
        views.mark_all_notifications_read,
        name="mark_all_notifications_read"
    ),

    path(
        "notifications/<int:notification_id>/read/",
        views.mark_notification_read,
        name="mark_notification_read"
    ),

    path(
    "notifications/<int:notification_id>/delete/",
    views.delete_notification,
    name="delete_notification"
    ),

    path(
        "notifications/count/",
        views.unread_notification_count,
        name="unread_notification_count"
    ),

    path(
        "activity-dashboard/",
        views.activity_dashboard,
        name="activity_dashboard"
    ),
    path("my-profile/", views.my_profile, name="my_profile"),

    path("players/", views.players_directory, name="players_directory"),

    path("player/<str:username>/", views.public_player_profile, name="public_player_profile"),

    path(
        "messages/",
        views.messages_inbox,
        name="messages_inbox"
    ),


    path(
        "messages/count/",
        views.unread_message_count,
        name="unread_message_count"
    ),

    
    path(
        "messages/<str:username>/",
        views.message_conversation,
        name="message_conversation"
    ),
]