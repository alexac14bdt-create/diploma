import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from dotenv import load_dotenv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.base import Base
from db.models import Chain, Place, Accessibility, CategoryEnum

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSession = async_sessionmaker(bind=engine, expire_on_commit=False)

CHAINS_DATA = [
    {"name": "Сбербанк",                "category": CategoryEnum.bank},
    {"name": "Аптека Невис",            "category": CategoryEnum.pharmacy},
    {"name": "Лента",                   "category": CategoryEnum.supermarket},
    {"name": "Мариинская больница",     "category": CategoryEnum.clinic},
    {"name": "Кофе Хауз",              "category": CategoryEnum.cafe},
    {"name": "Галерея",                 "category": CategoryEnum.mall},
    {"name": "МФЦ СПб",               "category": CategoryEnum.government},
    {"name": "Ски Парк",              "category": CategoryEnum.sport},
    {"name": "Park Inn Прибалтийская", "category": CategoryEnum.hotel},
    {"name": "Пятёрочка",             "category": CategoryEnum.supermarket},
]

PLACES_DATA = [
    {
        "name": "Сбербанк — Невский пр.",
        "address": "Невский пр., 45, Санкт-Петербург",
        "lat": 59.9311, "lon": 30.3441,
        "chain_index": 0,
        "category": CategoryEnum.bank,
        "phone": "+7 800 555-55-50",
        "accessibility": {
            "wheelchair": True, "accessible_entrance": True,
            "accessible_toilet": True, "elevator": True,
            "blind": True, "braille_signs": True, "audio_guide": False,
            "deaf": False, "induction_loop": False, "visual_alerts": False,
            "notes": "Пандус у главного входа, тактильная плитка, банкомат с Брайлем"
        }
    },
    {
        "name": "Сбербанк — Московский пр.",
        "address": "Московский пр., 78, Санкт-Петербург",
        "lat": 59.8983, "lon": 30.3196,
        "chain_index": 0,
        "category": CategoryEnum.bank,
        "phone": "+7 800 555-55-50",
        "accessibility": {
            "wheelchair": False, "accessible_entrance": False,
            "accessible_toilet": False, "elevator": False,
            "blind": False, "braille_signs": False, "audio_guide": False,
            "deaf": False, "induction_loop": False, "visual_alerts": False,
            "notes": "Вход — 3 ступени, без пандуса"
        }
    },
    {
        "name": "Аптека Невис — Литейный пр.",
        "address": "Литейный пр., 26, Санкт-Петербург",
        "lat": 59.9440, "lon": 30.3494,
        "chain_index": 1,
        "category": CategoryEnum.pharmacy,
        "phone": "+7 812 275-35-05",
        "accessibility": {
            "wheelchair": True, "accessible_entrance": True,
            "accessible_toilet": False, "elevator": False,
            "blind": False, "braille_signs": False, "audio_guide": False,
            "deaf": True, "induction_loop": False, "visual_alerts": True,
            "notes": "Широкий вход, пандус, табло с номерами очереди"
        }
    },
    {
        "name": "Лента — Пулковское шоссе",
        "address": "Пулковское шоссе, 25к1, Санкт-Петербург",
        "lat": 59.8231, "lon": 30.3244,
        "chain_index": 2,
        "category": CategoryEnum.supermarket,
        "phone": "+7 800 700-41-11",
        "accessibility": {
            "wheelchair": True, "accessible_entrance": True,
            "accessible_toilet": True, "elevator": True,
            "blind": False, "braille_signs": False, "audio_guide": False,
            "deaf": True, "induction_loop": False, "visual_alerts": True,
            "notes": "Парковка для инвалидов, широкие проходы, касса для колясочников"
        }
    },
    {
        "name": "Мариинская больница",
        "address": "Литейный пр., 56, Санкт-Петербург",
        "lat": 59.9398, "lon": 30.3500,
        "chain_index": 3,
        "category": CategoryEnum.clinic,
        "phone": "+7 812 275-70-77",
        "accessibility": {
            "wheelchair": True, "accessible_entrance": True,
            "accessible_toilet": True, "elevator": True,
            "blind": True, "braille_signs": True, "audio_guide": True,
            "deaf": True, "induction_loop": True, "visual_alerts": True,
            "notes": "Полностью адаптирована для всех нозологий, сурдопереводчик по записи"
        }
    },
    {
        "name": "Кофе Хауз — Невский пр.",
        "address": "Невский пр., 30, Санкт-Петербург",
        "lat": 59.9354, "lon": 30.3274,
        "chain_index": 4,
        "category": CategoryEnum.cafe,
        "phone": "+7 812 315-00-00",
        "accessibility": {
            "wheelchair": False, "accessible_entrance": False,
            "accessible_toilet": False, "elevator": False,
            "blind": False, "braille_signs": False, "audio_guide": False,
            "deaf": False, "induction_loop": False, "visual_alerts": False,
            "notes": "Подвальное помещение, лестница без пандуса"
        }
    },
    {
        "name": "Кофе Хауз — Садовая ул.",
        "address": "Садовая ул., 42, Санкт-Петербург",
        "lat": 59.9260, "lon": 30.3199,
        "chain_index": 4,
        "category": CategoryEnum.cafe,
        "phone": "+7 812 315-00-01",
        "accessibility": {
            "wheelchair": True, "accessible_entrance": True,
            "accessible_toilet": True, "elevator": False,
            "blind": False, "braille_signs": False, "audio_guide": False,
            "deaf": False, "induction_loop": False, "visual_alerts": False,
            "notes": "Первый этаж, пандус у входа, доступный туалет"
        }
    },
    {
        "name": "ТРК Галерея",
        "address": "Лиговский пр., 30А, Санкт-Петербург",
        "lat": 59.9268, "lon": 30.3597,
        "chain_index": 5,
        "category": CategoryEnum.mall,
        "phone": "+7 812 458-00-00",
        "accessibility": {
            "wheelchair": True, "accessible_entrance": True,
            "accessible_toilet": True, "elevator": True,
            "blind": True, "braille_signs": False, "audio_guide": False,
            "deaf": True, "induction_loop": False, "visual_alerts": True,
            "notes": "Лифты на все этажи, специальные туалеты, коляски в аренду"
        }
    },
    {
        "name": "МФЦ Санкт-Петербург — Московский р-н",
        "address": "Варшавская ул., 43к2, Санкт-Петербург",
        "lat": 59.8819, "lon": 30.3148,
        "chain_index": 6,
        "category": CategoryEnum.government,
        "phone": "+7 812 573-90-00",
        "accessibility": {
            "wheelchair": True, "accessible_entrance": True,
            "accessible_toilet": True, "elevator": True,
            "blind": True, "braille_signs": True, "audio_guide": False,
            "deaf": True, "induction_loop": True, "visual_alerts": True,
            "notes": "Сурдопереводчик, тактильные указатели, индукционная петля"
        }
    },
    {
        "name": "Park Inn Прибалтийская",
        "address": "Кораблестроителей ул., 14, Санкт-Петербург",
        "lat": 59.9619, "lon": 30.2150,
        "chain_index": 8,
        "category": CategoryEnum.hotel,
        "phone": "+7 812 329-26-26",
        "accessibility": {
            "wheelchair": True, "accessible_entrance": True,
            "accessible_toilet": True, "elevator": True,
            "blind": False, "braille_signs": False, "audio_guide": False,
            "deaf": True, "induction_loop": False, "visual_alerts": True,
            "notes": "Номера для инвалидов, широкие коридоры, световые оповещения"
        }
    },
]

async def seed():
    async with AsyncSession() as session:
        print("Очищаем таблицы...")
        from sqlalchemy import text
        await session.execute(text("DELETE FROM accessibility"))
        await session.execute(text("DELETE FROM places"))
        await session.execute(text("DELETE FROM chains"))
        await session.commit()

        print("Добавляем сети...")
        chains = []
        for data in CHAINS_DATA:
            chain = Chain(**data)
            session.add(chain)
            chains.append(chain)
        await session.flush()

        print("Добавляем места и доступность...")
        for place_data in PLACES_DATA:
            acc_data = place_data.pop("accessibility")
            chain_index = place_data.pop("chain_index")
            place = Place(**place_data, chain_id=chains[chain_index].id)
            session.add(place)
            await session.flush()
            acc = Accessibility(place_id=place.id, **acc_data)
            session.add(acc)

        await session.commit()
        print("✅ Готово! Данные успешно загружены.")

        from sqlalchemy import select
        result = await session.execute(
            select(Place.name, Place.address, Accessibility.wheelchair,
                   Accessibility.blind, Accessibility.deaf)
            .join(Accessibility, Place.id == Accessibility.place_id)
        )
        rows = result.all()
        print(f"\n{'Название':<42} {'Адрес':<38} {'Коляска':^8} {'Слеп':^6} {'Глух':^6}")
        print("-" * 105)
        for row in rows:
            print(
                f"{row[0]:<42} {row[1]:<38} "
                f"{'✓' if row[2] else '✗':^8} "
                f"{'✓' if row[3] else '✗':^6} "
                f"{'✓' if row[4] else '✗':^6}"
            )

if __name__ == "__main__":
    asyncio.run(seed())