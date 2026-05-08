import { fetchAdminDashboard } from "./api.js";
import { renderCategoryBars, renderDonutChart, renderSalesChart } from "./adminCharts.js";
import { getSession, initAdminSession } from "./adminSession.js";


const state = { range: "7d" };


function showOverviewSkeletons() {
  ["#kpi-grid", "#sales-chart", "#inventory-chart", "#category-chart", "#alerts-panel"].forEach((selector) => {
    const element = document.querySelector(selector);
    if (element) {
      element.innerHTML = "<div class='skeleton'></div>";
    }
  });
}


function renderKpis(kpis) {
  const kpiGrid = document.querySelector("#kpi-grid");
  const cards = [
    { label: "Revenue", value: `Rs ${kpis.today_revenue}`, note: "Total non-cancelled revenue in the selected range." },
    { label: "Active orders", value: kpis.active_orders, note: "Orders still in active fulfillment lanes." },
    { label: "Low-stock SKUs", value: kpis.low_stock_skus, note: "Items touching or below reorder threshold." },
    { label: "Perishable watch", value: kpis.perishable_attention, note: "Fresh products that need immediate admin attention." },
  ];
  kpiGrid.innerHTML = cards.map((card) => `<article class="kpi-card"><p class="eyebrow">${card.label}</p><div class="kpi-value">${card.value}</div><p class="kpi-note">${card.note}</p></article>`).join("");
}


function renderAlerts(alerts) {
  const host = document.querySelector("#alerts-panel");
  host.innerHTML = alerts.map((alert) => `<article class="alert-card ${alert.severity}"><div><strong>${alert.headline}</strong><p class="muted-label">${alert.detail}</p></div><span>${alert.type}</span></article>`).join("");
}


async function loadOverview(session) {
  showOverviewSkeletons();
  const payload = await fetchAdminDashboard(session.token, state.range);
  renderKpis(payload.kpis);
  renderSalesChart(document.querySelector("#sales-chart"), payload.charts.sales_trends);
  renderCategoryBars(document.querySelector("#category-chart"), payload.charts.category_performance);
  renderDonutChart(document.querySelector("#inventory-chart"), payload.charts.inventory_mix);
  renderAlerts(payload.alerts);
  document.querySelector("#updated-at").textContent = `Updated ${new Date(payload.updated_at).toLocaleString()}`;
}


document.querySelectorAll(".filter-chip").forEach((button) => {
  button.addEventListener("click", async () => {
    document.querySelectorAll(".filter-chip").forEach((item) => item.classList.remove("is-active"));
    button.classList.add("is-active");
    state.range = button.dataset.range;
    const session = getSession();
    if (session.token) {
      await loadOverview(session);
    }
  });
});


initAdminSession(loadOverview);
