import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from db.models import Chain, Place, Accessibility, CategoryEnum

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine       = create_async_engine(DATABASE_URL, echo=False)
AsyncSession = async_sessionmaker(bind=engine, expire_on_commit=False)

DATA_DIR       = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
OSM_INPUT_FILE = os.path.join(DATA_DIR, "osm_raw.json")

CATEGORY_MAP = {
    "supermarket":   CategoryEnum.supermarket,
    "pharmacy":      CategoryEnum.pharmacy,
    "clinic":        CategoryEnum.clinic,
    "hospital":      CategoryEnum.clinic,
    "dentist":       CategoryEnum.clinic,
    "veterinary":    CategoryEnum.clinic,
    "bank":          CategoryEnum.bank,
    "school":        CategoryEnum.clinic,
    "kindergarten":  CategoryEnum.clinic,
    "library":       CategoryEnum.clinic,
    "post_office":   CategoryEnum.government,
    "government":    CategoryEnum.government,
    "police":        CategoryEnum.government,
    "notary":        CategoryEnum.government,
    "housing_office":CategoryEnum.government,
    "dry_cleaning":  CategoryEnum.mall,
    "laundry":       CategoryEnum.mall,
    "phone_repair":  CategoryEnum.mall,
    "hairdresser":   CategoryEnum.mall,
    "beauty":        CategoryEnum.mall,
    "car_wash":      CategoryEnum.transport,
    "tyres":         CategoryEnum.transport,
    "fuel":          CategoryEnum.transport,
    "books":         CategoryEnum.mall,
    "clothes":       CategoryEnum.mall,
    "pet_shop":      CategoryEnum.mall,
    "florist":       CategoryEnum.mall,
    "copyshop":      CategoryEnum.mall,
    "marketplace":   CategoryEnum.mall,
    "gym":           CategoryEnum.sport,
    "swimming_pool": CategoryEnum.sport,
    "ice_rink":      CategoryEnum.sport,
    "computer_club": CategoryEnum.mall,
    "vr_club":       CategoryEnum.mall,
    "cafe":          CategoryEnum.cafe,
    "restaurant":    CategoryEnum.cafe,
    "canteen":       CategoryEnum.cafe,
    "fast_food":     CategoryEnum.cafe,
    "bar":           CategoryEnum.cafe,
    "cinema":        CategoryEnum.mall,
    "theatre":       CategoryEnum.mall,
    "museum":        CategoryEnum.mall,
}

CHAINS = {
    "сбербанк":        "Сбербанк",
    "сбер":            "Сбербанк",
    "альфа-банк":      "Альфа-Банк",
    "альфабанк":       "Альфа-Банк",
    "альфа банк":      "Альфа-Банк",
    "втб":             "ВТБ",
    "газпромбанк":     "Газпромбанк",
    "тинькофф":        "Тинькофф",
    "россельхозбанк":  "Россельхозбанк",
    "райффайзен":      "Райффайзенбанк",
    "пятёрочка":       "Пятёрочка",
    "пятерочка":       "Пятёрочка",
    "магнит":          "Магнит",
    "перекрёсток":     "Перекрёсток",
    "перекресток":     "Перекрёсток",
    "лента":           "Лента",
    "окей":            "Окей",
    "вкусвилл":        "ВкусВилл",
    "дикси":           "Дикси",
    "ашан":            "Ашан",
    "metro":           "Metro",
    "метро":           "Metro",
    "невис":           "Аптека Невис",
    "ригла":           "Ригла",
    "горздрав":        "Горздрав",
    "планета здоровья":"Планета здоровья",
    "apteka":          "Apteka.ru",
    "еаптека":         "Еаптека",
    "мфц":             "МФЦ СПб",
    "почта":           "Почта России",
    "мвд":             "МВД",
    "макдоналдс":      "Макдоналдс",
    "макдональдс":     "Макдоналдс",
    "kfc":             "KFC",
    "бургер кинг":     "Бургер Кинг",
    "subway":          "Subway",
    "сабвей":          "Subway",
    "додо":            "Додо Пицца",
    "шоколадница":     "Шоколадница",
    "starbucks":       "Starbucks",
    "старбакс":        "Starbucks",
    "costa":           "Costa Coffee",
    "скиллbox":        "Skillbox",
    "зоозавр":         "Зоозавр",
    "четыре лапы":     "Четыре лапы",
    "Gloria jeans":    "Gloria Jeans",
    "gloria jeans":    "Gloria Jeans",
    "zara":            "Zara",
    "h&m":             "H&M",
    "галерея":         "ТРК Галерея",
    "мега":            "МЕГА",
    "park inn":        "Park Inn",
    "marriott":        "Marriott",
    "лукойл":          "Лукойл",
    "газпромнефть":    "Газпромнефть",
    "роснефть":        "Роснефть",
}

def detect_chain(name: str) -> str | None:
    name_lower = name.lower()
    for keyword, chain_name in CHAINS.items():
        if keyword in name_lower:
            return chain_name
    return None

async def get_or_create_chain(session, chain_name: str, category: CategoryEnum, cache: dict) -> int:
    key = f"{chain_name}:{category.value}"
    if key in cache:
        return cache[key]

    result = await session.execute(
        select(Chain).where(Chain.name == chain_name, Chain.category == category)
    )
    chain = result.scalar_one_or_none()
    if not chain:
        chain = Chain(name=chain_name, category=category)
        session.add(chain)
        await session.flush()

    cache[key] = chain.id
    return chain.id

async def place_exists(session, name: str, address: str) -> bool:
    result = await session.execute(
        select(Place.id).where(
            Place.name == name,
            Place.address == address,
        )
    )
    return result.scalar_one_or_none() is not None

async def save_one(session, item: dict, chain_cache: dict) -> str:
    try:
        category_key = item.get("category_key", "")
        category = CATEGORY_MAP.get(category_key)
        if not category:
            return "error"

        name    = item["name"]
        address = item["address"]

        if await place_exists(session, name, address):
            return "duplicate"

        chain_name = detect_chain(name)
        chain_id   = None
        if chain_name:
            chain_id = await get_or_create_chain(session, chain_name, category, chain_cache)

        place = Place(
            name=name,
            address=address,
            lat=item["lat"],
            lon=item["lon"],
            phone=(item.get("phone") or "")[:50] or None,
            website=(item.get("website") or "")[:200] or None,
            category=category,
            chain_id=chain_id,
        )
        session.add(place)
        await session.flush()

        wheelchair = item.get("wheelchair", False)
        acc = Accessibility(
            place_id=place.id,
            wheelchair=wheelchair,
            accessible_entrance=wheelchair,
            accessible_toilet=False,
            elevator=False,
            blind=False,
            braille_signs=False,
            audio_guide=False,
            deaf=False,
            induction_loop=False,
            visual_alerts=False,
            notes=(
                "♿ Адаптировано для колясочников (данные OpenStreetMap)"
                if wheelchair else
                "Данные о доступности не проверены"
            ),
        )
        session.add(acc)
        return "added"

    except Exception as e:
        return f"error:{e}"

async def main():
    print("=" * 60)
    print("  ЭТАП 2/4: Загрузка данных OSM в базу данных")
    print("=" * 60)

    if not os.path.exists(OSM_INPUT_FILE):
        print()
        print("  ❌ Файл data/osm_raw.json не найден!")
        print("  Сначала запусти: python scripts/step1_fetch_osm.py")
        return

    with open(OSM_INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_in_file = data.get("total_objects", 0)
    fetched_at    = data.get("fetched_at", "неизвестно")
    categories    = data.get("categories", {})

    print(f"  Файл: data/osm_raw.json")
    print(f"  Выгружен: {fetched_at}")
    print(f"  Объектов в файле: {total_in_file}")
    print()

    stats = {"added": 0, "duplicate": 0, "error": 0}
    chain_cache = {}
    BATCH_SIZE  = 50

    async with AsyncSession() as session:
        for cat_key, items in categories.items():
            if not items:
                continue

            label    = items[0].get("category_label", cat_key) if items else cat_key
            cat_added = 0
            cat_dup   = 0

            for item in items:
                result = await save_one(session, item, chain_cache)
                if result == "added":
                    stats["added"] += 1
                    cat_added += 1
                elif result == "duplicate":
                    stats["duplicate"] += 1
                    cat_dup += 1
                else:
                    stats["error"] += 1

                if (stats["added"] + stats["duplicate"]) % BATCH_SIZE == 0:
                    await session.commit()

            await session.commit()
            print(f"  ✅ {label:<35} добавлено: {cat_added:>4}  дублей: {cat_dup:>4}")

    print()
    print("=" * 60)
    print(f"  ✅ Этап 2 завершён!")
    print(f"  Добавлено в БД:    {stats['added']}")
    print(f"  Пропущено (дубли): {stats['duplicate']}")
    print(f"  Ошибок:            {stats['error']}")
    print()
    print("  👉 Следующий шаг:")
    print("     python scripts/step3_fetch_2gis.py")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())