
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict
from math import radians, sin, cos, sqrt, atan2

from .models import Event, PlayerActivity


# ==========================================
# CALCULATE GPS DISTANCE
# ==========================================

def calculate_distance(lat1, lon1, lat2, lon2):

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


# ==========================================
# LEARN PLAYER INTERESTS
# ==========================================

def get_player_sport_interests(user):

    sport_scores = defaultdict(int)

    if not user or not user.is_authenticated:
        return sport_scores

    # Consider activity from the last 90 days.
    cutoff_date = timezone.now() - timedelta(days=90)

    activities = PlayerActivity.objects.filter(
        user=user,
        created_at__gte=cutoff_date
    ).select_related("event")

    activity_weights = {
        "view": 1,
        "join_request": 3,
        "join_approved": 5,
    }

    for activity in activities:

        sport = activity.event.sport.lower()

        weight = activity_weights.get(
            activity.activity_type,
            0
        )

        sport_scores[sport] += weight

    return sport_scores


# ==========================================
# RECOMMEND EVENTS
# ==========================================

def recommend_events(
    user_sport,
    user_level,
    user_location,
    user_latitude=None,
    user_longitude=None,
    radius="10",
    favorite_sports=None,
    user=None
):

    # Only upcoming, active events.
    events = Event.objects.filter(
        date__gt=timezone.now(),
        is_cancelled=False
    ).order_by("date")

    recommendations = []

    # ======================================
    # SAVED FAVOURITE SPORTS
    # ======================================

    if favorite_sports:

        preferred_sports = [
            sport.lower()
            for sport in favorite_sports
        ]

    elif user_sport:

        preferred_sports = [
            user_sport.lower()
        ]

    else:

        preferred_sports = []

    # ======================================
    # LEARN FROM PLAYER ACTIVITY
    # ======================================

    sport_interests = get_player_sport_interests(user)

    # ======================================
    # TRAVEL RADIUS
    # ======================================

    if radius != "all":

        try:
            radius_km = float(radius)

            if radius_km <= 0:
                radius_km = 10

        except (TypeError, ValueError):
            radius_km = 10

    else:

        radius_km = None

    # ======================================
    # GPS AVAILABILITY
    # ======================================

    has_gps = (
        user_latitude is not None
        and user_longitude is not None
    )

    # ======================================
    # SCORE EACH EVENT
    # ======================================

    for event in events:

        if event.players_remaining <= 0:
            continue

        score = 0
        distance = None

        event_sport = event.sport.lower()

        # ----------------------------------
        # FAVOURITE SPORTS
        # ----------------------------------

        if event_sport in preferred_sports:
            score += 50

        # ----------------------------------
        # LEARNED SPORTS INTEREST
        # ----------------------------------

        interest_score = sport_interests.get(
            event_sport,
            0
        )

        # Activity bonus is capped at 25.
        activity_bonus = min(
            interest_score,
            25
        )

        score += activity_bonus

        # ----------------------------------
        # PREFERRED SKILL LEVEL
        # ----------------------------------

        if (
            user_level
            and event.level.lower() == user_level.lower()
        ):
            score += 30

        # ----------------------------------
        # LOCATION MATCH
        # ----------------------------------

        if (
            user_location
            and user_location.lower() in event.location.lower()
        ):
            score += 20

        # ----------------------------------
        # AVAILABLE PLAYER SPOTS
        # ----------------------------------

        score += 10

        # ----------------------------------
        # GPS DISTANCE
        # ----------------------------------

        if has_gps:

            if event.latitude is None or event.longitude is None:
                continue

            distance = calculate_distance(
                user_latitude,
                user_longitude,
                event.latitude,
                event.longitude
            )

            if (
                radius_km is not None
                and distance > radius_km
            ):
                continue

            score += max(
                0,
                10 - distance / 10
            )

      
        # ----------------------------------
        # EXPLAIN WHY THIS EVENT IS RECOMMENDED
        # ----------------------------------

        reasons = []

        if event_sport in preferred_sports:
            reasons.append(
                f"Matches your favourite sport: {event.sport}"
            )

        if interest_score > 0:
            reasons.append(
                f"You frequently explore {event.sport} events"
            )

        if (
            user_level
            and event.level.lower() == user_level.lower()
        ):
            reasons.append(
                f"Matches your skill level: {event.level}"
            )

        if (
            user_location
            and user_location.lower() in event.location.lower()
        ):
            reasons.append(
                "Matches your preferred location"
            )

        if distance is not None:
            reasons.append(
                f"Within your preferred distance ({distance:.1f} km away)"
            )

        if event.players_remaining > 0:
            reasons.append(
                f"{event.players_remaining} player spots available"
            )

        # ----------------------------------
        # SAVE RECOMMENDATION
        # ----------------------------------

        if score > 0:

            recommendations.append({

                "event": event,

                "score": round(score, 1),

                "distance": (
                    round(distance, 1)
                    if distance is not None
                    else None
                ),

                "activity_bonus": activity_bonus,

                "reasons": reasons,

            })


    # ======================================
    # SORT RECOMMENDATIONS
    # ======================================

    recommendations.sort(
        key=lambda item: (
            -item["score"],
            item["distance"]
            if item["distance"] is not None
            else float("inf")
        )
    )

    return recommendations
