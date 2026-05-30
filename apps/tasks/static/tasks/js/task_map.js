document.addEventListener('DOMContentLoaded', function() {
    var mapEl = document.getElementById('map');
    if (!mapEl) return;

    var map = L.map('map').setView([31.6295, -7.9811], 13);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; OSM',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);

    if (!window.mapTasks || window.mapTasks.length === 0) {
        map.setView([31.6295, -7.9811], 10);
        return;
    }

    var customIcon = L.divIcon({
        className: 'sq-map-marker',
        html: '<div class="sq-marker-pin"></div>',
        iconSize: [30, 42],
        iconAnchor: [15, 42],
        popupAnchor: [0, -42]
    });

    var markers = [];
    window.mapTasks.forEach(function(task) {
        if (isNaN(task.lat) || isNaN(task.lng)) return;

        var popupHtml =
            '<div class="sq-popup">' +
            '  <div class="sq-popup-cat">' + task.category + '</div>' +
            '  <h4>' + task.title + '</h4>' +
            '  <div class="sq-popup-reward">' + task.reward + ' Dh</div>' +
            (task.address ? '<p class="sq-popup-addr">' + task.address + '</p>' : '') +
            '  <a href="/tasks/' + task.id + '/" class="sq-popup-btn">Voir la mission</a>' +
            '</div>';

        var marker = L.marker([task.lat, task.lng], { icon: customIcon }).addTo(map);
        marker.bindPopup(popupHtml, { maxWidth: 280 });
        markers.push(marker);
    });

    if (markers.length === 1) {
        map.setView(markers[0].getLatLng(), 14);
    } else if (markers.length > 1) {
        var group = L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.15));
    }
});
