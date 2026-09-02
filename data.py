MASTER_INFO = (
    "👩‍🎨 <b>Про майстра</b>\n\n"
    "Вітаю! Я б'юті-майстер, який допомагає підкреслити природну красу "
    "та створити акуратний, доглянутий образ.\n\n"
    "Працюю уважно, стерильно та без поспіху. Перед записом ми узгоджуємо "
    "послугу, дату й час."
)

SERVICES = [
    {
        "id": "lashes",
        "name": "Нарощування вій",
        "price": "від 900 грн",
        "duration": "2–3 години",
        "description": "Підбір ефекту під форму очей і бажаний образ.",
        "group_ids": ["anastasia"],
    },
    {
        "id": "lash_lamination",
        "name": "Ламінування вій",
        "price": "від 650 грн",
        "duration": "60–90 хв",
        "description": "Природний вигин і доглянутий вигляд без нарощування.",
        "group_ids": ["anastasia"],
    },
    {
        "id": "brows",
        "name": "Оформлення та фарбування брів",
        "price": "від 450 грн",
        "duration": "40–60 хв",
        "description": "Форма й відтінок з урахуванням рис обличчя.",
        "group_ids": ["maria"],
    },
    {
        "id": "manicure",
        "name": "Манікюр",
        "price": "від 700 грн",
        "duration": "1.5–2 години",
        "description": "Чиста обробка й акуратне покриття.",
        "group_ids": ["olena"],
    },
    {
        "id": "makeup",
        "name": "Макіяж",
        "price": "від 1000 грн",
        "duration": "60–120 хв",
        "description": "Денний, вечірній або святковий образ.",
        "group_ids": ["maria"],
    },
    {
        "id": "skincare",
        "name": "Догляд за шкірою",
        "price": "від 800 грн",
        "duration": "45–90 хв",
        "description": "Делікатні процедури для свіжого вигляду шкіри.",
        "group_ids": ["olena"],
    },
]

SCHEDULE_GROUPS = [
    {"id": "anastasia", "name": "Майстер Анастасія", "service_ids": ["lashes", "lash_lamination"]},
    {"id": "maria", "name": "Майстер Марія", "service_ids": ["brows", "makeup"]},
    {"id": "olena", "name": "Майстер Олена", "service_ids": ["manicure", "skincare"]},
]

CONTACTS = (
    "📍 <b>Контакти</b>\n\n"
    "Telegram: @beauty_master\n"
    "Instagram: instagram.com/beauty_master\n"
    "Адреса: ваше місто, район/студія\n\n"
    "Точну адресу майстер надсилає після підтвердження запису."
)

PORTFOLIO_PHOTOS = [
    "assets/portfolio/work_1.jpg",
    "assets/portfolio/work_2.jpg",
    "assets/portfolio/work_3.jpg",
]
