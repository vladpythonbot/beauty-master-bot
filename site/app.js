const LANGUAGE_STORAGE_KEY = "beauty-studio-language";
const $ = (selector) => document.querySelector(selector);

let currentLanguage = localStorage.getItem(LANGUAGE_STORAGE_KEY) || siteConfig.defaultLanguage || "ru";
let currentPortfolioFilter = "all";

const imageThemes = {
  lashes: ["#f8d8df", "#c7b8ff"],
  "lashes-soft": ["#f6edf7", "#d9c8ff"],
  "lashes-light": ["#fff4f0", "#e9c6d4"],
  brows: ["#f4e5d8", "#b89077"],
  "brows-soft": ["#f7efe8", "#d4b09a"],
  nails: ["#f8dbe7", "#b66586"],
  "nails-soft": ["#fff0f5", "#dca0ba"],
  makeup: ["#ede3ff", "#9b6a88"],
  "makeup-soft": ["#f4ecff", "#b98da5"],
  skin: ["#e9f1ee", "#9bb6a8"],
};

function t(path) {
  return path.split(".").reduce((value, key) => value?.[key], translations[currentLanguage]) || path;
}

function localize(value) {
  if (!value || typeof value !== "object") return value;
  return value[currentLanguage] || value.ru || Object.values(value)[0];
}

function demoVisual(type, label = "") {
  const [start, end] = imageThemes[type] || imageThemes.makeup;
  return `
    <div class="demo-visual" style="--visual-start:${start};--visual-end:${end}">
      <span class="demo-orbit"></span>
      <span class="demo-line demo-line-a"></span>
      <span class="demo-line demo-line-b"></span>
      <span class="demo-label">${label}</span>
    </div>
  `;
}

function renderServices() {
  $("#servicesGrid").innerHTML = services
    .map((service) => {
      const title = localize(service.title);
      return `
        <article class="service-card reveal">
          ${demoVisual(service.image, title)}
          <div class="card-body">
            <h3>${title}</h3>
            <p>${localize(service.description)}</p>
            <div class="service-meta">
              <span>${localize(service.duration)}</span>
              <strong>${localize(service.price)}</strong>
            </div>
            <a class="button button-small" href="${siteConfig.telegramBotUrl}" target="_blank" rel="noreferrer">${t("actions.book")}</a>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderMasters() {
  $("#mastersGrid").innerHTML = masters
    .map(
      (master, index) => `
        <article class="master-card reveal">
          <div class="master-photo">${t("masters.initials")}${index + 1}</div>
          <h3>${localize(master.name)}</h3>
          <strong>${localize(master.specialization)}</strong>
          <p>${localize(master.note)}</p>
          <a class="button button-secondary button-small" href="${siteConfig.telegramBotUrl}" target="_blank" rel="noreferrer">${t("actions.bookMaster")}</a>
        </article>
      `
    )
    .join("");
}

function renderPortfolio(filter = currentPortfolioFilter) {
  currentPortfolioFilter = filter;
  const visibleItems = filter === "all" ? portfolioItems : portfolioItems.filter((item) => item.category === filter);

  $("#portfolioGrid").innerHTML = visibleItems
    .map((item) => {
      const title = localize(item.title);
      return `
        <article class="portfolio-card reveal">
          ${demoVisual(item.image, title)}
          <div class="portfolio-caption">
            <span>${t(`portfolio.filters.${item.category}`)}</span>
            <strong>${title}</strong>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderReviews() {
  $("#reviewsGrid").innerHTML = reviewPlaceholders
    .map(
      (review) => `
        <article class="review-card reveal">
          <span>${localize(review.title)}</span>
          <p>${localize(review.text)}</p>
        </article>
      `
    )
    .join("");
}

function applyStaticTexts() {
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-aria]").forEach((node) => {
    node.setAttribute("aria-label", t(node.dataset.i18nAria));
  });
  document.querySelectorAll("[data-i18n-array]").forEach((node) => {
    const values = t(node.dataset.i18nArray);
    node.textContent = Array.isArray(values) ? values[Number(node.dataset.i18nIndex)] : "";
  });
}

function applyConfig() {
  document.documentElement.lang = currentLanguage === "ua" ? "uk" : "ru";
  document.documentElement.style.setProperty("--accent", siteConfig.accentColor);
  document.title = t("meta.title");
  document.querySelector('meta[name="description"]').setAttribute("content", t("meta.description"));

  document.querySelectorAll("[data-studio-name]").forEach((node) => {
    node.textContent = siteConfig.studioName;
  });
  document.querySelectorAll("[data-city]").forEach((node) => {
    node.textContent = localize(siteConfig.city);
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
  $("#contactAddress").textContent = localize(siteConfig.address);
  $("#contactHours").textContent = localize(siteConfig.workingHours);
  $("#heroDescription").textContent = t("hero.description");
  $("#heroEyebrow").innerHTML = `${t("hero.eyebrow")} · <span data-city>${localize(siteConfig.city)}</span>`;
}

function applyLanguageState() {
  document.querySelectorAll("[data-language]").forEach((button) => {
    const isActive = button.dataset.language === currentLanguage;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
  });
}

function renderPage() {
  applyStaticTexts();
  applyConfig();
  applyLanguageState();
  renderServices();
  renderMasters();
  renderPortfolio(currentPortfolioFilter);
  renderReviews();
  setupReveal();
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
      setupReveal();
    });
  });
}

function setupLanguageSwitcher() {
  document.querySelectorAll("[data-language]").forEach((button) => {
    button.addEventListener("click", () => {
      currentLanguage = button.dataset.language;
      localStorage.setItem(LANGUAGE_STORAGE_KEY, currentLanguage);
      renderPage();
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

  document.querySelectorAll(".reveal:not(.is-visible)").forEach((item) => observer.observe(item));
}

setupMenu();
setupFilters();
setupLanguageSwitcher();
renderPage();
