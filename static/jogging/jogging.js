let map, polyline;
let path = [];
let watchId;
let startTime;

function startJogging() {

    map = L.map("map").setView([0, 0], 18);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19
    }).addTo(map);

    polyline = L.polyline([], { color: "red", weight: 4 }).addTo(map);

    startTime = Date.now();

    watchId = navigator.geolocation.watchPosition(
        pos => {
            const lat = pos.coords.latitude;
            const lng = pos.coords.longitude;

            const point = [lat, lng];
            path.push(point);
            polyline.addLatLng(point);
            map.setView(point, 18);

            updateStats();
        },
        err => alert("Enable GPS permission"),
        {
            enableHighAccuracy: true,
            maximumAge: 0,
            timeout: 10000
        }
    );
}

function updateStats() {
    const distance = calculateDistance(path);
    const duration = (Date.now() - startTime) / 60000;
    const speed = duration > 0 ? distance / (duration / 60) : 0;
    const calories = distance * 60;

    document.getElementById("time").innerText = duration.toFixed(1);
    document.getElementById("distance").innerText = distance.toFixed(2);
    document.getElementById("speed").innerText = speed.toFixed(2);
    document.getElementById("calories").innerText = calories.toFixed(0);
}

function stopJogging() {
    navigator.geolocation.clearWatch(watchId);

    const duration = (Date.now() - startTime) / 60000;
    const distance = calculateDistance(path);
    const speed = distance / (duration / 60);
    const calories = distance * 60;

    fetch("/jogging/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            path,
            duration: Math.round(duration),
            distance,
            speed,
            calories
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.role === "player")
            window.location.href = "/jogging/history/player";
        else
            window.location.href = "/jogging/history/coach";
    });
}

/* DISTANCE FORMULA */
function calculateDistance(points) {
    let d = 0;
    for (let i = 1; i < points.length; i++) {
        d += haversine(points[i-1], points[i]);
    }
    return d;
}

function haversine(p1, p2) {
    const R = 6371;
    const dLat = (p2[0]-p1[0]) * Math.PI/180;
    const dLng = (p2[1]-p1[1]) * Math.PI/180;
    const a =
        Math.sin(dLat/2)**2 +
        Math.cos(p1[0]*Math.PI/180) *
        Math.cos(p2[0]*Math.PI/180) *
        Math.sin(dLng/2)**2;
    return R * (2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)));
}
