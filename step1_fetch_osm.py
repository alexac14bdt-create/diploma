import asyncio
import httpx
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
OSM_OUTPUT_FILE = os.path.join(DATA_DIR, "osm_raw.json")

CATEGORIES = {

    "supermarket": {
        "label": "Супермаркет",
        "tags": [
            '["shop"="supermarket"]',
            '["shop"="convenience"]',
            '["shop"="grocery"]',
        ]
    },

    "pharmacy": {
        "label": "Аптека",
        "tags": ['["amenity"="pharmacy"]']
    },
    "clinic": {
        "label": "Поликлиника",
        "tags": ['["amenity"="clinic"]', '["healthcare"="centre"]']
    },
    "hospital": {
        "label": "Больница",
        "tags": ['["amenity"="hospital"]']
    },
    "dentist": {
        "label": "Стоматология",
        "tags": ['["amenity"="dentist"]', '["healthcare"="dentist"]']
    },
    "veterinary": {
        "label": "Ветеринарная клиника",
        "tags": ['["amenity"="veterinary"]']
    },

    "bank": {
        "label": "Банк",
        "tags": ['["amenity"="bank"]']
    },

    "school": {
        "label": "Школа",
        "tags": ['["amenity"="school"]']
    },
    "kindergarten": {
        "label": "Детский сад",
        "tags": ['["amenity"="kindergarten"]']
    },
    "library": {
        "label": "Библиотека",
        "tags": ['["amenity"="library"]']
    },

    "post_office": {
        "label": "Почта",
        "tags": ['["amenity"="post_office"]']
    },
    "government": {
        "label": "МФЦ",
        "tags": [
            '["office"="government"]',
            '["amenity"="townhall"]',
            '["name"~"МФЦ",i]',
        ]
    },
    "police": {
        "label": "Полиция",
        "tags": ['["amenity"="police"]']
    },
    "notary": {
        "label": "Нотариус",
        "tags": ['["office"="notary"]', '["amenity"="notary"]']
    },
    "housing_office": {
        "label": "ЖЭК",
        "tags": [
            '["office"="housing"]',
            '["name"~"ЖЭК|ЖКХ|управляющая компания",i]',
        ]
    },

    "dry_cleaning": {
        "label": "Химчистка",
        "tags": ['["shop"="dry_cleaning"]']
    },
    "laundry": {
        "label": "Прачечная",
        "tags": ['["shop"="laundry"]']
    },
    "phone_repair": {
        "label": "Ремонт телефонов",
        "tags": [
            '["shop"="mobile_phone"]',
            '["repair"="phone"]',
            '["name"~"ремонт.*телефон|сервис.*телефон",i]',
        ]
    },
    "hairdresser": {
        "label": "Парикмахерская",
        "tags": ['["shop"="hairdresser"]']
    },
    "beauty": {
        "label": "Салон красоты",
        "tags": ['["shop"="beauty"]', '["leisure"="spa"]']
    },

    "car_wash": {
        "label": "Автомойка",
        "tags": ['["amenity"="car_wash"]']
    },
    "tyres": {
        "label": "Шиномонтаж",
        "tags": ['["shop"="tyres"]', '["name"~"шиномонтаж",i]']
    },
    "fuel": {
        "label": "АЗС",
        "tags": ['["amenity"="fuel"]']
    },

    "books": {
        "label": "Книжный магазин",
        "tags": ['["shop"="books"]']
    },
    "clothes": {
        "label": "Магазин одежды",
        "tags": ['["shop"="clothes"]', '["shop"="shoes"]']
    },
    "pet_shop": {
        "label": "Зоомагазин",
        "tags": ['["shop"="pet"]']
    },
    "florist": {
        "label": "Цветочный магазин",
        "tags": ['["shop"="florist"]']
    },
    "copyshop": {
        "label": "Копировальный центр",
        "tags": ['["shop"="copyshop"]', '["name"~"копи|копировал|печать",i]']
    },
    "marketplace": {
        "label": "Рынок",
        "tags": ['["amenity"="marketplace"]', '["shop"="wholesale"]']
    },

    "gym": {
        "label": "Спортзал",
        "tags": [
            '["leisure"="fitness_centre"]',
            '["leisure"="sports_centre"]',
        ]
    },
    "swimming_pool": {
        "label": "Бассейн",
        "tags": [
            '["leisure"="swimming_pool"]["access"!="private"]',
            '["sport"="swimming"]',
        ]
    },
    "ice_rink": {
        "label": "Каток",
        "tags": ['["leisure"="ice_rink"]']
    },
    "computer_club": {
        "label": "Компьютерный клуб",
        "tags": [
            '["amenity"="gaming"]',
            '["name"~"компьютерный клуб|киберклуб|кибер клуб|cybercafe",i]',
        ]
    },
    "vr_club": {
        "label": "VR-клуб",
        "tags": ['["name"~"VR|виртуальная реальность|vr.клуб",i]']
    },

    "cafe": {
        "label": "Кафе / Кофейня / Антикафе",
        "tags": [
            '["amenity"="cafe"]',
            '["amenity"="coffee_shop"]',
        ]
    },
    "restaurant": {
        "label": "Ресторан",
        "tags": ['["amenity"="restaurant"]']
    },
    "canteen": {
        "label": "Столовая",
        "tags": ['["amenity"="canteen"]', '["name"~"столовая",i]']
    },
    "fast_food": {
        "label": "Фастфуд",
        "tags": ['["amenity"="fast_food"]']
    },
    "bar": {
        "label": "Бар / Паб",
        "tags": ['["amenity"="bar"]', '["amenity"="pub"]']
    },

    "cinema": {
        "label": "Кинотеатр",
        "tags": ['["amenity"="cinema"]']
    },
    "theatre": {
        "label": "Театр",
        "tags": ['["amenity"="theatre"]']
    },
    "museum": {
        "label": "Музей",
        "tags": ['["tourism"="museum"]']
    },
}

MAX_PER_CATEGORY = 500

async def fetch_category(client: httpx.AsyncClient, category_key: str, info: dict) -> list:
    tag_filters = info["tags"]
    label = info["label"]

    lines = []
    for tag in tag_filters:
        lines.append(f"  node{tag}(area.spb);")
        lines.append(f"  way{tag}(area.spb);")

    query = f"""
[out:json][timeout:90];
area["name"="Санкт-Петербург"]["admin_level"="4"]->.spb;
(
{''.join(lines)}
);
out center tags;
"""

    try:
        resp = await client.post(
            "https://overpass.kumi.systems/api/interpreter",
            data={"data": query},
            timeout=120,
        )

        if resp.status_code != 200:
            print(f"\n    ⚠️  HTTP {resp.status_code} для категории '{label}'")
            return []

        data = resp.json()
        elements = data.get("elements", [])

        results = []
        for el in elements:
            parsed = parse_element(el, category_key, label)
            if parsed:
                results.append(parsed)
            if len(results) >= MAX_PER_CATEGORY:
                break

        return results

    except Exception as e:
        print(f"\n    ❌ Ошибка для '{label}': {e}")
        return []

def parse_element(el: dict, category_key: str, label: str) -> dict | None:
    tags = el.get("tags", {})

    if el.get("type") == "node":
        lat = el.get("lat")
        lon = el.get("lon")
    else:
        center = el.get("center", {})
        lat = center.get("lat")
        lon = center.get("lon")

    if not lat or not lon:
        return None

    name = (
        tags.get("name:ru") or
        tags.get("name") or
        tags.get("brand:ru") or
        tags.get("brand") or
        ""
    ).strip()

    if not name or len(name) < 2:
        return None

    street  = tags.get("addr:street", "")
    house   = tags.get("addr:housenumber", "")
    city    = tags.get("addr:city", "Санкт-Петербург")

    if street and house:
        address = f"{street}, {house}, Санкт-Петербург"
    elif street:
        address = f"{street}, Санкт-Петербург"
    else:
        return None

    phone = (
        tags.get("phone") or
        tags.get("contact:phone") or
        tags.get("telephone")
    )

    wc = tags.get("wheelchair", "").lower()
    wheelchair = wc in ("yes", "limited")

    website = tags.get("website") or tags.get("contact:website")

    return {
        "osm_id":      el.get("id"),
        "osm_type":    el.get("type"),
        "category_key": category_key,
        "category_label": label,
        "name":        name,
        "address":     address,
        "lat":         lat,
        "lon":         lon,
        "phone":       phone,
        "website":     website,
        "wheelchair":  wheelchair,
        "wc_tag":      wc or "unknown",
    }

async def main():
    print("=" * 60)
    print("  ЭТАП 1/4: Выгрузка данных из OpenStreetMap")
    print("=" * 60)
    print(f"  Категорий для загрузки: {len(CATEGORIES)}")
    print(f"  Результат сохранится в: data/osm_raw.json")
    print()

    os.makedirs(DATA_DIR, exist_ok=True)

    all_results = {}
    total = 0
    failed = []

    async with httpx.AsyncClient() as client:
        for key, info in CATEGORIES.items():
            label = info["label"]
            print(f"  📂 {label:<30}", end="", flush=True)

            items = await fetch_category(client, key, info)
            all_results[key] = items
            total += len(items)

            if items:
                print(f"✅ {len(items)} объектов")
            else:
                print(f"⚠️  0 объектов")
                failed.append(label)

            await asyncio.sleep(3)

    output = {
        "fetched_at": datetime.now().isoformat(),
        "total_objects": total,
        "categories": all_results,
    }

    with open(OSM_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print()
    print("=" * 60)
    print(f"  ✅ Этап 1 завершён!")
    print(f"  Всего объектов скачано: {total}")
    print(f"  Файл сохранён: data/osm_raw.json")
    if failed:
        print(f"  ⚠️  Пустые категории ({len(failed)}): {', '.join(failed)}")
    print()
    print("  👉 Следующий шаг:")
    print("     python scripts/step2_load_osm.py")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())