const tg = window.Telegram?.WebApp;
const initData = tg?.initData || "";
const initialMode = new URLSearchParams(window.location.search).get("mode") === "admin" ? "admin" : "booking";

const state = {
  services: [],
  groups: [],
  adminSlots: [],
  selectedServices: new Set(),
  selectedAdminTimes: new Set(),
  selectedWeekdays: new Set([0, 1, 2, 3, 4]),
  selectedAdminDates: new Set(),
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

function setAdminSection(section) {
  document.querySelectorAll("[data-admin-section]").forEach((item) => {
    item.classList.toggle("hidden", item.dataset.adminSection !== section);
  });
  document.querySelectorAll("[data-admin-tab]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.adminTab === section);
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

function addDaysIso(days) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return toLocalIso(date);
}

function updateAdminSelection() {
  const selectedDate = $("#adminDate")?.value || state.adminSelectedDate;
  const manualTimes = parseTimes($("#adminTimes")?.value || "").length;
  const total = new Set([...state.selectedAdminTimes, ...parseTimes($("#adminTimes")?.value || "")]).size;
  const selectedDates = [...state.selectedAdminDates].sort();
  const dateText = selectedDates.length
    ? `${selectedDates.length} дн. · ${selectedDates.map((date) => formatDate(date).slice(0, 5)).join(", ")}`
    : selectedDate
      ? formatDate(selectedDate)
      : "дата не обрана";
  const timeText = total ? `${total} год.` : "час не обрано";
  const period = $("#schedulePeriod")?.value || "30";
  const start = $("#workStart")?.value || "09:00";
  const end = $("#workEnd")?.value || "19:00";
  const step = $("#slotStep")?.value || "60";
  const days = state.selectedWeekdays.size;
  $("#adminSelection").textContent =
    `Буде створено: ${period} дн. · ${days} роб. дн.\n` +
    `Час: ${start}-${end} · крок ${step} хв\n` +
    `Разово вибрано: ${dateText} · ${timeText}${manualTimes ? " · є ручний час" : ""}`;
}

function renderWeekdays() {
  document.querySelectorAll("[data-weekday]").forEach((button) => {
    const weekday = Number(button.dataset.weekday);
    button.classList.toggle("is-active", state.selectedWeekdays.has(weekday));
    button.onclick = () => {
      if (state.selectedWeekdays.has(weekday)) state.selectedWeekdays.delete(weekday);
      else state.selectedWeekdays.add(weekday);
      button.classList.toggle("is-active", state.selectedWeekdays.has(weekday));
      updateAdminSelection();
    };
  });
}

function getSelectedAdminGroupId() {
  return $("#adminGroup")?.value || "";
}

function getServiceById(serviceId) {
  return state.services.find((service) => String(service.id) === String(serviceId));
}

function getSelectedGroup() {
  return state.groups.find((group) => String(group.id) === String(state.groupId));
}

function getClientServices() {
  const group = getSelectedGroup();
  if (!group) return state.services;
  return state.services.filter((service) => (group.service_ids || []).includes(service.id));
}

function syncSelectedServicesWithGroup() {
  const availableIds = new Set(getClientServices().map((service) => service.id));
  [...state.selectedServices].forEach((serviceId) => {
    if (!availableIds.has(serviceId)) state.selectedServices.delete(serviceId);
  });
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
    const isActive = state.selectedAdminDates.has(iso);
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
      const date = button.dataset.calendarDate;
      if (state.selectedAdminDates.has(date)) state.selectedAdminDates.delete(date);
      else state.selectedAdminDates.add(date);
      state.adminSelectedDate = date;
      $("#adminDate").value = state.adminSelectedDate;
      renderAdminCalendar();
      updateAdminSelection();
    });
  });
  updateAdminSelection();
}

function renderServices() {
  const services = getClientServices();
  syncSelectedServicesWithGroup();

  $("#services").innerHTML = services
    .map(
      (service) => `
        <button class="card${state.selectedServices.has(service.id) ? " is-active" : ""}" type="button" data-service="${service.id}">
          <strong>${escapeHtml(service.name)}</strong>
          <span>${escapeHtml(service.duration || "")} · ${escapeHtml(service.price)}</span>
          <small>${escapeHtml(service.description || "")}</small>
        </button>
      `
    )
    .join("");

  if (!services.length) {
    $("#services").innerHTML = "<p class='status'>У цього майстра поки немає прив'язаних послуг.</p>";
    return;
  }

  document.querySelectorAll("[data-service]").forEach((button) => {
    button.addEventListener("click", () => {
      const id = button.dataset.service;
      if (state.selectedServices.has(id)) state.selectedServices.delete(id);
      else state.selectedServices.add(id);
      button.classList.toggle("is-active", state.selectedServices.has(id));
      renderClientGroups();
    });
  });
}

function getClientGroups() {
  const selectedServices = [...state.selectedServices].map(getServiceById).filter(Boolean);
  if (!selectedServices.length) return state.groups;

  return state.groups.filter((group) =>
    selectedServices.every((service) => (group.service_ids || []).includes(service.id))
  );
}

function renderClientGroups() {
  const groups = getClientGroups();
  $("#groups").innerHTML = groups
    .map((group) => `<button class="chip" type="button" data-group="${escapeHtml(group.id)}">${escapeHtml(group.name)}</button>`)
    .join("");

  if (!groups.length) {
    $("#groups").innerHTML = "<p class='status'>Для цієї комбінації послуг немає спільного майстра. Оберіть одну процедуру або іншу комбінацію.</p>";
    state.groupId = "";
    $("#dates").innerHTML = "";
    $("#times").innerHTML = "";
    return;
  }

  if (state.groupId && !groups.some((group) => String(group.id) === String(state.groupId))) {
    state.groupId = "";
    $("#dates").innerHTML = "";
    $("#times").innerHTML = "";
    renderServices();
  }

  document.querySelectorAll("[data-group]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.group === state.groupId);
    button.addEventListener("click", async () => {
      state.groupId = button.dataset.group;
      state.slotId = 0;
      document.querySelectorAll("[data-group]").forEach((item) => item.classList.remove("is-active"));
      button.classList.add("is-active");
      renderServices();
      await loadDates();
    });
  });
}

function renderGroups() {
  renderClientGroups();
  $("#statMasters").textContent = state.groups.length;
  const currentAdminGroup = $("#adminGroup")?.value || state.groups[0]?.id || "";
  $("#adminGroup").innerHTML = state.groups
    .map((group) => `<option value="${escapeHtml(group.id)}">${escapeHtml(group.name)}</option>`)
    .join("");
  if (currentAdminGroup && state.groups.some((group) => String(group.id) === String(currentAdminGroup))) {
    $("#adminGroup").value = currentAdminGroup;
  }
  if (!state.adminSelectedDate) {
    state.adminSelectedDate = isoDateFromToday(0);
    $("#adminDate").value = state.adminSelectedDate;
  }

  $("#adminGroup").onchange = () => {
    renderAdminCalendar();
    renderAdminSlots();
    updateAdminSelection();
  };
  renderAdminGroups();
}

function renderAdminGroups() {
  const list = $("#adminGroups");
  if (!list) return;

  if (!state.groups.length) {
    list.innerHTML = "<p class='status'>Додайте хоча б один графік.</p>";
    return;
  }

  list.innerHTML = state.groups
    .map(
      (group) => `
        <div class="group-admin-item">
          <div class="group-admin-fields">
            <input type="text" value="${escapeHtml(group.name)}" data-group-name="${escapeHtml(group.id)}" />
            <div class="group-service-list">
              ${state.services
                .map(
                  (service) => `
                    <label>
                      <input
                        type="checkbox"
                        data-group-service="${escapeHtml(group.id)}"
                        value="${escapeHtml(service.id)}"
                        ${(group.service_ids || []).includes(service.id) ? "checked" : ""}
                      />
                      <span>${escapeHtml(service.name)}</span>
                    </label>
                  `
                )
                .join("")}
            </div>
          </div>
          <div class="group-admin-actions">
            <button type="button" data-rename-group="${escapeHtml(group.id)}">Зберегти</button>
            <button type="button" data-delete-group="${escapeHtml(group.id)}">Видалити</button>
          </div>
        </div>
      `
    )
    .join("");

  document.querySelectorAll("[data-rename-group]").forEach((button) => {
    button.addEventListener("click", () => renameGroup(button.dataset.renameGroup));
  });
  document.querySelectorAll("[data-delete-group]").forEach((button) => {
    button.addEventListener("click", () => deleteGroup(button.dataset.deleteGroup));
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
  renderAdminCalendar();
  renderAdminSlots();
}

function renderAdminSlots() {
  const visibleSlots = state.adminSlots;
  $("#statFree").textContent = visibleSlots.length;
  $("#statToday").textContent = visibleSlots.filter((slot) => slot.slot_date === isoDateFromToday(0)).length;

  if (!visibleSlots.length) {
    $("#adminSlots").innerHTML = "<p class='status'>Вільних вікон поки немає.</p>";
    return;
  }

  const slotsByGroup = visibleSlots.reduce((result, slot) => {
    const groupKey = `${slot.group_id}|${slot.group_name}`;
    result[groupKey] = result[groupKey] || {};
    result[groupKey][slot.slot_date] = result[groupKey][slot.slot_date] || [];
    result[groupKey][slot.slot_date].push(slot);
    return result;
  }, {});

  $("#adminSlots").innerHTML = Object.entries(slotsByGroup)
    .map(([key, dates]) => {
      const [, groupName] = key.split("|");
      const total = Object.values(dates).reduce((sum, slots) => sum + slots.length, 0);
      return `
        <details class="master-slots" open>
          <summary>
            <strong>${escapeHtml(groupName)}</strong>
            <span>${total} вік.</span>
          </summary>
          ${Object.entries(dates)
            .sort(([dateA], [dateB]) => dateA.localeCompare(dateB))
            .map(
              ([date, slots]) => `
                <section class="day-card compact-day-card">
                  <div class="day-card-head">
                    <strong>${formatDate(date)}</strong>
                    <span>${slots.length} вік.</span>
                  </div>
                  <div class="slot-pills">
                    ${slots
                      .sort((a, b) => a.slot_time.localeCompare(b.slot_time))
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
              `
            )
            .join("")}
        </details>
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
            <strong>${escapeHtml(item.client_name)} · ${statusLabel(item.status)}</strong>
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

async function reloadGroups() {
  const response = await request("/api/bootstrap");
  if (!response.ok) return false;
  const data = await response.json();
  state.groups = data.groups;
  renderGroups();
  renderAdminCalendar();
  if (state.groupId && !state.groups.some((group) => String(group.id) === String(state.groupId))) {
    state.groupId = "";
    $("#dates").innerHTML = "";
    $("#times").innerHTML = "";
  }
  return true;
}

async function addGroup() {
  const input = $("#groupName");
  const name = input.value.trim();
  if (name.length < 2) return setAdminStatus("Введіть назву графіка.");

  $("#addGroup").disabled = true;
  setAdminStatus("Додаю графік...");
  try {
    const response = await request("/api/admin/groups", {
      method: "POST",
      body: JSON.stringify({ name, service_ids: state.services.map((service) => service.id) }),
    });
    if (!response.ok) return setAdminStatus("Не вдалося додати графік.");
    input.value = "";
    await reloadGroups();
    await loadAdminSlots();
    setAdminStatus("Графік додано.");
  } finally {
    $("#addGroup").disabled = false;
  }
}

async function renameGroup(groupId) {
  const input = [...document.querySelectorAll("[data-group-name]")].find((item) => item.dataset.groupName === groupId);
  const cleanName = input?.value.trim() || "";
  const serviceIds = [...document.querySelectorAll(`[data-group-service="${groupId}"]:checked`)].map((item) => item.value);
  if (cleanName.length < 2) return setAdminStatus("Назва занадто коротка.");
  if (!serviceIds.length) return setAdminStatus("Оберіть хоча б одну послугу для майстра.");

  setAdminStatus("Оновлюю графік...");
  const response = await request(`/api/admin/groups/${encodeURIComponent(groupId)}`, {
    method: "PATCH",
    body: JSON.stringify({ name: cleanName, service_ids: serviceIds }),
  });
  if (!response.ok) return setAdminStatus("Не вдалося змінити графік.");
  await reloadGroups();
  await loadAdminSlots();
  setAdminStatus("Графік оновлено.");
}

async function deleteGroup(groupId) {
  const group = state.groups.find((item) => String(item.id) === String(groupId));
  if (!group) return;

  setAdminStatus("Видаляю графік...");
  const response = await request(`/api/admin/groups/${encodeURIComponent(groupId)}`, { method: "DELETE" });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    return setAdminStatus(data.message || "Не вдалося видалити графік.");
  }
  await reloadGroups();
  await loadAdminSlots();
  setAdminStatus("Графік видалено.");
}

async function addAdminSlots() {
  const groupId = $("#adminGroup").value;
  const slotDates = [...state.selectedAdminDates].sort();
  const slotDate = $("#adminDate").value;
  if (!slotDates.length && slotDate) slotDates.push(slotDate);
  const times = [...new Set([...state.selectedAdminTimes, ...parseTimes($("#adminTimes").value)])].sort();
  if (!groupId) return setAdminStatus("Оберіть графік.");
  if (!slotDates.length) return setAdminStatus("Оберіть одну або кілька дат.");
  if (!times.length) return setAdminStatus("Оберіть або введіть час.");

  $("#addSlots").disabled = true;
  setAdminStatus("Додаю вільні вікна...");
  try {
    const response = await request("/api/admin/slots", {
      method: "POST",
      body: JSON.stringify({ group_id: groupId, slot_dates: slotDates, times }),
    });
    if (!response.ok) return setAdminStatus("Не вдалося додати вікна.");

    $("#adminTimes").value = "";
    state.selectedAdminTimes.clear();
    state.selectedAdminDates.clear();
    document.querySelectorAll("[data-quick-time]").forEach((button) => button.classList.remove("is-active"));
    updateAdminSelection();
    await loadAdminSlots();
    await loadAdminApplications();
    if (state.groupId) await loadDates();
    setAdminStatus(`Додано вікон: ${slotDates.length} дн. × ${times.length} год.`);
  } finally {
    $("#addSlots").disabled = false;
  }
}

async function generateSlots() {
  const groupId = $("#adminGroup").value;
  const period = Number($("#schedulePeriod").value || 30);
  const startTime = $("#workStart").value;
  const endTime = $("#workEnd").value;
  const stepMinutes = Number($("#slotStep").value || 60);
  const weekdays = [...state.selectedWeekdays].sort((a, b) => a - b);

  if (!groupId) return setAdminStatus("Оберіть графік.");
  if (!weekdays.length) return setAdminStatus("Оберіть хоча б один робочий день.");
  if (!startTime || !endTime || startTime >= endTime) return setAdminStatus("Перевірте початок і кінець дня.");

  $("#generateSlots").disabled = true;
  setAdminStatus("Створюю графік...");
  try {
    const response = await request("/api/admin/slots/bulk", {
      method: "POST",
      body: JSON.stringify({
        group_id: groupId,
        start_date: addDaysIso(0),
        end_date: addDaysIso(period - 1),
        weekdays,
        start_time: startTime,
        end_time: endTime,
        step_minutes: stepMinutes,
      }),
    });
    if (!response.ok) return setAdminStatus("Не вдалося створити графік.");

    const data = await response.json();
    await loadAdminSlots();
    await loadAdminApplications();
    if (state.groupId) await loadDates();
    setAdminStatus(`Графік створено. Нових вікон: ${data.created}.`);
  } finally {
    $("#generateSlots").disabled = false;
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
  renderWeekdays();
  renderAdminCalendar();

  $("#modeSwitch").classList.toggle("hidden", !state.isAdmin);
  if (state.isAdmin) {
    $("#modeSwitch").classList.remove("hidden");
    await refreshAdmin();
    setMode(initialMode);
  } else {
    setMode("booking");
  }
}

$("#sendRequest").addEventListener("click", sendApplication);
$("#addGroup").addEventListener("click", addGroup);
$("#addSlots").addEventListener("click", addAdminSlots);
$("#generateSlots").addEventListener("click", generateSlots);
$("#refreshAdmin").addEventListener("click", refreshAdmin);
$("#adminTimes").addEventListener("input", updateAdminSelection);
$("#clearDates").addEventListener("click", () => {
  state.selectedAdminDates.clear();
  renderAdminCalendar();
  updateAdminSelection();
});
["schedulePeriod", "workStart", "workEnd", "slotStep"].forEach((id) => {
  $(`#${id}`).addEventListener("change", updateAdminSelection);
});
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
document.querySelectorAll("[data-admin-tab]").forEach((button) => {
  button.addEventListener("click", () => setAdminSection(button.dataset.adminTab));
});
init().catch(() => setStatus("Не вдалося завантажити Mini App."));
