// app/static/js/layers.js
import { getMarkerIcon } from "./icons.js";

export const LAYER_META = {
  // Default
  default_maple_roads: { label: "Maple roads", kind: "line" },
  default_parks: { label: "Parks", kind: "mixed" },
  default_public_restrooms: { label: "Public restrooms", kind: "point" },
  default_people_centred_pois: { label: "People-centred POIs", kind: "point" },

  // Wheelchair
  wc_paths: { label: "Wheelchair paths", kind: "mixed" },
  wc_chargers: { label: "Wheelchair chargers", kind: "point" },
  wc_assistive_centers: { label: "Assistive device centers", kind: "point" },
  wc_accessibility_status: { label: "Accessibility status", kind: "mixed" },
  wc_safe_routes: { label: "Safe routes (big)", kind: "mixed", heavy: true },
  wc_dental_disabled: { label: "Dental clinics (disabled)", kind: "point" },

  // Elder
  elder_night_holiday_clinics: { label: "Night & holiday clinics", kind: "point" },
  elder_late_night_pharmacy: { label: "Late-night pharmacy", kind: "point" },
  elder_mental_health: { label: "Mental health", kind: "point" },

  // Bicycle
  bike_paths: { label: "Bike paths", kind: "line" },
  bike_facilities: { label: "Bike facilities", kind: "point" },
};

export const MODE_PRESET = {
  Default: ["default_maple_roads", "default_parks", "default_public_restrooms"],
  Wheelchair: ["wc_paths", "wc_chargers", "wc_accessibility_status"],
  Elder: ["elder_night_holiday_clinics", "elder_late_night_pharmacy", "elder_mental_health"],
  Bicycle: ["bike_paths", "bike_facilities"],
};

export const MODE_COSTING = {
  Default: "pedestrian",
  Wheelchair: "pedestrian",
  Elder: "pedestrian",
  Bicycle: "bicycle",
};

const layerCache = {}; // name -> Leaflet layer
const enabled = {};    // name -> boolean

function normalizeGeoJSONCollections(gj) {
  // Leaflet sometimes chokes on GeometryCollection. Many of your files wrap a Point inside it.
  if (!gj || !gj.features) return gj;
  for (const f of gj.features) {
    const g = f.geometry;
    if (g && g.type === "GeometryCollection" && Array.isArray(g.geometries) && g.geometries.length === 1) {
      f.geometry = g.geometries[0];
    }
  }
  return gj;
}

function popupHtml(props) {
  const title = props?.CONTENTS_NAME || props?.name || props?.title || "No name";
  const addr = props?.ADDR_NEW || props?.address || "";
  const tel = props?.TEL_NO || props?.tel || "";
  const parts = [`<b>${title}</b>`, addr ? `${addr}` : "", tel ? `${tel}` : ""].filter(Boolean);
  return parts.join("<br>");
}

function lineStyle(name, feature) {
  // If your data has LINE_COLOR/LINE_WEIGHT/LINE_OPACITY you can use them here later.
  if (name.startsWith("wc_")) return { weight: 5, opacity: 0.9 };
  if (name.startsWith("bike_")) return { weight: 5, opacity: 0.9 };
  return { weight: 4, opacity: 0.85 };
}

export async function toggleLayer(map, L, name, on, msgFn) {
  enabled[name] = on;

  if (!on) {
    if (layerCache[name]) map.removeLayer(layerCache[name]);
    return;
  }

  // load once
  if (!layerCache[name]) {
    try {
      const res = await fetch(`layers/${name}.geojson`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      let gj = await res.json();
      gj = normalizeGeoJSONCollections(gj);

      const layer = L.geoJSON(gj, {
        style: (feature) => lineStyle(name, feature),
        pointToLayer: (feature, latlng) => {
          // IMPORTANT: use "name" (current layer key), NOT layerName
          return L.marker(latlng, { icon: getMarkerIcon(L, name, feature?.properties || {}) });
        },
        onEachFeature: (feature, lyr) => {
          if (feature?.properties) lyr.bindPopup(popupHtml(feature.properties));
        },
      });

      layerCache[name] = layer;
    } catch (e) {
      console.error(e);
      msgFn?.(`⚠ Failed to load layer: ${name}`);
      enabled[name] = false;
      return;
    }
  }

  layerCache[name].addTo(map);
}

export async function applyMode(map, L, mode, msgFn) {
  // turn everything off
  for (const name of Object.keys(LAYER_META)) {
    if (enabled[name]) await toggleLayer(map, L, name, false, msgFn);
  }

  // apply preset (keep heavy layers OFF by default)
  const preset = MODE_PRESET[mode] || [];
  for (const name of preset) {
    const meta = LAYER_META[name];
    if (meta?.heavy) continue;
    await toggleLayer(map, L, name, true, msgFn);
  }
}

export function renderLayerUI(container, mode, onToggle) {
  container.innerHTML = "";

  const show = (name) => {
    if (mode === "Default") return name.startsWith("default_");
    if (mode === "Wheelchair") return name.startsWith("wc_");
    if (mode === "Elder") return name.startsWith("elder_");
    if (mode === "Bicycle") return name.startsWith("bike_");
    return false;
  };

  for (const name of Object.keys(LAYER_META)) {
    if (!show(name)) continue;

    const meta = LAYER_META[name];
    const row = document.createElement("div");
    row.className = "layerRow";

    row.innerHTML = `
      <label style="display:flex; gap:8px; align-items:center;">
        <input type="checkbox" id="cb_${name}">
        <span>${meta.label}</span>
        ${meta.heavy ? `<span class="badge">(big)</span>` : ``}
      </label>
    `;

    container.appendChild(row);

    const cb = row.querySelector(`#cb_${name}`);
    cb.checked = Boolean(enabled[name]);
    cb.addEventListener("change", () => onToggle(name, cb.checked));
  }
}
export function getEnabledLayerNames() {
  return Object.keys(enabled).filter((k) => enabled[k]);
}
