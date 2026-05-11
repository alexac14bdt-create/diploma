import asyncio
import httpx
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from db.models import Chain, Place, Accessibility, CategoryEnum

load_dotenv()

DATABASE_URL  = os.getenv("DATABASE_URL")
TWOGIS_KEY    = os.getenv("TWOGIS_API_KEY")

engine        = create_async_engine(DATABASE_URL, echo=False)
AsyncSession  = async_sessionmaker(bind=engine, expire_on_commit=False)

CATEGORY_QUERIES = {
    CategoryEnum.supermarket:  ["супермаркет", "продукты"],
    CategoryEnum.pharmacy:     ["аптека"],
    CategoryEnum.clinic:       ["поликлиника", "больница", "стоматология", "ветеринарная клиника"],
    CategoryEnum.bank:         ["банк", "банкомат"],
    CategoryEnum.government:   ["МФЦ", "почта", "полиция", "ЖЭК", "нотариус"],
    CategoryEnum.mall:         ["торговый центр", "рынок", "магазин одежды"],
    CategoryEnum.cafe:         ["кафе", "ресторан", "столовая", "фастфуд",
                                "кофейня", "бар", "антикафе"],
    CategoryEnum.sport:        ["спортзал", "бассейн", "каток"],
    CategoryEnum.hotel:        ["гостиница", "отель"],
    CategoryEnum.transport:    ["автомойка", "шиномонтаж", "АЗС"],
}

EXTRA_QUERIES = {
    CategoryEnum.clinic:   ["школа", "детский сад", "библиотека"],
    CategoryEnum.mall:     ["книжный магазин", "зоомагазин", "цветочный магазин",
                            "салон красоты", "парикмахерская", "химчистка",
                            "прачечная", "ремонт телефонов", "копировальный центр",
                            "компьютерный клуб", "VR-клуб"],
    CategoryEnum.cafe:     ["кинотеатр", "театр", "музей"],
}

CITY = "Санкт-Петербург"
MAX_PER_QUERY = 50

async def fetch_2gis(client: httpx.AsyncClient, query: str, page: int = 1) -> list[dict]:
    url = "https://catalog.api.2gis.com/3.0/items"
    params = {
        "q":           query,
        "location":    "30.3141,59.9311",
        "radius":      30000,
        "type":        "branch",
        "fields":      "items.point,items.address,items.contact_groups,items.rubrics",
        "page_size":   MAX_PER_QUERY,
        "page":        page,
        "key":         TWOGIS_KEY,
        "city_id":     "4504222876482159",
    }

    try:
        resp = await client.get(url, params=params, timeout=15)
        data = resp.json()

        if data.get("meta", {}).get("code") != 200:
            print(f"  ⚠️  2GIS вернул ошибку для '{query}': {data.get('meta')}")
            return []

        return data.get("result", {}).get("items", [])

    except Exception as e:
        print(f"  ❌ Ошибка запроса к 2GIS для '{query}': {e}")
        return []

def parse_2gis_item(item: dict, category: CategoryEnum) -> dict | None:
    point = item.get("point")
    if not point:
        return None

    addr_obj = item.get("address", {})
    address  = addr_obj.get("name", "").strip()
    if not address:
        return None

    name = item.get("name", "").strip()
    if not name:
        return None

    phone = None
    contacts = item.get("contact_groups", [])
    for group in contacts:
        for contact in group.get("contacts", []):
            if contact.get("type") == "phone":
                phone = contact.get("value")
                break
        if phone:
            break

    rubrics = item.get("rubrics", [])
    rubric_name = rubrics[0].get("name", "") if rubrics else ""

    return {
        "name":        name,
        "address":     f"{address}, Санкт-Петербург",
        "lat":         point.get("lat"),
        "lon":         point.get("lon"),
        "phone":       phone,
        "category":    category,
        "rubric_name": rubric_name,
        "external_id": item.get("id", ""),
    }

async def fetch_osm_wheelchair(client: httpx.AsyncClient) -> list[dict]:
    print("📡 Загружаем данные о доступности из OpenStreetMap...")

    query = """
    [out:json][timeout:60];
    area["name"="Санкт-Петербург"]["admin_level"="4"]->.spb;
    (
      node["wheelchair"="yes"](area.spb);
      node["wheelchair"="limited"](area.spb);
      way["wheelchair"="yes"](area.spb);
      way["wheelchair"="limited"](area.spb);
    );
    out center;
    """

    try:
        resp = await client.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query},
            timeout=90
        )
        data = resp.json()
        elements = data.get("elements", [])
        print(f"  ✅ OSM: получено {len(elements)} объектов с wheelchair=yes/limited")
        return elements

    except Exception as e:
        print(f"  ⚠️  Не удалось загрузить данные OSM: {e}")
        print("  Продолжаем без данных о доступности из OSM.")
        return []

def build_osm_index(osm_elements: list[dict]) -> list[tuple[float, float]]:
    coords = []
    for el in osm_elements:
        if el.get("type") == "node":
            lat, lon = el.get("lat"), el.get("lon")
        else:
            center = el.get("center", {})
            lat, lon = center.get("lat"), center.get("lon")
        if lat and lon:
            coords.append((lat, lon))
    return coords

def is_wheelchair_accessible(lat: float, lon: float, osm_coords: list, threshold_m: float = 50) -> bool:
    import math
    for olat, olon in osm_coords:
        dlat = abs(lat - olat) * 111320
        dlon = abs(lon - olon) * 111320 * math.cos(math.radians(lat))
        dist = math.sqrt(dlat**2 + dlon**2)
        if dist <= threshold_m:
            return True
    return False

CHAIN_KEYWORDS = {
    "сбербанк":       "Сбербанк",
    "сбер":           "Сбербанк",
    "альфа":          "Альфа-Банк",
    "альфа-банк":     "Альфа-Банк",
    "втб":            "ВТБ",
    "газпромбанк":    "Газпромбанк",
    "тинькофф":       "Тинькофф",
    "пятёрочка":      "Пятёрочка",
    "пятерочка":      "Пятёрочка",
    "магнит":         "Магнит",
    "перекрёсток":    "Перекрёсток",
    "перекресток":    "Перекрёсток",
    "лента":          "Лента",
    "окей":           "Окей",
    "о'кей":          "Окей",
    "вкусвилл":       "ВкусВилл",
    "аптека невис":   "Аптека Невис",
    "невис":          "Аптека Невис",
    "rigla":          "Ригла",
    "ригла":          "Ригла",
    "горздрав":       "Горздрав",
    "планета здоровья": "Планета здоровья",
    "мфц":            "МФЦ СПб",
    "почта россии":   "Почта России",
    "почта":          "Почта России",
    "макдоналдс":     "Макдоналдс",
    "макдональдс":    "Макдоналдс",
    "kfc":            "KFC",
    "бургер кинг":    "Бургер Кинг",
    "subway":         "Subway",
    "сабвей":         "Subway",
    "додо":           "Додо Пицца",
    "додо пицца":     "Додо Пицца",
    "шоколадница":    "Шоколадница",
    "кофе хауз":      "Кофе Хауз",
    "starbucks":      "Starbucks",
    "старбакс":       "Starbucks",
    "costa":          "Costa Coffee",
    "галерея":        "ТРК Галерея",
    "мега":           "МЕГА",
    "park inn":       "Park Inn",
    "marriott":       "Marriott",
    "hilton":         "Hilton",
    "полиция":        "Полиция",
    "мвд":            "МВД",
}

async def get_or_create_chain(
    session, name: str, category: CategoryEnum, chain_cache: dict
) -> int | None:
    name_lower = name.lower()

    chain_name = None
    for keyword, canonical in CHAIN_KEYWORDS.items():
        if keyword in name_lower:
            chain_name = canonical
            break

    if not chain_name:
        return None

    cache_key = f"{chain_name}:{category.value}"
    if cache_key in chain_cache:
        return chain_cache[cache_key]

    result = await session.execute(
        select(Chain).where(Chain.name == chain_name, Chain.category == category)
    )
    chain = result.scalar_one_or_none()

    if not chain:
        chain = Chain(name=chain_name, category=category)
        session.add(chain)
        await session.flush()

    chain_cache[cache_key] = chain.id
    return chain.id

async def save_place(session, item: dict, chain_id: int | None, wheelchair: bool) -> bool:
    result = await session.execute(
        select(Place).where(
            Place.name == item["name"],
            Place.address == item["address"]
        )
    )
    if result.scalar_one_or_none():
        return False

    place = Place(
        name=item["name"],
        address=item["address"],
        lat=item["lat"],
        lon=item["lon"],
        phone=item.get("phone"),
        category=item["category"],
        chain_id=chain_id,
    )
    session.add(place)
    await session.flush()

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
        notes="Данные о доступности требуют проверки" if not wheelchair else
              "Адаптировано для колясочников по данным OpenStreetMap",
    )
    session.add(acc)
    return True

async def main():
    if not TWOGIS_KEY:
        print("❌ ОШИБКА: TWOGIS_API_KEY не найден в файле .env")
        print("   Получи ключ на https://dev.2gis.ru и добавь в .env:")
        print("   TWOGIS_API_KEY=твой_ключ")
        return

    print("=" * 60)
    print("  Парсер организаций СПб → PostgreSQL")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        osm_elements = await fetch_osm_wheelchair(client)
        osm_coords   = build_osm_index(osm_elements)
        print(f"  OSM индекс: {len(osm_coords)} точек с wheelchair доступностью\n")

        all_queries = {}
        for cat, queries in CATEGORY_QUERIES.items():
            all_queries.setdefault(cat, []).extend(queries)
        for cat, queries in EXTRA_QUERIES.items():
            all_queries.setdefault(cat, []).extend(queries)

        total_added   = 0
        total_skipped = 0
        chain_cache   = {}

        async with AsyncSession() as session:
            for category, queries in all_queries.items():
                print(f"\n📂 Категория: {category.value}")

                for query in queries:
                    print(f"  🔍 Запрос: «{query}»", end="", flush=True)

                    items = await fetch_2gis(client, query)
                    added_for_query = 0

                    for raw in items:
                        parsed = parse_2gis_item(raw, category)
                        if not parsed:
                            continue

                        wheelchair = is_wheelchair_accessible(
                            parsed["lat"], parsed["lon"], osm_coords
                        )

                        chain_id = await get_or_create_chain(
                            session, parsed["name"], category, chain_cache
                        )

                        added = await save_place(session, parsed, chain_id, wheelchair)
                        if added:
                            added_for_query += 1
                            total_added += 1
                        else:
                            total_skipped += 1

                    await session.commit()
                    print(f" → добавлено: {added_for_query}")

                    await asyncio.sleep(0.5)

        print("\n" + "=" * 60)
        print(f"  ✅ Готово!")
        print(f"  Добавлено новых объектов:  {total_added}")
        print(f"  Пропущено (уже в базе):    {total_skipped}")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())