import asyncio
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from sqlalchemy import select, update, func, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from db.models import Chain, Place, CategoryEnum

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine       = create_async_engine(DATABASE_URL, echo=False)
AsyncSession = async_sessionmaker(bind=engine, expire_on_commit=False)

def clean_name(name: str) -> str:
    name = name.strip().lower()
    prefixes = [
        "аптека ", "магазин ", "салон ", "кафе ", "ресторан ",
        "клиника ", "центр ", "отделение ", "офис ", "гипермаркет ",
        "супермаркет ", "студия ", "парикмахерская ", "сервис ",
        "фитнес ", "спортивный клуб ", "фитнес-клуб ",
    ]
    for prefix in prefixes:
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    return name.strip()

def extract_base_name(name: str) -> str:
    original = name.strip()
    separators = [" — ", " - ", " №", " #", " (", ",", " на ", " у ", " в "]
    result = original
    for sep in separators:
        if sep in result:
            result = result[:result.index(sep)]
    result = re.sub(r'\s*\d+$', '', result).strip()
    if len(result) < 2:
        result = original
    return result.strip()

async def main():
    print("=" * 60)
    print("  Автоматическое создание сетей для всех организаций")
    print("=" * 60)
    print()

    async with AsyncSession() as session:
        result = await session.execute(
            select(Place.id, Place.name, Place.category)
            .where(Place.chain_id == None)
            .order_by(Place.name)
        )
        places_without_chain = result.all()
        print(f"  Мест без chain_id: {len(places_without_chain)}")

        groups: dict[tuple, list[int]] = {}
        name_map: dict[tuple, str] = {}

        for place_id, name, category in places_without_chain:
            base = extract_base_name(name)
            key = (base.lower(), category)
            if key not in groups:
                groups[key] = []
                name_map[key] = base
            groups[key].append(place_id)

        chains_to_create = {k: v for k, v in groups.items() if len(v) >= 2}
        singles = {k: v for k, v in groups.items() if len(v) == 1}

        print(f"  Найдено сетей (2+ филиала): {len(chains_to_create)}")
        print(f"  Одиночных заведений (без сети): {len(singles)}")
        print()

        created = 0
        updated_places = 0

        for (base_lower, category), place_ids in chains_to_create.items():
            canonical_name = name_map[(base_lower, category)]

            existing = await session.execute(
                select(Chain).where(
                    func.lower(Chain.name) == base_lower,
                    Chain.category == category
                )
            )
            chain = existing.scalar_one_or_none()

            if not chain:
                chain = Chain(name=canonical_name, category=category)
                session.add(chain)
                await session.flush()
                created += 1

            await session.execute(
                update(Place)
                .where(Place.id.in_(place_ids))
                .values(chain_id=chain.id)
            )
            updated_places += len(place_ids)

            print(f"  ✅ {canonical_name:<35} {len(place_ids):>3} филиала(ов)  →  chain_id={chain.id}")

        await session.commit()

        total_with_chain = await session.execute(
            select(func.count(Place.id)).where(Place.chain_id != None)
        )
        total_without_chain = await session.execute(
            select(func.count(Place.id)).where(Place.chain_id == None)
        )

        print()
        print("=" * 60)
        print(f"  ✅ Готово!")
        print(f"  Создано новых сетей:          {created}")
        print(f"  Обновлено мест (добавлен chain_id): {updated_places}")
        print(f"  Мест с chain_id (итого):      {total_with_chain.scalar()}")
        print(f"  Мест без chain_id (одиночные): {total_without_chain.scalar()}")
        print("=" * 60)
        print()
        print("  Теперь кнопка 'Другой филиал этой сети'")
        print("  будет работать для всех сетей в базе.")
        print()
        print("  Перезапусти бота: python main.py")

if __name__ == "__main__":
    asyncio.run(main())