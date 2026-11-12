
from django.db import models
from django.contrib.auth.models import User


class Event(models.Model):

    SPORT_CHOICES = [
        ("Football", "Football"),
        ("Cricket", "Cricket"),
        ("Basketball", "Basketball"),
        ("Badminton", "Badminton"),
    ]

    LEVEL_CHOICES = [
        ("Beginner", "Beginner"),
        ("Intermediate", "Intermediate"),
        ("Advanced", "Advanced"),
    ]

    organizer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="organized_events"
    )

    title = models.CharField(max_length=200)

    sport = models.CharField(
        max_length=50,
        choices=SPORT_CHOICES
    )

    location = models.CharField(max_length=200)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    date = models.DateTimeField()

    level = models.CharField(
        max_length=50,
        choices=LEVEL_CHOICES
    )

    players_needed = models.PositiveIntegerField(default=1)
    players_joined = models.PositiveIntegerField(default=0)

    is_cancelled = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def players_remaining(self):
        return max(0, self.players_needed - self.players_joined)

    def __str__(self):
        return self.title


class JoinRequest(models.Model):

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="join_requests"
    )

    player = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="join_requests"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.player.username} - {self.event.title} - {self.status}"


class PlayerPreference(models.Model):

    LEVEL_CHOICES = [
        ("Beginner", "Beginner"),
        ("Intermediate", "Intermediate"),
        ("Advanced", "Advanced"),
    ]

    RADIUS_CHOICES = [
        ("5", "5 km"),
        ("10", "10 km"),
        ("20", "20 km"),
        ("50", "50 km"),
        ("100", "100 km"),
        ("all", "Any Distance"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="player_preference"
    )

    favorite_sports = models.JSONField(default=list, blank=True)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    preferred_level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default="Beginner"
    )

    preferred_radius = models.CharField(
        max_length=10,
        choices=RADIUS_CHOICES,
        default="10"
    )

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences for {self.user.username}"


class PlayerActivity(models.Model):

    ACTIVITY_CHOICES = [
        ("view", "Viewed Event"),
        ("join_request", "Requested to Join"),
        ("join_approved", "Join Request Approved"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sports_activities"
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="player_activities"
    )

    activity_type = models.CharField(
        max_length=30,
        choices=ACTIVITY_CHOICES
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "activity_type"]),
            models.Index(fields=["user", "event"]),
        ]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.activity_type} - {self.event.title}"
        )


class Notification(models.Model):

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications"
    )

    message = models.CharField(max_length=255)

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
        ]

    def __str__(self):
        return f"{self.recipient.username} - {self.message}"


class PlayerProfile(models.Model):
    """
    Public profile information for each PlayNear player.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="player_profile"
    )

    bio = models.TextField(
        max_length=500,
        blank=True
    )

    city = models.CharField(
        max_length=100,
        blank=True
    )

    profile_photo = models.ImageField(
        upload_to="profile_photos/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Message(models.Model):

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_messages"
    )

    body = models.TextField(max_length=2000)

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["sender", "recipient"]),
            models.Index(fields=["recipient", "is_read"]),
        ]

    def __str__(self):
        return f"Message from {self.sender.username} to {self.recipient.username}"

class EventReview(models.Model):

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    player = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="event_reviews"
    )

    rating = models.PositiveSmallIntegerField(
        choices=[
            (1, "⭐ 1 Star"),
            (2, "⭐⭐ 2 Stars"),
            (3, "⭐⭐⭐ 3 Stars"),
            (4, "⭐⭐⭐⭐ 4 Stars"),
            (5, "⭐⭐⭐⭐⭐ 5 Stars"),
        ]
    )

    comment = models.TextField(
        max_length=500,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
                fields=["event", "player"],
                name="unique_player_event_review"
            )
        ]

    def __str__(self):
        return f"{self.player.username} - {self.event.title} ({self.rating}/5)"    