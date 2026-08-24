const siteConfig = {
  studioName: "Beauty Studio",
  city: "Харьков",
  tagline: "Спокойное пространство красоты, ухода и уверенности",
  description:
    "Демонстрационный шаблон сайта для бьюти-студии, частного мастера или салона. Все тексты, услуги, цены, фотографии и контакты легко заменить под реального клиента.",
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
    description: "Аккуратный объём, подбор эффекта под форму глаз и образ клиента.",
    duration: "2–3 часа",
    price: "от 900 грн",
    image: "lashes",
  },
  {
    id: "lash-lamination",
    title: "Ламинирование ресниц",
    description: "Естественный изгиб, ухоженный вид и мягкий акцент без наращивания.",
    duration: "60–90 мин",
    price: "от 650 грн",
    image: "lashes",
  },
  {
    id: "brows",
    title: "Оформление и окрашивание бровей",
    description: "Форма, оттенок и чистая линия с учётом черт лица.",
    duration: "40–60 мин",
    price: "от 450 грн",
    image: "brows",
  },
  {
    id: "manicure",
    title: "Маникюр",
    description: "Чистая обработка, покрытие и аккуратный результат на каждый день.",
    duration: "1.5–2 часа",
    price: "от 700 грн",
    image: "nails",
  },
  {
    id: "makeup",
    title: "Макияж",
    description: "Дневной, вечерний или образ для события с комфортной посадкой.",
    duration: "60–120 мин",
    price: "от 1000 грн",
    image: "makeup",
  },
  {
    id: "skincare",
    title: "Уход за кожей",
    description: "Деликатные уходовые процедуры для свежего и ухоженного вида.",
    duration: "45–90 мин",
    price: "от 800 грн",
    image: "skin",
  },
];

const masters = [
  {
    name: "Мастер Анастасия",
    specialization: "Ресницы и ламинирование",
    note: "Помогает подобрать эффект под форму глаз и привычный образ.",
  },
  {
    name: "Мастер Мария",
    specialization: "Брови и макияж",
    note: "Работает с формой, оттенком и мягкими образами на каждый день.",
  },
  {
    name: "Мастер Елена",
    specialization: "Маникюр и уход",
    note: "Фокусируется на чистой обработке и аккуратном покрытии.",
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
    text: "Здесь можно разместить реальный отзыв клиента после согласования текста.",
  },
  {
    title: "Пример отзыва",
    text: "Блок оставлен как демонстрационная зона для будущих отзывов студии.",
  },
  {
    title: "Пример отзыва",
    text: "Не используйте фальшивые отзывы: замените эти карточки реальными.",
  },
];
