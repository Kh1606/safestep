import {
  MODE_COSTING,
  applyMode,
  renderLayerUI,
  toggleLayer,
  getEnabledLayerNames
} from "./layers.js";

import { createLegendControl } from "./legend.js";

function msg(t) {
  document.getElementById("msg").textContent = t || "";
}

function decodePolyline6(str){
  let index=0, lat=0, lng=0, coords=[];
  while(index < str.length){
    let shift=0, result=0, b;
    do { b=str.charCodeAt(index++)-63; result|=(b&0x1f)<<shift; shift+=5; } while(b>=0x20);
    let dlat = (result & 1) ? ~(result>>1) : (result>>1);
    lat += dlat;

    shift=0; result=0;
    do { b=str.charCodeAt(index++)-63; result|=(b&0x1f)<<shift; shift+=5; } while(b>=0x20);
    let dlng = (result & 1) ? ~(result>>1) : (result>>1);
    lng += dlng;

    coords.push([lat/1e6, lng/1e6]);
  }
  return coords;
}

async function addSeongdongMask(map, L) {
  const res = await fetch("/layers/seongdong_boundary");
  if (!res.ok) { msg("⚠ seongdong_boundary not found"); return; }

  const gj = await res.json();
  const ring = gj?.features?.[0]?.geometry?.coordinates?.[0];
  if (!ring) { msg("⚠ invalid boundary geometry"); return; }

  const inner = ring.map(([lon, lat]) => [lat, lon]);
  const outer = [[90,-180],[90,180],[-90,180],[-90,-180],[90,-180]];

  L.polygon([outer, inner], {
    stroke:false, fillColor:"#000", fillOpacity:0.55, interactive:false
  }).addTo(map);

  const outline = L.polyline(inner, { color:"#fff", weight:3, opacity:0.9 }).addTo(map);
  const b = outline.getBounds();
  map.fitBounds(b, { padding:[20,20] });
  map.setMaxBounds(b.pad(0.25));
}

// helper
function clearEl(el) { if (el) el.innerHTML = ""; }

export async function init() {
  const L = window.L;

  const map = L.map("map").setView([37.554, 127.04], 13);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19 }).addTo(map);

  await addSeongdongMask(map, L);

  // UI refs
  const modeSel = document.getElementById("modeSel");
  const layerBox = document.getElementById("layerBox");

  // Address UI
  const startAddr = document.getElementById("startAddr");
  const endAddr = document.getElementById("endAddr");
  const btnStartSearch = document.getElementById("btnStartSearch");
  const btnEndSearch = document.getElementById("btnEndSearch");
  const startResults = document.getElementById("startResults");
  const endResults = document.getElementById("endResults");

  // Legend
  const legend = createLegendControl(L, map);

  // Route state
  let start = null;
  let end = null;
  let startMarker = null;
  let endMarker = null;
  let routeLine = null;

  const clearRoute = () => {
    if (routeLine) map.removeLayer(routeLine);
    routeLine = null;
  };

  const clearPoints = () => {
    start = null;
    end = null;

    if (startMarker) map.removeLayer(startMarker);
    if (endMarker) map.removeLayer(endMarker);
    startMarker = null;
    endMarker = null;

    clearEl(startResults);
    clearEl(endResults);
  };

  function setPoint(kind, lat, lon) {
    const ll = L.latLng(lat, lon);

    if (kind === "start") {
      start = { lat, lon };
      if (!startMarker) startMarker = L.marker(ll).addTo(map);
      else startMarker.setLatLng(ll);
    } else {
      end = { lat, lon };
      if (!endMarker) endMarker = L.marker(ll).addTo(map);
      else endMarker.setLatLng(ll);
    }

    map.panTo(ll);
  }

  async function requestRoute() {
    if (!start || !end) return;

    const mode = modeSel.value;

    // base costing
    let costing = MODE_COSTING[mode] || "pedestrian";
    let body = { locations: [start, end], costing };

    // wheelchair = pedestrian + type
    if (mode === "Wheelchair") {
      body.costing = "pedestrian";
      body.costing_options = { pedestrian: { type: "wheelchair" } };
    }

    const res = await fetch("/api/route", {
      method: "POST",
      headers: { "Content-Type":"application/json" },
      body: JSON.stringify(body)
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      msg("Route error: " + (data.detail || "unknown"));
      return;
    }

    const shape = data?.trip?.legs?.[0]?.shape;
    if (!shape) { msg("Route error: no shape"); return; }

    const pts = decodePolyline6(shape);
    clearRoute();
    routeLine = L.polyline(pts, { color:"#111", weight:6, opacity:0.9 }).addTo(map);
    map.fitBounds(routeLine.getBounds(), { padding:[30,30] });

    const distKm = data?.trip?.summary?.length ?? 0;
    const sec = data?.trip?.summary?.time ?? 0;
    msg(`Mode: ${mode} • Distance: ${distKm.toFixed(2)} km • ETA: ${Math.round(sec/60)} min`);
  }

  async function doSearch(q, resultsEl, kind) {
    clearEl(resultsEl);
    q = (q || "").trim();
    if (q.length < 2) return;

    let res;
    try {
      res = await fetch(`/api/geocode?q=${encodeURIComponent(q)}&limit=5`);
    } catch (e) {
      resultsEl.innerHTML = `<div class="addrItem">Network error</div>`;
      return;
    }

    const items = await res.json().catch(() => []);
    if (!Array.isArray(items) || items.length === 0) {
      resultsEl.innerHTML = `<div class="addrItem">No results</div>`;
      return;
    }

    for (const it of items) {
      const btn = document.createElement("button");
      btn.className = "addrItem";
      btn.type = "button";
      btn.textContent = it.display_name || `${it.lat}, ${it.lon}`;
      btn.onclick = async () => {
        setPoint(kind, it.lat, it.lon);
        clearEl(resultsEl);
        await requestRoute();
      };
      resultsEl.appendChild(btn);
    }
  }

  // Buttons
  btnStartSearch.onclick = () => doSearch(startAddr.value, startResults, "start");
  btnEndSearch.onclick = () => doSearch(endAddr.value, endResults, "end");
  startAddr.addEventListener("keydown", (e) => { if (e.key === "Enter") btnStartSearch.click(); });
  endAddr.addEventListener("keydown", (e) => { if (e.key === "Enter") btnEndSearch.click(); });

  // Clear buttons
  document.getElementById("clearPts").onclick = () => { clearPoints(); clearRoute(); msg(""); };
  document.getElementById("clearRoute").onclick = () => { clearRoute(); msg(""); };

  // Layers + legend sync
  const refreshUI = async () => {
    const mode = modeSel.value;

    await applyMode(map, L, mode, msg);

    // legend after preset applied
    legend.update(mode, getEnabledLayerNames());

    renderLayerUI(layerBox, mode, async (layerName, on) => {
      await toggleLayer(map, L, layerName, on, msg);
      legend.update(modeSel.value, getEnabledLayerNames());
    });

    // if route already exists, rerun with new mode
    await requestRoute();
  };

  modeSel.addEventListener("change", refreshUI);
  await refreshUI();

  // Map click: set start then end, then reroute
  map.on("click", async (e) => {
    msg("");

    if (!start) {
      setPoint("start", e.latlng.lat, e.latlng.lng);
    } else if (!end) {
      setPoint("end", e.latlng.lat, e.latlng.lng);
    } else {
      // third click resets start
      clearPoints();
      clearRoute();
      setPoint("start", e.latlng.lat, e.latlng.lng);
    }

    await requestRoute();
  });
}
