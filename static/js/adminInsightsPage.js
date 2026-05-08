import { fetchAdminLogs, fetchUserInsights } from "./api.js";
import { renderDonutChart, renderRecords, renderScatterMatrix3D } from "./adminCharts.js";
import { initAdminSession } from "./adminSession.js";


function renderInsightKpis(kpis) {
  const host = document.querySelector("#insights-kpis");
  host.innerHTML = [
    { label: "Avg basket", value: `Rs ${kpis.average_basket_value}`, note: "Average order value across completed grocery orders." },
    { label: "Repeat rate", value: `${kpis.repeat_customer_rate}%`, note: "Share of customers with strong repeat ordering behavior." },
    { label: "High-intent users", value: kpis.high_intent_users, note: "Users with strong recent purchase or session signals." },
  ].map((item) => `<article class="kpi-card"><p class="eyebrow">${item.label}</p><div class="kpi-value">${item.value}</div><p class="kpi-note">${item.note}</p></article>`).join("");
}


async function loadInsights(session) {
  const [insights, logs] = await Promise.all([fetchUserInsights(session.token), fetchAdminLogs(session.token)]);
  renderInsightKpis(insights.kpis);
  renderScatterMatrix3D(document.querySelector("#scatter-matrix"), insights.scatter_matrix_3d);
  renderRecords(document.querySelector("#top-customers"), insights.top_customers, [
    { label: "Customer", key: "name" },
    { label: "Segment", key: "segment" },
    { label: "Intent", key: "intent_score" },
  ]);
  renderDonutChart(document.querySelector("#segment-mix"), Object.entries(insights.segment_mix).map(([label, value]) => ({ label, value })));
  renderRecords(document.querySelector("#admin-logs"), logs.entries, [
    { label: "Actor", key: "actor" },
    { label: "Action", key: "action" },
    { label: "Module", key: "module" },
    { label: "When", key: "timestamp" },
  ]);
}


initAdminSession(loadInsights);
