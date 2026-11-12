
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import Event, PlayerPreference, PlayerProfile, EventReview


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password1",
            "password2",
        ]


class EventForm(forms.ModelForm):

    latitude = forms.FloatField(
        required=False,
        widget=forms.HiddenInput()
    )

    longitude = forms.FloatField(
        required=False,
        widget=forms.HiddenInput()
    )

    date = forms.DateTimeField(
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={
                "type": "datetime-local",
                "class": "event-date-input",
                "required": "required",
                "style": "width:100%; min-width:0; display:block;",
            }
        )
    )

    class Meta:
        model = Event

        fields = [
            "title",
            "sport",
            "location",
            "latitude",
            "longitude",
            "date",
            "level",
            "players_needed",
        ]


class PlayerPreferenceForm(forms.ModelForm):

    favorite_sports = forms.MultipleChoiceField(
        choices=Event.SPORT_CHOICES,
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )

    class Meta:
        model = PlayerPreference

        fields = [
            "favorite_sports",
            "preferred_level",
            "preferred_radius",
            "latitude",
            "longitude",
        ]

        widgets = {
            "preferred_level": forms.Select(),

            "preferred_radius": forms.Select(),

            "latitude": forms.NumberInput(
                attrs={
                    "step": "any",
                    "placeholder": "Enter your latitude",
                }
            ),

            "longitude": forms.NumberInput(
                attrs={
                    "step": "any",
                    "placeholder": "Enter your longitude",
                }
            ),
        }

class PlayerProfileForm(forms.ModelForm):

    class Meta:
        model = PlayerProfile
        fields = ["profile_photo", "bio", "city"]

        widgets = {
            "profile_photo": forms.ClearableFileInput(attrs={
                "accept": "image/*",
                "class": "form-control"
            }),
            "bio": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Tell other players a little about yourself..."
            }),
            "city": forms.TextInput(attrs={
                "placeholder": "Enter your city"
            }),
        }

class EventReviewForm(forms.ModelForm):

    class Meta:
        model = EventReview

        fields = [
            "rating",
            "comment",
        ]

        widgets = {
            "rating": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Share your experience...",
                    "rows": 4,
                    "maxlength": 500,
                }
            ),
        }

        labels = {
            "rating": "Rate your experience",
            "comment": "Your review",
        }