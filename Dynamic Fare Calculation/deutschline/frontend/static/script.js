// Define the stations array (you can fetch this dynamically from your backend)
const stations = ["Frankfurt Hauptbahnhof", "Mannheim Hauptbahnhof", "Heidelberg Hauptbahnhof", "Stuttgart Hauptbahnhof", "Ulm Hauptbahnhof", "Munich Hauptbahnhof", "Dortmund Hauptbahnhof", "Essen Hauptbahnhof", "Dusseldorf Hauptbahnhof", "Koln Hauptbahnhof", "Bonn Hauptbahnhof"];

// Function to populate dropdown with stations
function populateDropdown(selectId, stationList) {
    const select = document.getElementById(selectId);
    select.innerHTML = ""; // Clear existing options
    stationList.forEach(station => {
        const option = document.createElement('option');
        option.text = station;
        option.value = station;
        select.add(option);
    });
}

// Function to initialize the page
function initializePage() {
    // Populate current location dropdown
    populateDropdown('current-location', stations);

    // Populate destination dropdown
    populateDropdown('destination', stations);
}

// Call initializePage function when the DOM content is loaded
document.addEventListener('DOMContentLoaded', initializePage);

// Parse query parameters and set form field values
document.addEventListener('DOMContentLoaded', function() {
    // Parse query parameters
    const queryString = window.location.search;
    const urlParams = new URLSearchParams(queryString);

    // Get selected options from query parameters
    const currentLocation = urlParams.get('currentLocation');
    const destination = urlParams.get('destination');
    const date = urlParams.get('date');
    const time = urlParams.get('time');
    const travelClass = urlParams.get('class');

    // Set values of HTML elements with IDs
    document.getElementById("current-location").value = currentLocation;
    document.getElementById("destination").value = destination;
    document.getElementById("date").value = date;
    document.getElementById("time").value = time;
    document.getElementById("class").value = travelClass;
});
