const tg = window.Telegram?.WebApp;
const initData = tg?.initData || "";
const initialMode = new URLSearchParams(window.location.search).get("mode") === "admin" ? "admin" : "booking";

const state = {
  services: [],
  groups: [],
  adminSlots: [],
  selectedServices: new Set(),
  selectedAdminTimes: new Set(),
  adminCalendarMonth: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
  adminSelectedDate: "",
  groupId: "",
  slotId: 0,
  isAdmin: false,
};

const DEFAULT_TIMES = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00"];
const MONTHS = ["Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень", "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"];

const $ = (selector) => document.querySelector(selector);

function request(path, options = {}) {
  return fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Telegram-Init-Data": initData,
      ...(options.headers || {}),
    },
  });
}

function formatDate(value) {
  const [year, month, day] = value.split("-");
  return `${day}.${month}.${year}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setStatus(text) {
  $("#status").textContent = text;
}

function setAdminStatus(text) {
  $("#adminStatus").textContent = text;
}

function setMode(mode) {
  const isAdminMode = mode === "admin";
  $("#bookingView").classList.toggle("hidden", isAdminMode);
  $("#adminView").classList.toggle("hidden", !isAdminMode);
  document.querySelectorAll("[data-mode]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.mode === mode);
  });
}

function renderQuickTimes() {
  $("#quickTimes").innerHTML = DEFAULT_TIMES.map(
    (time) => `<button class="quick-time" type="button" data-quick-time="${time}">${time}</button>`
  ).join("");

  document.querySelectorAll("[data-quick-time]").forEach((button) => {
    button.addEventListener("click", () => {
      const time = button.dataset.quickTime;
      if (state.selectedAdminTimes.has(time)) state.selectedAdminTimes.delete(time);
      else state.selectedAdminTimes.add(time);
      button.classList.toggle("is-active", state.selectedAdminTimes.has(time));
      updateAdminSelection();
    });
  });
}

function toLocalIso(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function isoDateFromToday(offset) {
  const date = new Date();
  date.setDate(date.getDate() + offset);
  return toLocalIso(date);
}

function addMonths(date, offset) {
  return new Date(date.getFullYear(), date.getMonth() + offset, 1);
}

function updateAdminSelection() {
  const selectedDate = $("#adminDate")?.value || state.adminSelectedDate;
  const manualTimes = parseTimes($("#adminTimes")?.value || "").length;
  const total = new Set([...state.selectedAdminTimes, ...parseTimes($("#adminTimes")?.value || "")]).size;
  const dateText = selectedDate ? formatDate(selectedDate) : "дата не обрана";
  const timeText = total ? `${total} год.` : "час не обрано";
  $("#adminSelection").textContent = `Обрано: ${dateText} · ${timeText}${manualTimes ? " · є ручний час" : ""}`;
}

function getSelectedAdminGroupId() {
  return $("#adminGroup")?.value || "";
}

function renderAdminCalendar() {
  const calendar = $("#adminCalendar");
  if (!calendar) return;

  const month = state.adminCalendarMonth;
  $("#calendarTitle").textContent = `${MONTHS[month.getMonth()]} ${month.getFullYear()}`;

  const selectedGroupId = getSelectedAdminGroupId();
  const slotCounts = state.adminSlots.reduce((result, slot) => {
    if (selectedGroupId && String(slot.group_id) !== String(selectedGroupId)) return result;
    result[slot.slot_date] = (result[slot.slot_date] || 0) + 1;
    return result;
  }, {});

  const todayIso = isoDateFromToday(0);
  const firstDay = new Date(month.getFullYear(), month.getMonth(), 1);
  const mondayOffset = (firstDay.getDay() + 6) % 7;
  const start = new Date(firstDay);
  start.setDate(firstDay.getDate() - mondayOffset);

  calendar.innerHTML = Array.from({ length: 42 }, (_, index) => {
    const date = new Date(start);
    date.setDate(start.getDate() + index);
    const iso = toLocalIso(date);
    const isOutside = date.getMonth() !== month.getMonth();
    const isPast = iso < todayIso;
    const isToday = iso === todayIso;
    const isActive = iso === state.adminSelectedDate;
    const count = slotCounts[iso] || 0;

    return `
      <button
        class="calendar-day${isOutside ? " is-outside" : ""}${isToday ? " is-today" : ""}${isActive ? " is-active" : ""}"
        type="button"
        data-calendar-date="${iso}"
        ${isPast ? "disabled" : ""}
      >
        <span>${date.getDate()}</span>
        <small>${count ? `${count} вік.` : ""}</small>
      </button>
    `;
  }).join("");

  document.querySelectorAll("[data-calendar-date]").forEach((button) => {
    button.addEventListener("click", () => {
      state.adminSelectedDate = button.dataset.calendarDate;
      $("#adminDate").value = state.adminSelectedDate;
      renderAdminCalendar();
      updateAdminSelection();
    });
  });
  updateAdminSelection();
}

function renderServices() {
  $("#services").innerHTML = state.services
    .map(
      (service) => `
        <button class="card" type="button" data-service="${service.id}">
          <strong>${escapeHtml(service.name)}</strong>
          <span>${escapeHtml(service.price)}</span>
        </button>
      `
    )
    .join("");

  document.querySelectorAll("[data-service]").forEach((button) => {
    button.addEventListener("click", () => {
      const id = button.dataset.service;
      if (state.selectedServices.has(id)) state.selectedServices.delete(id);
      else state.selectedServices.add(id);
      button.classList.toggle("is-active", state.selectedServices.has(id));
    });
  });
}

function renderGroups() {
  $("#groups").innerHTML = state.groups
    .map((group) => `<button class="chip" type="button" data-group="${escapeHtml(group.id)}">${escapeHtml(group.name)}</button>`)
    .join("");
  $("#adminGroup").innerHTML = state.groups
    .map((group) => `<option value="${escapeHtml(group.id)}">${escapeHtml(group.name)}</option>`)
    .join("");
  if (!state.adminSelectedDate) {
    state.adminSelectedDate = isoDateFromToday(0);
    $("#adminDate").value = state.adminSelectedDate;
  }

  document.querySelectorAll("[data-group]").forEach((button) => {
    button.addEventListener("click", async () => {
      state.groupId = button.dataset.group;
      state.slotId = 0;
      document.querySelectorAll("[data-group]").forEach((item) => item.classList.remove("is-active"));
      button.classList.add("is-active");
      await loadDates();
    });
  });

  $("#adminGroup").addEventListener("change", () => {
    renderAdminCalendar();
    updateAdminSelection();
  });
}

async function loadDates() {
  $("#dates").innerHTML = "";
  $("#times").innerHTML = "";
  const response = await request(`/api/dates?group_id=${encodeURIComponent(state.groupId)}`);
  const data = await response.json();

  if (!data.dates.length) {
    $("#dates").innerHTML = "<p class='status'>Поки немає вільних дат.</p>";
    return;
  }

  $("#dates").innerHTML = data.dates
    .map((date) => `<button class="chip" type="button" data-date="${date}">${formatDate(date)}</button>`)
    .join("");

  document.querySelectorAll("[data-date]").forEach((button) => {
    button.addEventListener("click", async () => {
      document.querySelectorAll("[data-date]").forEach((item) => item.classList.remove("is-active"));
      button.classList.add("is-active");
      await loadTimes(button.dataset.date);
    });
  });
}

async function loadTimes(date) {
  state.slotId = 0;
  const response = await request(`/api/times?group_id=${encodeURIComponent(state.groupId)}&date=${encodeURIComponent(date)}`);
  const data = await response.json();
  $("#times").innerHTML = data.slots
    .map((slot) => `<button class="chip" type="button" data-slot="${slot.id}">${slot.slot_time}</button>`)
    .join("");

  document.querySelectorAll("[data-slot]").forEach((button) => {
    button.addEventListener("click", () => {
      state.slotId = Number(button.dataset.slot);
      document.querySelectorAll("[data-slot]").forEach((item) => item.classList.remove("is-active"));
      button.classList.add("is-active");
    });
  });
}

async function sendApplication() {
  const serviceIds = [...state.selectedServices];
  const name = $("#clientName").value.trim();
  const contact = $("#clientContact").value.trim();

  if (!serviceIds.length) return setStatus("Оберіть хоча б одну послугу.");
  if (!state.slotId) return setStatus("Оберіть дату і час.");
  if (name.length < 2) return setStatus("Введіть ім'я.");
  if (contact.length < 4) return setStatus("Залиште телефон або Telegram.");

  $("#sendRequest").disabled = true;
  setStatus("Надсилаю заявку...");

  const response = await request("/api/applications", {
    method: "POST",
    body: JSON.stringify({
      service_ids: serviceIds,
      slot_id: state.slotId,
      name,
      contact,
    }),
  });

  if (!response.ok) {
    $("#sendRequest").disabled = false;
    return setStatus("Не вдалося надіслати. Оновіть Mini App і спробуйте ще раз.");
  }

  setStatus("Заявку надіслано. Майстер підтвердить запис.");
  tg?.HapticFeedback?.notificationOccurred("success");
  setTimeout(() => tg?.close(), 900);
}

function parseTimes(value) {
  return [...new Set((value.match(/\b([01]?\d|2[0-3])[:.]\d{2}\b/g) || []).map((item) => item.replace(".", ":")))];
}

async function loadAdminSlots() {
  const response = await request("/api/admin/slots");
  if (!response.ok) return;
  const data = await response.json();
  const freeSlots = data.slots.filter((slot) => slot.status === "free");
  state.adminSlots = freeSlots;
  $("#statFree").textContent = freeSlots.length;
  renderAdminCalendar();

  if (!freeSlots.length) {
    $("#adminSlots").innerHTML = "<p class='status'>Вільних вікон поки немає.</p>";
    return;
  }

  const slotsByDate = freeSlots.reduce((result, slot) => {
    const key = `${slot.slot_date}|${slot.group_name}`;
    result[key] = result[key] || [];
    result[key].push(slot);
    return result;
  }, {});

  $("#adminSlots").innerHTML = Object.entries(slotsByDate)
    .map(([key, slots]) => {
      const [date, groupName] = key.split("|");
      return `
        <section class="day-card">
          <div class="day-card-head">
            <strong>${formatDate(date)}</strong>
            <span>${escapeHtml(groupName)}</span>
          </div>
          <div class="slot-pills">
            ${slots
              .map(
                (slot) => `
                  <span class="slot-pill">
                    ${escapeHtml(slot.slot_time)}
                    <button type="button" aria-label="Видалити ${escapeHtml(slot.slot_time)}" data-delete-slot="${slot.id}">×</button>
                  </span>
                `
              )
              .join("")}
          </div>
        </section>
      `;
    })
    .join("");

  document.querySelectorAll("[data-delete-slot]").forEach((button) => {
    button.addEventListener("click", async () => {
      setAdminStatus("Видаляю вікно...");
      await request(`/api/admin/slots/${button.dataset.deleteSlot}`, { method: "DELETE" });
      await loadAdminSlots();
      setAdminStatus("Вікно видалено.");
    });
  });
}

function statusLabel(status) {
  const labels = {
    new: "Очікує",
    confirmed: "Підтверджено",
    cancelled: "Скасовано",
  };
  return labels[status] || status;
}

async function loadAdminApplications() {
  const response = await request("/api/admin/applications");
  if (!response.ok) return;
  const data = await response.json();

  if (!data.applications.length) {
    $("#adminApplications").innerHTML = "<p class='status'>Заявок поки немає.</p>";
    $("#statNew").textContent = "0";
    return;
  }

  $("#statNew").textContent = data.applications.filter((item) => item.status === "new").length;

  $("#adminApplications").innerHTML = data.applications
    .map((item) => {
      const actions =
        item.status === "new"
          ? `
            <div class="item-actions">
              <button type="button" data-application-action="confirmed" data-application-id="${item.id}">Підтвердити</button>
              <button type="button" data-application-action="cancelled" data-application-id="${item.id}">Скасувати</button>
            </div>
          `
          : "";

      return `
        <div class="application-item">
          <div>
            <strong>#${item.id} · ${escapeHtml(item.client_name)} · ${statusLabel(item.status)}</strong>
            <div class="application-meta">
              <span>${formatDate(item.desired_date)}</span>
              <span>${escapeHtml(item.desired_time)}</span>
              <span>${escapeHtml(item.schedule_group || "")}</span>
            </div>
            <p>${escapeHtml(item.service)}</p>
            <p>${escapeHtml(item.contact)}</p>
          </div>
          ${actions}
        </div>
      `;
    })
    .join("");

  document.querySelectorAll("[data-application-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      setAdminStatus("Оновлюю заявку...");
      await request(`/api/admin/applications/${button.dataset.applicationId}`, {
        method: "PATCH",
        body: JSON.stringify({ status: button.dataset.applicationAction }),
      });
      await loadAdminApplications();
      await loadAdminSlots();
      if (state.groupId) await loadDates();
      setAdminStatus("Готово.");
    });
  });
}

async function addAdminSlots() {
  const groupId = $("#adminGroup").value;
  const slotDate = $("#adminDate").value;
  const times = [...new Set([...state.selectedAdminTimes, ...parseTimes($("#adminTimes").value)])].sort();
  if (!groupId) return setAdminStatus("Оберіть графік.");
  if (!slotDate) return setAdminStatus("Оберіть дату.");
  if (!times.length) return setAdminStatus("Оберіть або введіть час.");

  $("#addSlots").disabled = true;
  setAdminStatus("Додаю вільні вікна...");
  try {
    const response = await request("/api/admin/slots", {
      method: "POST",
      body: JSON.stringify({ group_id: groupId, slot_date: slotDate, times }),
    });
    if (!response.ok) return setAdminStatus("Не вдалося додати вікна.");

    $("#adminTimes").value = "";
    state.selectedAdminTimes.clear();
    document.querySelectorAll("[data-quick-time]").forEach((button) => button.classList.remove("is-active"));
    updateAdminSelection();
    await loadAdminSlots();
    await loadAdminApplications();
    if (state.groupId) await loadDates();
    setAdminStatus(`Додано: ${times.join(", ")}.`);
  } finally {
    $("#addSlots").disabled = false;
  }
}

async function refreshAdmin() {
  if (!state.isAdmin) return;
  setAdminStatus("Оновлюю дані...");
  await loadAdminApplications();
  await loadAdminSlots();
  setAdminStatus("Дані оновлено.");
}

async function init() {
  tg?.ready();
  tg?.expand();

  const response = await request("/api/bootstrap");
  const data = await response.json();
  state.services = data.services;
  state.groups = data.groups;
  state.isAdmin = Boolean(data.is_admin);

  renderServices();
  renderGroups();
  renderQuickTimes();
  renderAdminCalendar();

  if (data.is_admin) {
    $("#modeSwitch").classList.remove("hidden");
    await refreshAdmin();
    setMode(initialMode);
  }
}

$("#sendRequest").addEventListener("click", sendApplication);
$("#addSlots").addEventListener("click", addAdminSlots);
$("#refreshAdmin").addEventListener("click", refreshAdmin);
$("#adminTimes").addEventListener("input", updateAdminSelection);
$("#calendarPrev").addEventListener("click", () => {
  state.adminCalendarMonth = addMonths(state.adminCalendarMonth, -1);
  renderAdminCalendar();
});
$("#calendarNext").addEventListener("click", () => {
  state.adminCalendarMonth = addMonths(state.adminCalendarMonth, 1);
  renderAdminCalendar();
});
document.querySelectorAll("[data-mode]").forEach((button) => {
  button.addEventListener("click", () => setMode(button.dataset.mode));
});
init().catch(() => setStatus("Не вдалося завантажити Mini App."));
