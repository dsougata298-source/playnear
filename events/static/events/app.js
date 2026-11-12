
document.addEventListener("DOMContentLoaded", () => {

    const searchInput = document.getElementById("searchInput");
    const locationInput = document.getElementById("locationInput");
    const searchButton = document.getElementById("searchButton");
    const cards = document.querySelectorAll(".event-card");
    const chips = document.querySelectorAll(".filter-chip");
    const noResults = document.getElementById("noResults");

    let selectedSport = "all";

    function filterEvents() {

        const query = searchInput
            ? searchInput.value.trim().toLowerCase()
            : "";

        const location = locationInput
            ? locationInput.value.trim().toLowerCase()
            : "";

        let visibleCount = 0;

        cards.forEach((card) => {

            const cardText = card.textContent.toLowerCase();

            const cardSport =
                card.querySelector(".event-sport")
                    ?.textContent.trim().toLowerCase() || "";

            const matchesSearch = cardText.includes(query);
            const matchesLocation = cardText.includes(location);

            const matchesSport =
                selectedSport === "all" ||
                cardSport.includes(selectedSport);

            const visible =
                matchesSearch && matchesLocation && matchesSport;

            card.hidden = !visible;

            if (visible) {
                visibleCount++;
            }
        });

        if (noResults) {
            noResults.hidden = visibleCount > 0;
        }
    }

    if (searchButton) {
        searchButton.addEventListener("click", filterEvents);
    }

    if (searchInput) {
        searchInput.addEventListener("input", filterEvents);
    }

    if (locationInput) {
        locationInput.addEventListener("input", filterEvents);
    }

    chips.forEach((chip) => {

        chip.addEventListener("click", () => {

            selectedSport = chip.dataset.sport.toLowerCase();

            chips.forEach((item) => {
                item.classList.remove("active");
            });

            chip.classList.add("active");

            filterEvents();
        });

    });

});
