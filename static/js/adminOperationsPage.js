import { fetchOperationsSummary } from "./api.js";
import { renderMetricList, renderRecords } from "./adminCharts.js";
import { getSession, initAdminSession } from "./adminSession.js";


const state = { range: "7d" };


async function loadOperations(session) {
  const payload = await fetchOperationsSummary(session.token, state.range);
  renderRecords(document.querySelector("#inventory-watch"), payload.inventory_watch, [
    { label: "Product", key: "name" },
    { label: "Stock", key: "stock_quantity" },
    { label: "Threshold", key: "reorder_threshold" },
  ]);
  renderMetricList(document.querySelector("#top-movers"), payload.top_movers.map((item) => ({
    label: item.name,
    note: `${item.category} velocity`,
    value: item.velocity_score,
  })));
  renderRecords(document.querySelector("#order-lane"), payload.order_lane, [
    { label: "Order", key: "order_id" },
    { label: "Status", key: "status" },
    { label: "Value", key: "total_amount" },
  ]);
}


document.querySelectorAll(".filter-chip").forEach((button) => {
  button.addEventListener("click", async () => {
    document.querySelectorAll(".filter-chip").forEach((item) => item.classList.remove("is-active"));
    button.classList.add("is-active");
    state.range = button.dataset.range;
    const session = getSession();
    if (session.token) {
      await loadOperations(session);
    }
  });
});


initAdminSession(loadOperations);
