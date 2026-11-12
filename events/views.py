
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.db.models import Q, Avg, Count
from django.contrib.auth.models import User

from .forms import (
    RegisterForm,
    EventForm,
    PlayerPreferenceForm,
    PlayerProfileForm,
    EventReviewForm,
)

from .models import (
    Event,
    JoinRequest,
    PlayerPreference,
    PlayerActivity,
    Notification,
    PlayerProfile,
    Message,
    EventReview,
)

from .nearby_notifications import notify_nearby_players
from .recommendations import recommend_events


# ==========================================
# HOME PAGE
# ==========================================

def home(request):
    events = Event.objects.filter(
        date__gt=timezone.now(),
        is_cancelled=False
    ).annotate(
        average_rating=Avg("reviews__rating"),
        review_count=Count("reviews")
    ).order_by("date")

    events = [
        event for event in events
        if event.players_remaining > 0
    ]

    return render(
        request,
        "events/home.html",
        {
            "events": events,
        }
    )


# ==========================================
# USER REGISTRATION
# ==========================================

def register_view(request):

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)

            messages.success(
                request,
                "Your account has been created successfully!"
            )

            return redirect("home")

    else:
        form = RegisterForm()

    return render(
        request,
        "events/register.html",
        {
            "form": form,
        }
    )


# ==========================================
# USER LOGIN
# ==========================================

def login_view(request):

    if request.method == "POST":
        form = AuthenticationForm(
            request,
            data=request.POST
        )

        if form.is_valid():
            user = form.get_user()
            login(request, user)

            messages.success(
                request,
                "You have logged in successfully!"
            )

            next_url = request.POST.get("next")

            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)

            return redirect("home")

    else:
        form = AuthenticationForm()

    return render(
        request,
        "events/login.html",
        {
            "form": form,
        }
    )


# ==========================================
# USER LOGOUT
# ==========================================

@login_required
def logout_view(request):

    logout(request)

    messages.success(
        request,
        "You have been logged out successfully."
    )

    return redirect("home")


# ==========================================
# CREATE SPORTS EVENT
# ==========================================

@login_required
def create_event(request):

    if request.method == "POST":
        form = EventForm(request.POST)

        if form.is_valid():

            event = form.save(commit=False)
            event.organizer = request.user
            event.save()

            # Notify nearby players.
            notify_nearby_players(event)

            messages.success(
                request,
                "Your sports event has been created successfully!"
            )

            return redirect("my_events")

    else:
        form = EventForm()

    return render(
        request,
        "events/create_event.html",
        {
            "form": form,
        }
    )


# ==========================================
# EVENT DETAILS
# ==========================================

@login_required
def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    event_expired = event.date <= timezone.now()

    if request.user.is_authenticated:
        PlayerActivity.objects.create(
            user=request.user,
            event=event,
            activity_type="view"
        )

    user_request = JoinRequest.objects.filter(
        event=event,
        player=request.user
    ).first()

    # Get all reviews for this event
    reviews = EventReview.objects.filter(
        event=event
    ).select_related("player")

    # Calculate average rating
    average_rating = reviews.aggregate(
        average=Avg("rating")
    )["average"]

    review_count = reviews.count()

    context = {
        "event": event,
        "user_request": user_request,
        "event_expired": event_expired,
        "reviews": reviews,
        "average_rating": average_rating,
        "review_count": review_count,
    }

    return render(
        request,
        "events/event_detail.html",
        context
    )


# ==========================================
# REQUEST TO JOIN AN EVENT
# ==========================================

@login_required
@require_POST
def join_event(request, event_id):

    event = get_object_or_404(
        Event,
        id=event_id
    )

    if event.is_cancelled:
        messages.error(
            request,
            "This event has been cancelled."
        )
        return redirect("event_detail", event_id=event.id)

    if event.date <= timezone.now():
        messages.error(
            request,
            "This event has already started."
        )
        return redirect("event_detail", event_id=event.id)

    if event.organizer == request.user:
        messages.error(
            request,
            "You cannot join your own event."
        )
        return redirect("event_detail", event_id=event.id)

    if event.players_remaining <= 0:
        messages.error(
            request,
            "Sorry, this event is already full."
        )
        return redirect("event_detail", event_id=event.id)

    existing_request = JoinRequest.objects.filter(
        event=event,
        player=request.user
    ).first()

    if existing_request:

        if existing_request.status == "Pending":
            messages.warning(
                request,
                "You have already requested to join this event."
            )

        elif existing_request.status == "Approved":
            messages.info(
                request,
                "Your request to join this event has already been approved."
            )

        else:
            messages.warning(
                request,
                "You have already submitted a request for this event."
            )

        return redirect("event_detail", event_id=event.id)

    join_request = JoinRequest.objects.create(
        event=event,
        player=request.user,
        status="Pending"
    )

    # Record player activity.
    PlayerActivity.objects.create(
        user=request.user,
        event=event,
        activity_type="join_request"
    )

    # Notify the event organizer.
    Notification.objects.create(
        recipient=event.organizer,
        event=event,
        message=f"{request.user.username} requested to join your event: {event.title}."
    )

    messages.success(
        request,
        "Your join request has been sent to the organizer!"
    )

    return redirect("event_detail", event_id=event.id)


# ==========================================
# ORGANIZER DASHBOARD
# ==========================================

@login_required
def organizer_dashboard(request):

    join_requests = JoinRequest.objects.filter(
        event__organizer=request.user
    ).select_related(
        "event",
        "player"
    ).order_by("-created_at")

    total_events = Event.objects.filter(
        organizer=request.user
    ).count()

    total_requests = join_requests.count()

    pending_requests = join_requests.filter(
        status="Pending"
    ).count()

    approved_requests = join_requests.filter(
        status="Approved"
    ).count()

    rejected_requests = join_requests.filter(
        status="Rejected"
    ).count()

    context = {
        "join_requests": join_requests,
        "total_events": total_events,
        "total_requests": total_requests,
        "pending_requests": pending_requests,
        "approved_requests": approved_requests,
        "rejected_requests": rejected_requests,
    }

    return render(
        request,
        "events/organizer_dashboard.html",
        context
    )


# ==========================================
# APPROVE OR REJECT JOIN REQUEST
# ==========================================

@login_required
@require_POST
def update_join_request(request, request_id):

    join_request = get_object_or_404(
        JoinRequest,
        id=request_id,
        event__organizer=request.user
    )

    event = join_request.event

    if event.is_cancelled:
        messages.error(
            request,
            "This event has been cancelled. You cannot update its join requests."
        )
        return redirect("organizer_dashboard")

    if event.date <= timezone.now():
        messages.error(
            request,
            "This event has already started. You cannot update its join requests."
        )
        return redirect("organizer_dashboard")

    if join_request.status != "Pending":
        messages.warning(
            request,
            "This join request has already been processed."
        )
        return redirect("organizer_dashboard")

    action = request.POST.get("action")

    if action == "approve":

        if event.players_remaining <= 0:
            messages.error(
                request,
                "This event is already full."
            )
            return redirect("organizer_dashboard")

        join_request.status = "Approved"
        join_request.save(update_fields=["status"])

        event.players_joined += 1
        event.save(update_fields=["players_joined"])

        # Record approved activity.
        PlayerActivity.objects.create(
            user=join_request.player,
            event=event,
            activity_type="join_approved"
        )

        # Notify the player.
        Notification.objects.create(
            recipient=join_request.player,
            event=event,
            message=f"Your request to join '{event.title}' has been approved!"
        )

        messages.success(
            request,
            f"{join_request.player.username}'s request has been approved."
        )

    elif action == "reject":

        join_request.status = "Rejected"
        join_request.save(update_fields=["status"])

        # Notify the player.
        Notification.objects.create(
            recipient=join_request.player,
            event=event,
            message=f"Your request to join '{event.title}' has been rejected."
        )

        messages.success(
            request,
            f"{join_request.player.username}'s request has been rejected."
        )

    else:
        messages.error(
            request,
            "Invalid action."
        )

    return redirect("organizer_dashboard")


# ==========================================
# MY EVENTS
# ==========================================

@login_required
def my_events(request):

    created_events = Event.objects.filter(
        organizer=request.user
    ).order_by("-created_at")

    my_join_requests = JoinRequest.objects.filter(
        player=request.user
    ).select_related(
        "event",
        "event__organizer"
    ).order_by("-created_at")

    context = {
        "created_events": created_events,
        "my_join_requests": my_join_requests,
        "now": timezone.now(),
    }

    return render(
        request,
        "events/my_events.html",
        context
    )


# ==========================================
# RECOMMENDED EVENTS
# ==========================================

@login_required
def recommended_events(request):

    preference, created = PlayerPreference.objects.get_or_create(
        user=request.user
    )

    favorite_sports = preference.favorite_sports or []

    user_sport = request.GET.get(
        "sport",
        favorite_sports[0] if favorite_sports else ""
    )

    user_level = request.GET.get(
        "level",
        preference.preferred_level
    )

    user_location = request.GET.get(
        "location",
        ""
    )

    radius = request.GET.get(
        "radius",
        preference.preferred_radius
    )

    valid_radii = ["5", "10", "20", "50", "100", "all"]

    if radius not in valid_radii:
        radius = preference.preferred_radius

    latitude = request.GET.get("latitude")
    longitude = request.GET.get("longitude")

    user_latitude = None
    user_longitude = None

    try:
        if latitude and longitude:

            user_latitude = float(latitude)
            user_longitude = float(longitude)

            if not (-90 <= user_latitude <= 90):
                user_latitude = None
                user_longitude = None

            if not (-180 <= user_longitude <= 180):
                user_latitude = None
                user_longitude = None

        else:
            user_latitude = preference.latitude
            user_longitude = preference.longitude

    except (TypeError, ValueError):
        user_latitude = None
        user_longitude = None

    recommendations = recommend_events(
        user_sport=user_sport,
        user_level=user_level,
        user_location=user_location,
        user_latitude=user_latitude,
        user_longitude=user_longitude,
        radius=radius,
        favorite_sports=favorite_sports,
        user=request.user,
    )

    context = {
        "recommendations": recommendations,
        "user_sport": user_sport,
        "user_level": user_level,
        "user_location": user_location,
        "user_latitude": user_latitude,
        "user_longitude": user_longitude,
        "radius": radius,
        "favorite_sports": favorite_sports,
    }

    return render(
        request,
        "events/recommended_events.html",
        context
    )


# ==========================================
# PLAYER PREFERENCES
# ==========================================

@login_required
def my_preferences(request):

    preference, created = PlayerPreference.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        form = PlayerPreferenceForm(
            request.POST,
            instance=preference
        )

        if form.is_valid():

            saved_preference = form.save(commit=False)
            saved_preference.user = request.user
            saved_preference.save()

            messages.success(
                request,
                "Your preferences have been saved successfully!"
            )

            return redirect("my_preferences")

    else:
        form = PlayerPreferenceForm(
            instance=preference
        )

    return render(
        request,
        "events/my_preferences.html",
        {
            "form": form,
        }
    )


# ==========================================
# NOTIFICATIONS PAGE
# ==========================================

@login_required
def notifications(request):
    all_notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related("event").order_by("-id")

    unread_count = all_notifications.filter(
        is_read=False
    ).count()

    notification_filter = request.GET.get("filter", "all")

    if notification_filter == "unread":
        user_notifications = all_notifications.filter(
            is_read=False
        )
    elif notification_filter == "read":
        user_notifications = all_notifications.filter(
            is_read=True
        )
    else:
        notification_filter = "all"
        user_notifications = all_notifications

    context = {
        "notifications": user_notifications,
        "unread_count": unread_count,
        "notification_filter": notification_filter,
    }

    return render(
        request,
        "events/notifications.html",
        context
    )

# ==========================================
# MARK NOTIFICATION AS READ
# ==========================================


@login_required
@require_POST
def mark_notification_read(request, notification_id):

    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )

    notification.is_read = True
    notification.save(update_fields=["is_read"])

    # Open the related event when one exists.
    if notification.event:
        return redirect(
            "event_detail",
            event_id=notification.event.id
        )

    return redirect("notifications")

@login_required
@require_POST
def delete_notification(request, notification_id):
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )

    notification.delete()

    messages.success(
        request,
        "Notification deleted successfully."
    )

    return redirect("notifications")


@login_required
@require_POST
def mark_all_notifications_read(request):

    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)

    messages.success(
        request,
        "All notifications have been marked as read!"
    )

    return redirect("notifications")




# ==========================================
# UNREAD NOTIFICATION COUNT
# ==========================================

@login_required
def unread_notification_count(request):
    count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()

    return JsonResponse({
        "unread_count": count
    })

# ==========================================
# EDIT EVENT
# ==========================================

@login_required
def edit_event(request, event_id):

    event = get_object_or_404(
        Event,
        id=event_id,
        organizer=request.user
    )

    # Prevent editing cancelled events.
    if event.is_cancelled:
        messages.error(
            request,
            "You cannot edit a cancelled event."
        )
        return redirect("my_events")

    # Prevent editing past or started events.
    if event.date <= timezone.now():
        messages.error(
            request,
            "You cannot edit an event that has already started."
        )
        return redirect("my_events")

    if request.method == "POST":

        form = EventForm(
            request.POST,
            instance=event
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Your event has been updated successfully!"
            )

            return redirect("my_events")

    else:

        form = EventForm(
            instance=event
        )

    return render(
        request,
        "events/edit_event.html",
        {
            "form": form,
            "event": event,
        }
    )


# ==========================================
# CANCEL EVENT
# ==========================================

@login_required
@require_POST
def cancel_event(request, event_id):

    event = get_object_or_404(
        Event,
        id=event_id,
        organizer=request.user
    )

    if event.is_cancelled:

        messages.warning(
            request,
            "This event has already been cancelled."
        )

        return redirect("my_events")

    if event.date <= timezone.now():

        messages.error(
            request,
            "You cannot cancel an event that has already started."
        )

        return redirect("my_events")

    # Soft cancellation: keep the event in the database.
    event.is_cancelled = True

    event.save(
        update_fields=["is_cancelled"]
    )

    # Notify approved participants.
    approved_requests = JoinRequest.objects.filter(
        event=event,
        status="Approved"
    ).select_related("player")

    for join_request in approved_requests:

        Notification.objects.create(
            recipient=join_request.player,
            event=event,
            message=f"The event '{event.title}' has been cancelled by the organizer."
        )

    messages.success(
        request,
        "Your event has been cancelled. Approved participants have been notified."
    )

    return redirect("my_events")


@login_required
def activity_dashboard(request):

    activities = PlayerActivity.objects.filter(
        user=request.user
    ).select_related(
        "event"
    ).order_by("-created_at")

    total_views = activities.filter(
        activity_type="view"
    ).count()

    total_requests = activities.filter(
        activity_type="join_request"
    ).count()

    total_approved = activities.filter(
        activity_type="join_approved"
    ).count()

    # Calculate activity for each sport.
    sport_summary = {}

    for activity in activities:

        sport = activity.event.sport

        if sport not in sport_summary:
            sport_summary[sport] = {
                "views": 0,
                "requests": 0,
                "approved": 0,
                "total": 0,
            }

        sport_summary[sport]["total"] += 1

        if activity.activity_type == "view":
            sport_summary[sport]["views"] += 1

        elif activity.activity_type == "join_request":
            sport_summary[sport]["requests"] += 1

        elif activity.activity_type == "join_approved":
            sport_summary[sport]["approved"] += 1

    context = {
        "total_views": total_views,
        "total_requests": total_requests,
        "total_approved": total_approved,
        "sport_summary": sport_summary.items(),
        "recent_activities": activities[:20],
    }

    return render(
        request,
        "events/activity_dashboard.html",
        context
    )

@login_required
def my_profile(request):

    profile, created = PlayerProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":
        form = PlayerProfileForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Your profile has been updated successfully!"
            )
            return redirect("my_profile")

    else:
        form = PlayerProfileForm(instance=profile)

    context = {
        "profile": profile,
        "form": form,
    }

    return render(
        request,
        "events/my_profile.html",
        context
    )


@login_required
def players_directory(request):

    players = PlayerProfile.objects.select_related(
        "user"
    ).order_by("user__username")

    return render(
        request,
        "events/players_directory.html",
        {
            "players": players,
        }
    )



@login_required
def public_player_profile(request, username):

    profile = get_object_or_404(
        PlayerProfile.objects.select_related("user"),
        user__username=username
    )

    preference = PlayerPreference.objects.filter(
        user=profile.user
    ).first()

    return render(
        request,
        "events/public_player_profile.html",
        {
            "profile": profile,
            "preference": preference,
        }
    )


# ==========================================
# PRIVATE MESSAGING INBOX
# ==========================================

@login_required
def messages_inbox(request):

    conversations = User.objects.filter(
        Q(sent_messages__recipient=request.user) |
        Q(received_messages__sender=request.user)
    ).distinct().order_by("username")

    return render(
        request,
        "events/messages_inbox.html",
        {
            "conversations": conversations,
        }
    )


# ==========================================
# PRIVATE CONVERSATION
# ==========================================

@login_required
def message_conversation(request, username):

    other_user = get_object_or_404(
        User,
        username=username
    )

    if other_user == request.user:
        messages.error(request, "You cannot message yourself.")
        return redirect("messages_inbox")

    if request.method == "POST":

        body = request.POST.get("body", "").strip()

        if body and len(body) <= 2000:

            Message.objects.create(
                sender=request.user,
                recipient=other_user,
                body=body
            )

            return redirect(
                "message_conversation",
                username=other_user.username
            )

        messages.error(
            request,
            "Please enter a message of up to 2000 characters."
        )

    conversation = Message.objects.filter(
        Q(sender=request.user, recipient=other_user) |
        Q(sender=other_user, recipient=request.user)
    ).select_related(
        "sender",
        "recipient"
    ).order_by("created_at")

    Message.objects.filter(
        sender=other_user,
        recipient=request.user,
        is_read=False
    ).update(is_read=True)

    return render(
        request,
        "events/message_conversation.html",
        {
            "other_user": other_user,
            "conversation": conversation,
        }
    )

@login_required
def unread_message_count(request):
    unread_count = Message.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()

    return JsonResponse({
        "unread_count": unread_count
    })

@login_required
def review_event(request, event_id):

    event = get_object_or_404(
        Event,
        id=event_id
    )

    # Organizers cannot review their own events
    if event.organizer == request.user:
        messages.error(
            request,
            "You cannot review your own event."
        )
        return redirect("event_detail", event_id=event.id)

    # Only approved players can review
    approved_player = JoinRequest.objects.filter(
        event=event,
        player=request.user,
        status="Approved"
    ).exists()

    if not approved_player:
        messages.error(
            request,
            "Only approved participants can review this event."
        )
        return redirect("event_detail", event_id=event.id)

    # Reviews are allowed only after the event date and time
    if event.date > timezone.now():
        messages.error(
            request,
            "You can review this event after it has finished."
        )
        return redirect("event_detail", event_id=event.id)

    # Find an existing review, if any
    existing_review = EventReview.objects.filter(
        event=event,
        player=request.user
    ).first()

    if request.method == "POST":

        form = EventReviewForm(
            request.POST,
            instance=existing_review
        )

        if form.is_valid():

            review = form.save(commit=False)
            review.event = event
            review.player = request.user
            review.save()

            messages.success(
                request,
                "Your event review has been saved!"
            )

            return redirect("event_detail", event_id=event.id)

    else:

        form = EventReviewForm(
            instance=existing_review
        )

    return render(
        request,
        "events/review_event.html",
        {
            "event": event,
            "form": form,
            "existing_review": existing_review,
        }
    )