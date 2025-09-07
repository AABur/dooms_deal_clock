// API base URL (same logic as main UI)
const API_BASE_URL = window.location.hostname === "localhost"
  ? "http://localhost:8000/api"
  : "/api";

function qs(id) {
  return document.getElementById(id);
}

function setStatus(el, text, cls) {
  el.classList.remove("ok", "warn", "err");
  if (cls) el.classList.add(cls);
  el.textContent = text;
}

async function getLatest() {
  try {
    const res = await fetch(`${API_BASE_URL}/clock/latest`, { method: "GET" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    qs("curTime").textContent = data.time ?? "—";
    qs("curCreated").textContent = data.created_at ?? "—";
    qs("curMsgId").textContent = data.message_id ?? "—";
  } catch (e) {
    qs("curTime").textContent = "—";
    qs("curCreated").textContent = "—";
    qs("curMsgId").textContent = "—";
  }
}

async function triggerFetch() {
  const statusEl = qs("fetchStatus");
  setStatus(statusEl, "Обновление...", "warn");
  const spinner = document.createElement("span");
  spinner.className = "spinner";
  statusEl.appendChild(spinner);
  try {
    const res = await fetch(`${API_BASE_URL}/clock/fetch`, { method: "POST" });
    const ok = res.ok;
    const data = await res.json().catch(() => ({}));
    if (!ok) throw new Error(data?.detail || `HTTP ${res.status}`);
    setStatus(statusEl, `OK: ${data.updates_count} новых`, "ok");
    await getLatest();
  } catch (e) {
    setStatus(statusEl, `Ошибка: ${e.message || e}`, "err");
  }
}

async function triggerReload() {
  const statusEl = qs("reloadStatus");
  const idStr = (qs("reloadId").value || "").trim();
  if (!idStr) {
    setStatus(statusEl, "Укажите ID сообщения", "warn");
    return;
  }
  const msgId = Number(idStr);
  if (!Number.isFinite(msgId) || msgId <= 0) {
    setStatus(statusEl, "Некорректный ID", "warn");
    return;
  }
  setStatus(statusEl, `Перезагрузка ${msgId}...`, "warn");
  const spinner = document.createElement("span");
  spinner.className = "spinner";
  statusEl.appendChild(spinner);
  try {
    const res = await fetch(`${API_BASE_URL}/clock/reload/${msgId}`, { method: "POST" });
    const ok = res.ok;
    const data = await res.json().catch(() => ({}));
    if (!ok) throw new Error(data?.detail || `HTTP ${res.status}`);
    setStatus(statusEl, `OK: перезагружено, +${data.updates_count}`, "ok");
    await getLatest();
  } catch (e) {
    setStatus(statusEl, `Ошибка: ${e.message || e}`, "err");
  }
}

async function triggerFetchPeriod() {
  const statusEl = qs("periodStatus");
  const daysStr = (qs("periodDays").value || "").trim();
  let days = Number(daysStr);
  if (!Number.isFinite(days) || days < 0) {
    setStatus(statusEl, "Некорректное число дней", "warn");
    return;
  }
  if (daysStr === "") days = 30;
  setStatus(statusEl, `Загрузка за период (дней=${days})...`, "warn");
  const spinner = document.createElement("span");
  spinner.className = "spinner";
  statusEl.appendChild(spinner);
  try {
    const url = new URL(`${API_BASE_URL}/clock/fetch-period`, location.origin);
    url.searchParams.set("days", String(days));
    const res = await fetch(url.pathname + url.search, { method: "POST" });
    const ok = res.ok;
    const data = await res.json().catch(() => ({}));
    if (!ok) throw new Error(data?.detail || `HTTP ${res.status}`);
    setStatus(statusEl, `OK: ${data.updates_count} новых`, "ok");
    await getLatest();
  } catch (e) {
    setStatus(statusEl, `Ошибка: ${e.message || e}`, "err");
  }
}

async function triggerReset() {
  const statusEl = qs("resetStatus");
  if (!confirm("Вы уверены, что хотите удалить все сообщения из базы?")) {
    setStatus(statusEl, "Отменено", "warn");
    return;
  }
  setStatus(statusEl, "Очистка базы...", "warn");
  const spinner = document.createElement("span");
  spinner.className = "spinner";
  statusEl.appendChild(spinner);
  try {
    const res = await fetch(`${API_BASE_URL}/clock/reset`, { method: "POST" });
    const ok = res.ok;
    const data = await res.json().catch(() => ({}));
    if (!ok) throw new Error(data?.detail || `HTTP ${res.status}`);
    setStatus(statusEl, `OK: удалено ${data.deleted}`, "ok");
    await getLatest();
  } catch (e) {
    setStatus(statusEl, `Ошибка: ${e.message || e}`, "err");
  }
}

async function loadHistory() {
  const statusEl = qs("historyStatus");
  const listEl = qs("historyList");
  let limit = Number((qs("historyLimit").value || "20").trim());
  if (!Number.isFinite(limit) || limit <= 0) limit = 20;
  setStatus(statusEl, `Загрузка (${limit})...`, "warn");
  listEl.innerHTML = "";
  try {
    const url = new URL(`${API_BASE_URL}/clock/history`, location.origin);
    url.searchParams.set("limit", String(limit));
    const res = await fetch(url.pathname + url.search, { method: "GET" });
    const ok = res.ok;
    const data = await res.json().catch(() => ({}));
    if (!ok) throw new Error(data?.detail || `HTTP ${res.status}`);
    const items = Array.isArray(data.updates) ? data.updates : [];
    if (!items.length) {
      listEl.innerHTML = '<div class="muted">Нет данных</div>';
      setStatus(statusEl, "Готово", "ok");
      return;
    }
    const frag = document.createDocumentFragment();
    for (const u of items) {
      const details = document.createElement("details");
      details.className = "entry";
      const summary = document.createElement("summary");
      const imgTag = u.image_data ? "📷" : "";
      summary.innerHTML = `<span class="mono">#${u.message_id}</span> • ${u.time ?? "—"} • <span class="muted">${u.created_at}</span> ${imgTag}`;
      const body = document.createElement("div");
      body.className = "entry-content";
      body.textContent = u.content ?? "";
      details.appendChild(summary);
      details.appendChild(body);
      frag.appendChild(details);
    }
    listEl.appendChild(frag);
    setStatus(statusEl, `Готово (${items.length})`, "ok");
  } catch (e) {
    setStatus(statusEl, `Ошибка: ${e.message || e}`, "err");
  }
}

window.AdminPage = {
  init() {
    qs("btnFetch").addEventListener("click", triggerFetch);
    qs("btnReload").addEventListener("click", triggerReload);
    qs("btnFetchPeriod").addEventListener("click", triggerFetchPeriod);
    qs("btnReset").addEventListener("click", triggerReset);
    qs("btnLoadHistory").addEventListener("click", loadHistory);
    getLatest();
    loadHistory();
  },
};
