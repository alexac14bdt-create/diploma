from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db.base import AsyncSessionLocal
from services.recommender import (
    get_or_create_user, save_nosology, get_user_nosology,
    find_place, is_adapted, find_nearest_same_chain,
    find_nearest_any, format_place_card,
    normalize_address, find_nearest_by_name, geocode_address
)
from bot.keyboards import (
    nosology_keyboard, alternatives_keyboard,
    route_keyboard, new_search_keyboard, places_list_keyboard,
    main_menu_keyboard
)

router = Router()


class SearchStates(StatesGroup):
    waiting_name = State()
    waiting_address = State()


async def start_new_search(message: Message, state: FSMContext, nosology: str | None):
    if not nosology:
        await message.answer(
            "Сначала выбери нозологию:",
            reply_markup=nosology_keyboard()
        )
        return

    await state.set_state(SearchStates.waiting_name)
    nosology_names = {
        "wheelchair": "Колясочник ♿",
        "blind":      "Слабовидящий 👁",
        "deaf":       "Слабослышащий 👂",
    }
    await message.answer(
        f"Нозология: <b>{nosology_names.get(nosology, nosology)}</b>\n\n"
        f"Введи <b>название</b> организации.\n"
        f"Например: <i>Сбербанк</i>, <i>Сбер</i>, <i>Аптека Невис</i>",
        parse_mode="HTML"
    )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    async with AsyncSessionLocal() as session:
        await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            username=message.from_user.username
        )

    await message.answer(
        "👋 Привет! Я помогу найти доступные места в Санкт-Петербурге.\n\n"
        "Кнопки <b>«🔍 Новый поиск»</b> и <b>«♿ Сменить нозологию»</b> "
        "всегда доступны над клавиатурой.\n\n"
        "Сначала выбери свою нозологию 👇",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )
    

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "ℹ️ <b>Как пользоваться ботом:</b>\n\n"
        "1️⃣ Нажми <b>«♿ Сменить нозологию»</b> и выбери свою\n"
        "2️⃣ Нажми <b>«🔍 Новый поиск»</b>\n"
        "3️⃣ Введи название организации\n"
        "   (можно сокращённо: <i>Сбер</i>, <i>Пятёрка</i>)\n"
        "4️⃣ Введи адрес в любом формате:\n"
        "   <i>Невский 45</i> или <i>Невский проспект, 45</i>\n"
        "5️⃣ Бот проверит адаптацию и предложит маршрут\n\n"
        "📋 <b>Команды:</b>\n"
        "/search — начать поиск\n"
        "/nosology — сменить нозологию\n"
        "/start — главное меню\n"
        "/help — эта справка",
        parse_mode="HTML"
    )


@router.message(Command("nosology"))
async def cmd_nosology(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Выбери нозологию:", reply_markup=nosology_keyboard())


@router.message(Command("search"))
async def cmd_search(message: Message, state: FSMContext):
    async with AsyncSessionLocal() as session:
        nosology = await get_user_nosology(session, message.from_user.id)
    await start_new_search(message, state, nosology)


@router.message(F.text == "🔍 Новый поиск")
async def menu_new_search(message: Message, state: FSMContext):
    await state.clear()
    async with AsyncSessionLocal() as session:
        nosology = await get_user_nosology(session, message.from_user.id)
    await start_new_search(message, state, nosology)


@router.message(F.text == "♿ Сменить нозологию")
async def menu_change_nosology(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Выбери нозологию:", reply_markup=nosology_keyboard())


@router.callback_query(F.data.startswith("nosology:"))
async def cb_nosology(callback: CallbackQuery, state: FSMContext):
    nosology = callback.data.split(":")[1]

    async with AsyncSessionLocal() as session:
        await get_or_create_user(
            session,
            telegram_id=callback.from_user.id,
            username=callback.from_user.username
        )
        await save_nosology(session, callback.from_user.id, nosology)

    nosology_names = {
        "wheelchair": "Колясочник ♿",
        "blind":      "Слабовидящий 👁",
        "deaf":       "Слабослышащий 👂",
    }
    await callback.message.edit_text(
        f"✅ Нозология сохранена: <b>{nosology_names[nosology]}</b>",
        parse_mode="HTML"
    )
    await state.set_state(SearchStates.waiting_name)
    await callback.message.answer(
        "Введи <b>название</b> организации.\n"
        "Например: <i>Сбербанк</i>, <i>Сбер</i>, <i>Аптека Невис</i>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "new_search")
async def cb_new_search(callback: CallbackQuery, state: FSMContext):
    async with AsyncSessionLocal() as session:
        nosology = await get_user_nosology(session, callback.from_user.id)

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await start_new_search(callback.message, state, nosology)
    await callback.answer()


@router.callback_query(F.data == "change_nosology")
async def cb_change_nosology(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(
        "Выбери нозологию:",
        reply_markup=nosology_keyboard()
    )
    await callback.answer()


@router.message(SearchStates.waiting_name)
async def got_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("Название слишком короткое. Попробуй ещё раз:")
        return

    await state.update_data(org_name=name)
    await state.set_state(SearchStates.waiting_address)
    await message.answer(
        f"🏢 Ищем: <b>{name}</b>\n\n"
        f"Введи <b>адрес</b> — улицу и номер дома.\n"
        f"Можно в любом формате:\n"
        f"• <i>Невский 45</i>\n"
        f"• <i>Невский проспект, 45</i>\n"
        f"• <i>Невский пр. 45</i>",
        parse_mode="HTML"
    )


@router.message(SearchStates.waiting_address)
async def got_address(message: Message, state: FSMContext):
    address = message.text.strip()
    if len(address) < 2:
        await message.answer("Адрес слишком короткий. Попробуй ещё раз:")
        return

    data = await state.get_data()
    org_name = data.get("org_name", "")
    await state.clear()

    searching_msg = await message.answer("🔍 Ищу в базе данных...")

    async with AsyncSessionLocal() as session:
        nosology = await get_user_nosology(session, message.from_user.id)

        if not nosology:
            await searching_msg.edit_text(
                "❗ Сначала выбери нозологию:",
                reply_markup=nosology_keyboard()
            )
            return

        place = await find_place(session, org_name, address)

        if not place:
            async with AsyncSessionLocal() as session2:
                nosology2 = await get_user_nosology(session2, message.from_user.id)
                user_lat, user_lon = await geocode_address(address)
                nearby = []
                if user_lat and user_lon:
                    nearby = await find_nearest_by_name(
                        session2, org_name, nosology2, user_lat, user_lon, limit=3
                    )

            if nearby:
                text = (
                    f"😔 Не нашёл <b>{org_name}</b> по адресу <b>{address}</b> в базе.\n\n"
                    f"Но нашёл ближайшие <b>{org_name}</b> рядом:\n\n"
                )
                for i, p in enumerate(nearby, 1):
                    text += f"{i}. <b>{p['name']}</b>\n   {p['address']}\n   📏 {p['distance_km']:.1f} км\n\n"
                text += "Нажми на место, чтобы построить маршрут:"
                await searching_msg.edit_text(
                    text, parse_mode="HTML",
                    reply_markup=places_list_keyboard(nearby)
                )
            else:
                await searching_msg.edit_text(
                    f"😔 Не нашёл <b>{org_name}</b> по адресу <b>{address}</b> в базе.\n\n"
                    f"<b>Советы:</b>\n"
                    f"• Проверь адрес — возможно номер дома другой\n"
                    f"• Сократи название: <i>Сбербанк</i> → <i>Сбер</i>\n"
                    f"• Убедись, что место добавлено в базу",
                    parse_mode="HTML",
                    reply_markup=new_search_keyboard()
                )
            return

        adapted = is_adapted(place, nosology)
        card_text = format_place_card(place, nosology, adapted)

        if adapted:
            await searching_msg.edit_text(
                card_text,
                parse_mode="HTML",
                reply_markup=route_keyboard(place["lat"], place["lon"], place["name"])
            )
        else:
            await searching_msg.edit_text(
                card_text + "\n\n⬇️ Что хочешь найти вместо этого?",
                parse_mode="HTML",
                reply_markup=alternatives_keyboard(
                    chain_id=place["chain_id"] or 0,
                    category=place["category"],
                    lat=place["lat"],
                    lon=place["lon"]
                )
            )


@router.callback_query(F.data.startswith("alt:"))
async def cb_alternatives(callback: CallbackQuery):
    parts    = callback.data.split(":")
    alt_type = parts[1]
    chain_id = int(parts[2])
    category = parts[3]
    lat      = float(parts[4])
    lon      = float(parts[5])

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    searching_msg = await callback.message.answer("🔍 Ищу альтернативы...")

    async with AsyncSessionLocal() as session:
        nosology = await get_user_nosology(session, callback.from_user.id)

    from services.graph_recommender import accessibility_graph

    graph_ready = accessibility_graph._built

    if graph_ready:
        if alt_type == "chain" and chain_id > 0:
            places = accessibility_graph.find_nearest_same_chain(
                user_lat=lat, user_lon=lon,
                chain_id=chain_id, nosology=nosology, limit=3
            )
            header = "🏢 Ближайшие адаптированные филиалы этой сети:"
        else:
            places = accessibility_graph.find_nearest_adapted(
                user_lat=lat, user_lon=lon,
                category=category, nosology=nosology, limit=3
            )
            category_names = {
                "cafe":        "кафе",
                "pharmacy":    "аптеки",
                "bank":        "банки",
                "clinic":      "клиники",
                "supermarket": "супермаркеты",
                "mall":        "торговые центры",
                "government":  "госучреждения",
                "sport":       "спортивные объекты",
                "hotel":       "гостиницы",
                "transport":   "автосервисы",
            }
            header = f"📍 Ближайшие адаптированные {category_names.get(category, 'места')}:"
    else:
        async with AsyncSessionLocal() as session:
            if alt_type == "chain" and chain_id > 0:
                places = await find_nearest_same_chain(
                    session=session, chain_id=chain_id, nosology=nosology,
                    user_lat=lat, user_lon=lon, exclude_place_id=0, limit=3
                )
                header = "🏢 Ближайшие адаптированные филиалы этой сети:"
            else:
                places = await find_nearest_any(
                    session=session, category=category, nosology=nosology,
                    user_lat=lat, user_lon=lon, exclude_place_id=0, limit=3
                )
                header = "📍 Ближайшие адаптированные места:"

    if not places:
        await searching_msg.edit_text(
            "😔 Подходящих альтернатив в базе не нашлось.",
            reply_markup=new_search_keyboard()
        )
        await callback.answer()
        return

    nosology_labels = {
        "wheelchair": "колясочников ♿",
        "blind":      "слабовидящих 👁",
        "deaf":       "слабослышащих 👂",
    }
    text = (
        f"{header}\n"
        f"<i>(адаптированы для {nosology_labels.get(nosology, nosology)})</i>\n\n"
    )
    for i, p in enumerate(places, 1):
        text += f"{i}. <b>{p['name']}</b>\n   {p['address']}\n   📏 {p['distance_km']:.1f} км\n\n"
    text += "Нажми на место, чтобы построить маршрут:"

    await searching_msg.edit_text(
        text, parse_mode="HTML", reply_markup=places_list_keyboard(places)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("show_route:"))
async def cb_show_route(callback: CallbackQuery):
    parts    = callback.data.split(":")
    dest_lat = float(parts[1])
    dest_lon = float(parts[2])
    place_id = int(parts[3])

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        from db.models import Place, Accessibility, Chain
        result = await session.execute(
            select(Place, Accessibility, Chain)
            .join(Accessibility, Place.id == Accessibility.place_id)
            .outerjoin(Chain, Place.chain_id == Chain.id)
            .where(Place.id == place_id)
        )
        row = result.first()

    if not row:
        await callback.answer("Место не найдено", show_alert=True)
        return

    place_obj, acc_obj, _ = row

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    text = (
        f"🏢 <b>{place_obj.name}</b>\n"
        f"📮 {place_obj.address}\n"
        f"📞 {place_obj.phone or 'не указан'}\n"
    )
    if acc_obj.notes:
        text += f"\n💬 {acc_obj.notes}\n"

    await callback.message.answer(
        text, parse_mode="HTML",
        reply_markup=route_keyboard(dest_lat, dest_lon, place_obj.name)
    )
    await callback.answer()