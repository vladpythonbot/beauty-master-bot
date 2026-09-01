const tg = window.Telegram?.WebApp;
const initData = tg?.initData || "";

const state = {
  services: [],
  groups: [],
  selectedServices: new Set(),
  groupId: "",
  slotId: 0,
};

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

function setStatus(text) {
  $("#status").textContent = text;
}

function renderServices() {
  $("#services").innerHTML = state.services
    .map(
      (service) => `
        <button class="card" type="button" data-service="${service.id}">
          <strong>${service.name}</strong>
          <span>${service.price}</span>
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
    .map((group) => `<button class="chip" type="button" data-group="${group.id}">${group.name}</button>`)
    .join("");
  $("#adminGroup").innerHTML = state.groups.map((group) => `<option value="${group.id}">${group.name}</option>`).join("");

  document.querySelectorAll("[data-group]").forEach((button) => {
    button.addEventListener("click", async () => {
      state.groupId = button.dataset.group;
      state.slotId = 0;
      document.querySelectorAll("[data-group]").forEach((item) => item.classList.remove("is-active"));
      button.classList.add("is-active");
      await loadDates();
    });
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
  $("#adminSlots").innerHTML = data.slots
    .filter((slot) => slot.status === "free")
    .map(
      (slot) => `
        <div class="slot-item">
          <span>${slot.group_name} · ${formatDate(slot.slot_date)} · ${slot.slot_time}</span>
          <button type="button" data-delete-slot="${slot.id}">Видалити</button>
        </div>
      `
    )
    .join("");

  document.querySelectorAll("[data-delete-slot]").forEach((button) => {
    button.addEventListener("click", async () => {
      await request(`/api/admin/slots/${button.dataset.deleteSlot}`, { method: "DELETE" });
      await loadAdminSlots();
    });
  });
}

async function addAdminSlots() {
  const groupId = $("#adminGroup").value;
  const slotDate = $("#adminDate").value;
  const times = parseTimes($("#adminTimes").value);
  if (!groupId || !slotDate || !times.length) return;

  await request("/api/admin/slots", {
    method: "POST",
    body: JSON.stringify({ group_id: groupId, slot_date: slotDate, times }),
  });
  $("#adminTimes").value = "";
  await loadAdminSlots();
  if (state.groupId) await loadDates();
}

async function init() {
  tg?.ready();
  tg?.expand();

  const response = await request("/api/bootstrap");
  const data = await response.json();
  state.services = data.services;
  state.groups = data.groups;

  renderServices();
  renderGroups();

  if (data.is_admin) {
    $("#adminPanel").classList.remove("hidden");
    await loadAdminSlots();
  }
}

$("#sendRequest").addEventListener("click", sendApplication);
$("#addSlots").addEventListener("click", addAdminSlots);
init().catch(() => setStatus("Не вдалося завантажити Mini App."));
