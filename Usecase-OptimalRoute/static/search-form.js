// search-form.js
const inputClasses = "w-full mt-1 p-2 border border-zinc-300 dark:border-zinc-700 rounded-md focus:outline-none focus:ring focus:ring-indigo-500 dark:focus:ring-indigo-300";
const labelClasses = "block text-sm font-medium text-zinc-700 dark:text-zinc-300";
const buttonClasses = "bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded mt-4 focus:outline-none focus:shadow-outline";

// search-form.js

class SearchForm extends HTMLElement {
  connectedCallback() {
    this.render();
  }

  render() {
    this.innerHTML = `
      <div class="container mx-auto p-6 bg-white rounded-lg shadow-md">
        <div class="text-center mt-6">
          <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT_6c3ZvXW6vxNSbjBzFepyOjPVMRf4a70kwCAspBGFPA&s" alt="Train Image" class="mx-auto mb-8" style="max-width: 200px;">
        </div>
        <form id="searchForm" action="/find_route" method="POST" class="text-center">
          <div class="flex flex-col items-center"> <!-- Flex container -->
            <div class="max-w-md mb-4"> <!-- Set the maximum width of the container -->
              <label for="start_station" class="block mb-2 text-sm font-medium text-gray-700">Source</label>
              <input type="text" id="start_station" name="start_station" class="${inputClasses}">
            </div>
            <div class="max-w-md mb-4"> <!-- Set the maximum width of the container -->
              <label for="end_station" class="block mb-2 text-sm font-medium text-gray-700">Destination</label>
              <input type="text" id="end_station" name="end_station" class="${inputClasses}">
            </div>
          </div>
          <button type="submit" class="${buttonClasses}" id="findRouteBtn">Find Route</button>
        </form>
      </div>
    `;

    // Add event listener to the submit button
    const findRouteBtn = this.querySelector("#findRouteBtn");
    findRouteBtn.addEventListener("click", (event) => {
      const startStationInput = this.querySelector("#start_station");
      const endStationInput = this.querySelector("#end_station");

      if (startStationInput.value.trim() === "" || endStationInput.value.trim() === "") {
        // Prevent form submission
        event.preventDefault();
        // Alert the user to fill in the station names
        alert("Please fill in both the start and end station names.");
      }
    });
  }



}

customElements.define('search-form', SearchForm);



