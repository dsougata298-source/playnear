
from math import radians, sin, cos, sqrt, atan2

from .models import PlayerPreference, Notification


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two GPS coordinates in kilometers.
    Uses the Haversine formula.
    """

    earth_radius = 6371

    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius * c


def notify_nearby_players(event):
    """
    Notify players when a new event matches their
    favorite sports and preferred distance.
    """

    # Event must have GPS coordinates.
    if event.latitude is None or event.longitude is None:
        return 0

    preferences = PlayerPreference.objects.select_related(
        "user"
    ).exclude(user=event.organizer)

    notification_count = 0

    for preference in preferences:

        # Check whether the player likes this sport.
        favorite_sports = preference.favorite_sports or []

        if event.sport not in favorite_sports:
            continue

        # Player must have saved GPS coordinates.
        if preference.latitude is None or preference.longitude is None:
            continue

        # Calculate distance between player and event.
        distance = calculate_distance(
            preference.latitude,
            preference.longitude,
            event.latitude,
            event.longitude,
        )

        # Check player's preferred radius.
        radius = preference.preferred_radius

        if radius != "all" and distance > float(radius):
            continue

        # Create an in-app notification.
        Notification.objects.create(
            recipient=preference.user,
            event=event,
            message=(
                f"New {event.sport} event nearby! "
                f"{event.title} is approximately "
                f"{distance:.1f} km away."
            ),
        )

        notification_count += 1

    return notification_count
