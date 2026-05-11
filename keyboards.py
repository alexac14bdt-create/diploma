from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🔍 Новый поиск"),
                KeyboardButton(text="♿ Сменить нозологию"),
            ]
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Выбери действие или введи текст...",
    )


def nosology_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="♿ Колясочник",      callback_data="nosology:wheelchair")],
        [InlineKeyboardButton(text="👁 Слабовидящий",   callback_data="nosology:blind")],
        [InlineKeyboardButton(text="👂 Слабослышащий",  callback_data="nosology:deaf")],
    ])


def alternatives_keyboard(chain_id: int, category: str, lat: float, lon: float) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🏢 Другой филиал этой сети",
            callback_data=f"alt:chain:{chain_id}:{category}:{lat}:{lon}"
        )],
        [InlineKeyboardButton(
            text="📍 Любое ближайшее подходящее место",
            callback_data=f"alt:any:{chain_id}:{category}:{lat}:{lon}"
        )],
    ])


def route_keyboard(dest_lat: float, dest_lon: float, place_name: str) -> InlineKeyboardMarkup:
    yandex_url = f"https://yandex.ru/maps/?rtext=~{dest_lat},{dest_lon}&rtt=pd"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🗺 Построить маршрут в Яндекс.Картах",
            url=yandex_url
        )],
    ])


def new_search_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Попробовать снова", callback_data="new_search")],
    ])


def places_list_keyboard(places: list) -> InlineKeyboardMarkup:
    buttons = []
    for p in places:
        dist = f"{p['distance_km']:.1f} км"
        buttons.append([InlineKeyboardButton(
            text=f"📍 {p['name']} — {dist}",
            callback_data=f"show_route:{p['lat']}:{p['lon']}:{p['id']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)