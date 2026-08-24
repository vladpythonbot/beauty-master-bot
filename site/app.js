const categoryLabels = {
  all: "Все",
  lashes: "Ресницы",
  brows: "Брови",
  nails: "Ногти",
  makeup: "Макияж",
};

const imageThemes = {
  lashes: ["#f8d8df", "#c7b8ff", "Ресницы"],
  "lashes-soft": ["#f6edf7", "#d9c8ff", "Ламинирование"],
  "lashes-light": ["#fff4f0", "#e9c6d4", "Натуральный эффект"],
  brows: ["#f4e5d8", "#b89077", "Брови"],
  "brows-soft": ["#f7efe8", "#d4b09a", "Форма"],
  nails: ["#f8dbe7", "#b66586", "Маникюр"],
  "nails-soft": ["#fff0f5", "#dca0ba", "Покрытие"],
  makeup: ["#ede3ff", "#9b6a88", "Макияж"],
  "makeup-soft": ["#f4ecff", "#b98da5", "Образ"],
  skin: ["#e9f1ee", "#9bb6a8", "Уход"],
};

const $ = (selector) => document.querySelector(selector);

function demoVisual(type, label = "") {
  const [start, end, text] = imageThemes[type] || imageThemes.makeup;
  return `
    <div class="demo-visual" style="--visual-start:${start};--visual-end:${end}">
      <span class="demo-orbit"></span>
      <span class="demo-line demo-line-a"></span>
      <span class="demo-line demo-line-b"></span>
      <span class="demo-label">${label || text}</span>
    </div>
  `;
}

function renderServices() {
  const container = $("#servicesGrid");
  container.innerHTML = services
    .map(
      (service) => `
        <article class="service-card reveal">
          ${demoVisual(service.image, service.title)}
          <div class="card-body">
            <h3>${service.title}</h3>
            <p>${service.description}</p>
            <div class="service-meta">
              <span>${service.duration}</span>
              <strong>${service.price}</strong>
            </div>
            <a class="button button-small" href="${siteConfig.telegramBotUrl}" target="_blank" rel="noreferrer">Записаться</a>
          </div>
        </article>
      `
    )
    .join("");
}

function renderMasters() {
  const container = $("#mastersGrid");
  container.innerHTML = masters
    .map(
      (master, index) => `
        <article class="master-card reveal">
          <div class="master-photo">М${index + 1}</div>
          <h3>${master.name}</h3>
          <strong>${master.specialization}</strong>
          <p>${master.note}</p>
          <a class="button button-secondary button-small" href="${siteConfig.telegramBotUrl}" target="_blank" rel="noreferrer">Записаться к мастеру</a>
        </article>
      `
    )
    .join("");
}

function renderPortfolio(filter = "all") {
  const container = $("#portfolioGrid");
  const visibleItems = filter === "all" ? portfolioItems : portfolioItems.filter((item) => item.category === filter);
  container.innerHTML = visibleItems
    .map(
      (item) => `
        <article class="portfolio-card reveal">
          ${demoVisual(item.image, item.title)}
          <div class="portfolio-caption">
            <span>${categoryLabels[item.category]}</span>
            <strong>${item.title}</strong>
          </div>
        </article>
      `
    )
    .join("");
}

function renderReviews() {
  const container = $("#reviewsGrid");
  container.innerHTML = reviewPlaceholders
    .map(
      (review) => `
        <article class="review-card reveal">
          <span>${review.title}</span>
          <p>${review.text}</p>
        </article>
      `
    )
    .join("");
}

function applyConfig() {
  document.documentElement.style.setProperty("--accent", siteConfig.accentColor);
  document.title = `${siteConfig.studioName} — сайт-визитка студии красоты`;
  document.querySelector('meta[name="description"]').setAttribute(
    "content",
    `${siteConfig.studioName}: демонстрационный сайт-визитка для студии красоты в городе ${siteConfig.city}.`
  );

  document.querySelectorAll("[data-studio-name]").forEach((node) => {
    node.textContent = siteConfig.studioName;
  });
  document.querySelectorAll("[data-city]").forEach((node) => {
    node.textContent = siteConfig.city;
  });
  document.querySelectorAll("[data-telegram-link]").forEach((node) => {
    node.setAttribute("href", siteConfig.telegramBotUrl);
  });
  document.querySelectorAll("[data-instagram-link]").forEach((node) => {
    node.setAttribute("href", siteConfig.instagramUrl);
  });
  document.querySelectorAll("[data-telegram-contact]").forEach((node) => {
    node.setAttribute("href", siteConfig.telegramUrl);
  });
  $("#contactPhone").textContent = siteConfig.phone;
  $("#contactPhone").setAttribute("href", `tel:${siteConfig.phone.replaceAll(" ", "")}`);
  $("#callButton").setAttribute("href", `tel:${siteConfig.phone.replaceAll(" ", "")}`);
  $("#contactAddress").textContent = siteConfig.address;
  $("#contactHours").textContent = siteConfig.workingHours;
  $("#heroTagline").textContent = siteConfig.tagline;
  $("#heroDescription").textContent = siteConfig.description;
}

function setupMenu() {
  const menuButton = $("#menuButton");
  const nav = $("#siteNav");
  menuButton.addEventListener("click", () => {
    const isOpen = nav.classList.toggle("is-open");
    menuButton.setAttribute("aria-expanded", String(isOpen));
  });

  nav.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      nav.classList.remove("is-open");
      menuButton.setAttribute("aria-expanded", "false");
    });
  });
}

function setupFilters() {
  document.querySelectorAll(".filter-button").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".filter-button").forEach((item) => item.classList.remove("is-active"));
      button.classList.add("is-active");
      renderPortfolio(button.dataset.filter);
    });
  });
}

function setupReveal() {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) entry.target.classList.add("is-visible");
      });
    },
    { threshold: 0.12 }
  );

  document.querySelectorAll(".reveal").forEach((item) => observer.observe(item));
}

applyConfig();
renderServices();
renderMasters();
renderPortfolio();
renderReviews();
setupMenu();
setupFilters();
setupReveal();
