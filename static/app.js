/*
name: app.js
function: this file contains the javascript code for the Google Maps api, the search bar, and the distance matrix service.
author: Logan Hunter
*/
function initMap() {
  // Create the map.
  const map = new google.maps.Map(document.getElementById('map'), {
    zoom: 7,
    center: {lat: 54.499396, lng: -2.335770},
  });

  // Fetch the charities GeoJSON data.
  fetch('static/charities.json')
      .then(response => response.json())
      .then(data => {
        // Add the GeoJSON data to the map.
        map.data.addGeoJson(data);

        map.data.setStyle((feature) => {
          return {
            icon: {
              url: 'static/images/charity.png',
              scaledSize: new google.maps.Size(50, 50),
            },
          };
        })


        const infoWindow = new google.maps.InfoWindow();

        // Show the information for a charity when its marker is clicked.
        map.data.addListener('click', (event) => {
          const name = event.feature.getProperty('name');
          const address = event.feature.getProperty('address');
          const postcode = event.feature.getProperty('postcode');
          const charityLink = '/locations/' + encodeURIComponent(name);
          const position = event.feature.getGeometry().get();
          const content = `
          <h2><a href="${charityLink}">${name}</a></h2>
            <p>${address}</p>
            <p><b>Postcode:</b> ${postcode}</p>
        `;

          infoWindow.setContent(content);
          infoWindow.setPosition(position);
          infoWindow.setOptions({pixelOffset: new google.maps.Size(0, -30)});
          infoWindow.open(map);
        });

  // Build and add the search bar
  const card = document.createElement('div');
  const titleBar = document.createElement('div');
  const title = document.createElement('div');
  const container = document.createElement('div');
  const input = document.createElement('input');
  const options = {
    types: ['postal_code'],
    componentRestrictions: {country: 'gb'},
  };

  card.setAttribute('id', 'pac-card');
  title.setAttribute('id', 'title');
  title.textContent = 'Find the nearest store';
  titleBar.appendChild(title);
  container.setAttribute('id', 'pac-container');
  input.setAttribute('id', 'pac-input');
  input.setAttribute('type', 'text');
  input.setAttribute('placeholder', 'Enter a postcode');
  container.appendChild(input);
  card.appendChild(titleBar);
  card.appendChild(container);
  map.controls[google.maps.ControlPosition.TOP_RIGHT].push(card);

  // Make the search bar into a Places Autocomplete search bar and select
  // which detail fields should be returned about the place that
  // the user selects from the suggestions.
  const autocomplete = new google.maps.places.Autocomplete(input, options);

  autocomplete.setFields(
      ['address_components', 'geometry', 'name']);

  // Set the origin point when the user selects an address
  const originMarker = new google.maps.Marker({map: map});
  originMarker.setVisible(false);
  let originLocation = map.getCenter();

  autocomplete.addListener('place_changed', async () => {
    originMarker.setVisible(false);
    originLocation = map.getCenter();
    const place = autocomplete.getPlace();

    if (!place.geometry) {
      // If the place has no geometry, it's likely a postcode
      const geocoder = new google.maps.Geocoder();
      geocoder.geocode({address: place.name, componentRestrictions: {country: 'GB'}}, (results, status) => {
        if (status === 'OK') {
          if (results[0]) {
            // Recenter the map to the selected postcode location
            originLocation = results[0].geometry.location;
            map.setCenter(originLocation);
            map.setZoom(9);
            originMarker.setPosition(originLocation);
            originMarker.setVisible(true);
          } else {
            window.alert('No results found');
          }
        } else {
          window.alert('Geocoder failed due to: ' + status);
        }
      });
    } else {
      // Recenter the map to the selected address
      originLocation = place.geometry.location;
      map.setCenter(originLocation);
      map.setZoom(9);
      originMarker.setPosition(originLocation);
      originMarker.setVisible(true);

      // Use the selected address as the origin to calculate distances
      // to each of the store locations
      const rankedStores = await calculateDistances(map.data, originLocation);
      showStoresList(map.data, rankedStores);
    }
  });

  async function calculateDistances(data, origin) {
    const stores = [];
    const destinations = [];

    // Build parallel arrays for the store names and destinations
    data.forEach((store) => {
      const storeName = store.getProperty('name');
      const storeLoc = store.getGeometry().get();

      stores.push(storeName);
      destinations.push(storeLoc);
    });

    // Retrieve the distances of each store from the origin
    // The returned list will be in the same order as the destinations list
    const service = new google.maps.DistanceMatrixService();
    const getDistanceMatrix =
        (service, parameters) => new Promise((resolve, reject) => {
          service.getDistanceMatrix(parameters, (response, status) => {
            if (status !== google.maps.DistanceMatrixStatus.OK) {
              reject(response);
            } else {
              const distances = [];
              const results = response.rows[0].elements;
              for (let j = 0; j < results.length; j++) {
                const element = results[j];
                const distanceText = element.distance.text;
                const distanceVal = element.distance.value;
                const distanceObject = {
                  storeName: stores[j],
                  distanceText: distanceText,
                  distanceVal: distanceVal,
                };
                distances.push(distanceObject);
              }

              resolve(distances);
            }
          });
        });

    const distancesList = await getDistanceMatrix(service, {
      origins: [origin],
      destinations: destinations,
      travelMode: 'DRIVING',
      unitSystem: google.maps.UnitSystem.METRIC,
    });

    distancesList.sort((first, second) => {
      return first.distanceVal - second.distanceVal;
    });

    return distancesList;
  }

  function showStoresList(data, stores) {
    if (stores.length === 0) {
      console.log('empty stores');
      return;
    }

    let panel = document.createElement('div');
    panel.setAttribute('id', 'panel');
    panel.classList.add('hidden');
    panel.style.width = '200px'; // Adjust the width here

    // Position the panel relative to the map container
    const mapContainer = map.getDiv();
    mapContainer.style.position = 'relative';
    mapContainer.appendChild(panel);

    // Clear the previous details
    panel.innerHTML = '';

    stores.forEach((store) => {
    // Add store details with text formatting
    const name = document.createElement('p');
    name.classList.add('place');

    // Create anchor tag for the charity page link
    const link = document.createElement('a');
    link.href = '/locations/' + encodeURIComponent(store.storeName);
    link.textContent = store.storeName;
    name.appendChild(link);

    panel.appendChild(name);
    const distanceText = document.createElement('p');
    distanceText.classList.add('distanceText');
    distanceText.textContent = store.distanceText;
    panel.appendChild(distanceText);
  });

    // If the panel already exists, replace it. Else, append it to the map container.
    const existingPanel = document.getElementById('panel');
    if (existingPanel) {
      mapContainer.replaceChild(panel, existingPanel);
    } else {
      mapContainer.appendChild(panel);
    }

    // Open the panel
    panel.classList.remove('hidden');

  }
  });
}