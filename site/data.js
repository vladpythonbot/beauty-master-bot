const siteConfig = {
  studioName: "Beauty Studio",
  city: "Харьков",
  tagline: "Ресницы, брови, маникюр, макияж и уход",
  description:
    "Современная студия красоты в Харькове: понятные услуги, аккуратный сервис и заявка на запись через Telegram.",
  telegramBotUrl: "https://t.me/demo_beauty_bot",
  instagramUrl: "https://instagram.com/demo_beauty_studio",
  telegramUrl: "https://t.me/demo_beauty_studio",
  phone: "+380 00 000 00 00",
  address: "Демонстрационный адрес, Харьков",
  workingHours: "Ежедневно с 09:00 до 19:00",
  accentColor: "#9b6a88",
};

const services = [
  {
    id: "lashes",
    title: "Наращивание ресниц",
    description: "Подбор эффекта под форму глаз и желаемый образ.",
    duration: "2–3 часа",
    price: "от 900 грн",
    image: "lashes",
  },
  {
    id: "lash-lamination",
    title: "Ламинирование ресниц",
    description: "Естественный изгиб и ухоженный вид без наращивания.",
    duration: "60–90 мин",
    price: "от 650 грн",
    image: "lashes",
  },
  {
    id: "brows",
    title: "Оформление и окрашивание бровей",
    description: "Форма и оттенок с учётом черт лица.",
    duration: "40–60 мин",
    price: "от 450 грн",
    image: "brows",
  },
  {
    id: "manicure",
    title: "Маникюр",
    description: "Чистая обработка и аккуратное покрытие.",
    duration: "1.5–2 часа",
    price: "от 700 грн",
    image: "nails",
  },
  {
    id: "makeup",
    title: "Макияж",
    description: "Дневной, вечерний или праздничный образ.",
    duration: "60–120 мин",
    price: "от 1000 грн",
    image: "makeup",
  },
  {
    id: "skincare",
    title: "Уход за кожей",
    description: "Деликатные процедуры для свежего вида кожи.",
    duration: "45–90 мин",
    price: "от 800 грн",
    image: "skin",
  },
];

const masters = [
  {
    name: "Мастер Анастасия",
    specialization: "Ресницы и ламинирование",
    note: "Подбирает эффект под форму глаз.",
  },
  {
    name: "Мастер Мария",
    specialization: "Брови и макияж",
    note: "Работает с формой, оттенком и образом.",
  },
  {
    name: "Мастер Елена",
    specialization: "Маникюр и уход",
    note: "Отвечает за аккуратную обработку и покрытие.",
  },
];

const portfolioItems = [
  { category: "lashes", title: "Демо-работа: ресницы", image: "lashes" },
  { category: "brows", title: "Демо-работа: брови", image: "brows" },
  { category: "nails", title: "Демо-работа: ногти", image: "nails" },
  { category: "makeup", title: "Демо-работа: макияж", image: "makeup" },
  { category: "lashes", title: "Демо-работа: ламинирование", image: "lashes-soft" },
  { category: "brows", title: "Демо-работа: окрашивание", image: "brows-soft" },
  { category: "nails", title: "Демо-работа: маникюр", image: "nails-soft" },
  { category: "makeup", title: "Демо-работа: вечерний образ", image: "makeup-soft" },
  { category: "lashes", title: "Демо-работа: естественный эффект", image: "lashes-light" },
];

const reviewPlaceholders = [
  {
    title: "Пример отзыва",
    text: "Здесь можно разместить реальный отзыв клиента.",
  },
  {
    title: "Пример отзыва",
    text: "Заглушка для будущего отзыва студии.",
  },
  {
    title: "Пример отзыва",
    text: "Замените эту карточку реальным отзывом.",
  },
];
