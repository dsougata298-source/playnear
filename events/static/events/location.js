
document.addEventListener("DOMContentLoaded", function () {
    const locationButton = document.getElementById("findNearbyButton");
    const locationStatus = document.getElementById("locationStatus");
    const recommendationForm = document.getElementById("recommendationForm");

    const latitudeInput = document.getElementById("playerLatitude");
    const longitudeInput = document.getElementById("playerLongitude");

    if (!locationButton || !recommendationForm) {
        return;
    }

    function getUserLocation() {
        if (!navigator.geolocation) {
            locationStatus.textContent =
                "Your browser does not support location services.";
            return;
        }

        locationStatus.textContent = "Requesting your location...";
        locationButton.disabled = true;

        navigator.geolocation.getCurrentPosition(
            function (position) {
                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;

                latitudeInput.value = latitude;
                longitudeInput.value = longitude;

                locationStatus.textContent =
                    "Location detected! Finding nearby sports events...";

                recommendationForm.requestSubmit();
            },

            function (error) {
                locationButton.disabled = false;

                if (error.code === error.PERMISSION_DENIED) {
                    locationStatus.textContent =
                        "Location permission denied. You can still enter your location manually.";
                } else if (error.code === error.POSITION_UNAVAILABLE) {
                    locationStatus.textContent =
                        "Your location is currently unavailable. Please try again or enter it manually.";
                } else if (error.code === error.TIMEOUT) {
                    locationStatus.textContent =
                        "Location request timed out. Please try again.";
                } else {
                    locationStatus.textContent =
                        "Unable to detect your location. Please enter it manually.";
                }

                console.error("Location error:", error.message);
            },

            {
                enableHighAccuracy: true,
                timeout: 15000,
                maximumAge: 0
            }
        );
    }

    locationButton.addEventListener("click", getUserLocation);
});
