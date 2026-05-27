// app/static/js/icons.js
export function makeEmojiIcon(L, emoji, bg) {
  return L.divIcon({
    className: "",
    html: `<div class="emojiMarker" style="background:${bg}">${emoji}</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -14],
  });
}

function sub(props) {
  return (props?.SUB_NAME || "").trim();
}

export function getMarkerIcon(L, layerName, props) {
  const s = sub(props);

  // --- Default ---
  if (layerName === "default_public_restrooms") {
    return makeEmojiIcon(L, "🚻", s.includes("상시") ? "#2e7d32" : "#ef6c00");
  }
  if (layerName === "default_people_centred_pois") {
    if (s.includes("공원_보행")) return makeEmojiIcon(L, "🚶‍♂️🚪", "#2e7d32");
    if (s.includes("공원_차량")) return makeEmojiIcon(L, "🚗🚪", "#2e7d32");
    if (s.includes("하천_보행")) return makeEmojiIcon(L, "🚶‍♂️🌊", "#1565c0");
    if (s.includes("하천_차량")) return makeEmojiIcon(L, "🚗🌊", "#1565c0");
    return makeEmojiIcon(L, "🌳", "#2e7d32");
  }
  if (layerName === "default_parks") {
    if (s.includes("화장실")) return makeEmojiIcon(L, "🚻", "#455a64");
    if (s.includes("주차장")) return makeEmojiIcon(L, "🅿️", "#455a64");
    if (s.includes("안내시설")) return makeEmojiIcon(L, "ℹ️", "#455a64");
    if (s.includes("수경")) return makeEmojiIcon(L, "💧", "#1565c0");
    if (s.includes("동상")) return makeEmojiIcon(L, "🗿", "#6d4c41");
    if (s.includes("캠핑")) return makeEmojiIcon(L, "⛺", "#2e7d32");
    if (s.includes("휠체어")) return makeEmojiIcon(L, "♿", "#6a1b9a");
    if (s.includes("유아차")) return makeEmojiIcon(L, "👶", "#ad1457");
    if (["게이트볼","농구장","배드민턴장","테니스장"].some(x=>s.includes(x)))
      return makeEmojiIcon(L, "🏟️", "#00897b");
    if (s.includes("잔디")) return makeEmojiIcon(L, "🏞️", "#2e7d32");
    return makeEmojiIcon(L, "🌳", "#2e7d32");
  }

  // --- Wheelchair ---
  if (layerName === "wc_chargers") {
    return makeEmojiIcon(L, "🔌", s.includes("정상") ? "#2e7d32" : "#9e9e9e");
  }
  if (layerName === "wc_accessibility_status") {
    if (s.startsWith("1")) return makeEmojiIcon(L, "♿", "#2e7d32");
    if (s.startsWith("2")) return makeEmojiIcon(L, "♿", "#f9a825");
    if (s.startsWith("3")) return makeEmojiIcon(L, "♿", "#c62828");
    return makeEmojiIcon(L, "♿", "#1565c0");
  }
  if (layerName === "wc_dental_disabled") return makeEmojiIcon(L, "🦷", "#6a1b9a");

  // --- Elder ---
  if (layerName.startsWith("elder_")) {
    if (layerName.includes("pharmacy")) return makeEmojiIcon(L, "💊🌙", "#5d4037");
    if (layerName.includes("mental")) return makeEmojiIcon(L, "🧠", "#5d4037");
    return makeEmojiIcon(L, "🏥🌙", "#5d4037");
  }

  // --- Bike ---
  if (layerName === "bike_facilities") {
    if (s.includes("공기")) return makeEmojiIcon(L, "💨", "#2e7d32");
    if (s.includes("수리")) return makeEmojiIcon(L, "🔧", "#2e7d32");
    if (s.includes("재생")) return makeEmojiIcon(L, "♻️🚲", "#2e7d32");
    return makeEmojiIcon(L, "🚲", "#2e7d32");
  }

  // fallback
  return makeEmojiIcon(L, "📍", "#37474f");
}

// Small icon for legend
export function legendIconHTML(emoji, bg) {
  return `<div class="emojiMarker emojiMarker--sm" style="background:${bg}">${emoji}</div>`;
}

export function legendLineHTML(color) {
  return `<div class="legendLine" style="border-top-color:${color}"></div>`;
}

// Legend items are tied to layers, so we can hide them if that layer is OFF
const LEGEND_BY_MODE = {
  Default: [
    { layer: "default_parks", label: "Park / green space", emoji: "🌳", bg: "#2e7d32" },
    { layer: "default_public_restrooms", label: "Restroom (always open)", emoji: "🚻", bg: "#2e7d32" },
    { layer: "default_public_restrooms", label: "Restroom (scheduled)", emoji: "🚻", bg: "#ef6c00" },
    { layer: "default_people_centred_pois", label: "Park entrance (walk)", emoji: "🚶‍♂️🚪", bg: "#2e7d32" },
    { layer: "default_people_centred_pois", label: "Park entrance (car)", emoji: "🚗🚪", bg: "#2e7d32" },
    { layer: "default_people_centred_pois", label: "River entrance (walk)", emoji: "🚶‍♂️🌊", bg: "#1565c0" },
    { layer: "default_people_centred_pois", label: "River entrance (car)", emoji: "🚗🌊", bg: "#1565c0" },
    { layer: "default_maple_roads", label: "Road line (maple roads)", type: "line", color: "#111" },
  ],

  Wheelchair: [
    { layer: "wc_paths", label: "Wheelchair path / guidance", type: "line", color: "#111" },
    { layer: "wc_chargers", label: "Charger (operating)", emoji: "🔌", bg: "#2e7d32" },
    { layer: "wc_chargers", label: "Charger (not operating)", emoji: "🔌", bg: "#9e9e9e" },
    { layer: "wc_accessibility_status", label: "Accessibility: good", emoji: "♿", bg: "#2e7d32" },
    { layer: "wc_accessibility_status", label: "Accessibility: ok", emoji: "♿", bg: "#f9a825" },
    { layer: "wc_accessibility_status", label: "Accessibility: bad", emoji: "♿", bg: "#c62828" },
    { layer: "wc_dental_disabled", label: "Dental (disabled)", emoji: "🦷", bg: "#6a1b9a" },
    // Optional layer (big)
    { layer: "wc_safe_routes", label: "Safe routes (overlay)", type: "line", color: "#111" },
  ],

  Elder: [
    { layer: "elder_night_holiday_clinics", label: "Night / holiday clinic", emoji: "🏥🌙", bg: "#5d4037" },
    { layer: "elder_late_night_pharmacy", label: "Late-night pharmacy", emoji: "💊🌙", bg: "#5d4037" },
    { layer: "elder_mental_health", label: "Mental health", emoji: "🧠", bg: "#5d4037" },
  ],

  Bicycle: [
    { layer: "bike_paths", label: "Bike path line", type: "line", color: "#111" },
    { layer: "bike_facilities", label: "Air pump", emoji: "💨", bg: "#2e7d32" },
    { layer: "bike_facilities", label: "Repair", emoji: "🔧", bg: "#2e7d32" },
    { layer: "bike_facilities", label: "Recycled bike shop", emoji: "♻️🚲", bg: "#2e7d32" },
  ],
};

export function getLegendItems(mode, enabledSet) {
  const items = LEGEND_BY_MODE[mode] || [];
  // show only legend rows whose layer is currently enabled
  if (!enabledSet) return items;
  return items.filter((it) => !it.layer || enabledSet.has(it.layer));
}

