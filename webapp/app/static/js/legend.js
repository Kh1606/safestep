// app/static/js/legend.js
import { getLegendItems, legendIconHTML, legendLineHTML } from "./icons.js";

export function createLegendControl(L, map) {
  const ctrl = L.control({ position: "topright" });
  let div;

  function render(mode, enabledSet) {
    const items = getLegendItems(mode, enabledSet);

    const rows = items.map((it) => {
      const iconHtml =
        it.type === "line"
          ? legendLineHTML(it.color || "#111")
          : legendIconHTML(it.emoji, it.bg);

      return `
        <div class="legendRow">
          ${iconHtml}
          <div class="legendLabel">${it.label}</div>
        </div>
      `;
    }).join("");

    div.innerHTML = `
      <div class="legendTitle">${mode} legend</div>
      ${rows || `<div class="legendEmpty">No active layers</div>`}
    `;
  }

  ctrl.onAdd = function () {
    div = L.DomUtil.create("div", "legendBox");
    L.DomEvent.disableClickPropagation(div);
    L.DomEvent.disableScrollPropagation(div);
    div.innerHTML = `<div class="legendTitle">Legend</div>`;
    return div;
  };

  ctrl.addTo(map);

  return {
    update(mode, enabledLayerNames) {
      const set = new Set(enabledLayerNames || []);
      render(mode, set);
    },
  };
}
