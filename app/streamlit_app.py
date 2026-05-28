import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lib.imports import *

import hashlib
import html
import json
import base64
import importlib
import re
import urllib.parse

import streamlit as st
try:
    from pymongo import MongoClient
    from pymongo.errors import DuplicateKeyError, PyMongoError
except ModuleNotFoundError:
    MongoClient = None
    DuplicateKeyError = PyMongoError = Exception

import models.content_based as content_based
from models.content_based import (
  build_content_index,
  get_content_recommendations,
  search_by_description,
  expand_query_text,
  extract_query_intents,
  get_hard_negative_terms,
)
import utils.preprocessing as movie_preprocessing


APP_MOVIE_CATALOG_CACHE_VERSION = 12001
AI_CHAT_LOGIC_VERSION = "genre-exclude-v2"


@st.cache_data(show_spinner=False)
def get_movies(catalog_version: int = APP_MOVIE_CATALOG_CACHE_VERSION) -> pd.DataFrame:
    importlib.reload(movie_preprocessing)
    return movie_preprocessing.load_movies()


@st.cache_resource(show_spinner=False)
def get_similarity(movies: pd.DataFrame):
    importlib.reload(content_based)
    return content_based.build_content_index(movies)


TITLE_UA_MAP = {
    "Inception": "Початок",
    "Interstellar": "Інтерстеллар",
    "The Dark Knight": "Темний лицар",
    "The Dark Knight Rises": "Темний лицар: Відродження легенди",
    "Avatar": "Аватар",
    "The Avengers": "Месники",
    "Joker": "Джокер",
}

TITLE_UA_MAP.update({
    "Avatar": "Аватар",
    "Avatar: The Way of Water": "Аватар: Шлях води",
    "Barbie": "Барбі",
    "Dune": "Дюна",
    "Dune: Part Two": "Дюна: Частина друга",
    "Elemental": "Стихії",
    "Fast X": "Форсаж 10",
    "Gran Turismo": "Ґран Турізмо",
    "Guardians of the Galaxy Vol. 3": "Вартові Галактики 3",
    "Inception": "Початок",
    "Inside Out 2": "Думками навиворіт 2",
    "Interstellar": "Інтерстеллар",
    "John Wick: Chapter 4": "Джон Вік 4",
    "Joker": "Джокер",
    "Meg 2: The Trench": "Мег 2: Западина",
    "Oppenheimer": "Оппенгеймер",
    "Saw X": "Пила X",
    "Spider-Man: Across the Spider-Verse": "Людина-павук: Крізь Всесвіт",
    "The Avengers": "Месники",
    "The Dark Knight": "Темний лицар",
    "The Dark Knight Rises": "Темний лицар повертається",
    "The Super Mario Bros. Movie": "Брати Супер Маріо в кіно",
})

OVERVIEW_UA_MAP = {
    "Avatar": "Колишній морський піхотинець Джейк Саллі потрапляє на Пандору, де знайомиться з народом на'ві та опиняється між наказами людей і новим світом, який стає для нього домом.",
    "Avatar: The Way of Water": "Джейк Саллі живе з новою родиною на Пандорі, але стара загроза повертається. Щоб захистити близьких, він вирушає до океанічного клану й відкриває інший бік планети.",
    "Barbie": "Барбі та Кен насолоджуються життям у яскравому й нібито ідеальному Барбіленді. Але коли вони отримують шанс потрапити у реальний світ, то швидко відкривають для себе радощі й небезпеки життя серед людей.",
    "Dune": "Пол Атрідас разом із родиною прибуває на небезпечну планету Арракіс, де видобувають найціннішу речовину у Всесвіті. Полу доведеться прийняти спадок, силу й випробування пустелі.",
    "Dune: Part Two": "Пол Атрідас об'єднується з фременами та вирушає шляхом помсти проти тих, хто знищив його родину. Перед ним постає вибір між коханням, долею і майбутнім цілого Всесвіту.",
    "Elemental": "У місті, де разом живуть мешканці вогню, води, землі й повітря, запальна дівчина та спокійний хлопець відкривають, що мають набагато більше спільного, ніж здається.",
    "Fast X": "Дом Торетто та його родина знову стикаються з небезпекою. Цього разу проти них виступає ворог із минулого, який прагне помсти й хоче зруйнувати все, що Дом любить.",
    "Gran Turismo": "Підліток, який майстерно грає в Gran Turismo, отримує шанс перетворити навички з гри на справжню кар'єру професійного автогонщика.",
    "Guardians of the Galaxy Vol. 3": "Вартові Галактики вирушають на небезпечну місію, щоб урятувати одного зі своїх і нарешті зіткнутися з болючими таємницями минулого Ракети.",
    "Inception": "Дом Кобб уміє проникати у сни та викрадати секрети з підсвідомості. Йому пропонують останню справу: не вкрасти ідею, а навпаки, підсадити її.",
    "Inside Out 2": "Райлі дорослішає, а в її голові з'являються нові емоції. Радість, Сум, Гнів, Страх і Відраза мають навчитися жити поруч із Тривожністю та іншими несподіваними почуттями.",
    "Interstellar": "Коли Земля стає непридатною для життя, група дослідників вирушає крізь космічну червоточину, щоб знайти новий дім для людства.",
    "John Wick: Chapter 4": "Джон Вік знаходить шлях до перемоги над Високим столом, але перед свободою йому доведеться пройти через нових ворогів і старі борги.",
    "Joker": "Артур Флек, самотній комік із Готема, поступово втрачає віру в суспільство, яке його відкидає, і перетворюється на символ хаосу.",
    "Meg 2: The Trench": "Дослідницька команда занурюється у найглибші частини океану, де стикається з доісторичними хижаками та небезпеками, що вириваються на поверхню.",
    "Oppenheimer": "Історія фізика Роберта Оппенгеймера, його роботи над створенням атомної бомби та моральної ціни відкриття, яке змінило світ.",
    "Saw X": "Джон Крамер вирушає на експериментальне лікування, але стає жертвою шахрайства. Тоді він повертає контроль у знайомий спосіб: через жорстокі випробування.",
    "Spider-Man: Across the Spider-Verse": "Майлз Моралес подорожує мультивсесвітом і зустрічає безліч Людей-павуків, але швидко розуміє, що навіть герої можуть мати різне бачення правильного вибору.",
    "The Avengers": "Найсильніші герої Землі об'єднуються, щоб зупинити загрозу, з якою ніхто з них не впорається самотужки.",
    "The Dark Knight": "Бетмен, Ґордон і Гарві Дент намагаються очистити Ґотем від злочинності, але поява Джокера перетворює місто на поле хаосу.",
    "The Dark Knight Rises": "Після років тиші Брюс Вейн змушений знову стати Бетменом, коли Ґотему загрожує безжальний Бейн.",
    "The Super Mario Bros. Movie": "Брати Маріо потрапляють у чарівний світ, де їм доведеться допомогти принцесі Піч зупинити Боузера й урятувати королівство.",
}

TITLE_UA_MAP.update({
    "A Haunting in Venice": "Привиди у Венеції",
    "A Million Miles Away": "За мільйон миль",
    "Ant-Man and the Wasp: Quantumania": "Людина-мураха та Оса: Квантоманія",
    "Avengers: Infinity War": "Месники: Війна нескінченності",
    "Blue Beetle": "Синій Жук",
    "Cobweb": "Павутиння",
    "Coco": "Коко",
    "Creed III": "Крід III",
    "Encanto": "Енканто",
    "Evil Dead Rise": "Повстання зловісних мерців",
    "Extraction 2": "Евакуація 2",
    "Guy Ritchie's The Covenant": "Перекладач",
    "Harry Potter and the Philosopher's Stone": "Гаррі Поттер і філософський камінь",
    "Heart of Stone": "Кам'яне серце",
    "Hidden Strike": "Прихований удар",
    "Hypnotic": "Гіпнотик",
    "Indiana Jones and the Dial of Destiny": "Індіана Джонс і реліквія долі",
    "Insidious: The Red Door": "Астрал: Червоні двері",
    "Kandahar": "Кандагар",
    "Knights of the Zodiac": "Лицарі Зодіаку",
    "Mavka: The Forest Song": "Мавка. Лісова пісня",
    "Miraculous: Ladybug & Cat Noir, the Movie": "Леді Баг і Супер-Кіт: Фільм",
    "Mission: Impossible - Dead Reckoning Part One": "Місія неможлива: Розплата. Частина перша",
    "Mortal Kombat Legends: Scorpion's Revenge": "Легенди Мортал Комбат: Помста Скорпіона",
    "My Fault": "Моя провина",
    "No Hard Feelings": "Без образ",
    "No One Will Save You": "Ніхто тебе не врятує",
    "One Piece Film Red": "Ван-Піс Фільм: Червоний",
    "PAW Patrol: The Mighty Movie": "Щенячий патруль: Мегакіно",
    "PAW Patrol: The Movie": "Щенячий патруль у кіно",
    "Prey": "Здобич",
    "Puss in Boots: The Last Wish": "Кіт у чоботях 2: Останнє бажання",
    "Red Dawn": "Червоний світанок",
    "Resident Evil: Death Island": "Оселя зла: Острів смерті",
    "Ruby Gillman, Teenage Kraken": "Рубі Ґіллман, підліток-кракен",
    "San Andreas": "Розлом Сан-Андреас",
    "Scream VI": "Крик VI",
    "Shazam! Fury of the Gods": "Шазам! Лють богів",
    "Sisu": "Сісу",
    "Sonic the Hedgehog 2": "Їжак Сонік 2",
    "Sound of Freedom": "Звук свободи",
    "Spider-Man: No Way Home": "Людина-павук: Додому шляху нема",
    "Spiral: From the Book of Saw": "Спіраль: Спадок Пили",
    "Spy Kids: Armageddon": "Діти шпигунів: Армагеддон",
    "Strays": "Бродяги",
    "Suzume": "Судзуме",
    "Talk to Me": "Поговори зі мною",
    "Teenage Mutant Ninja Turtles: Mutant Mayhem": "Підлітки-мутанти Черепашки-ніндзя: Погром мутантів",
    "The Boogeyman": "Бабай",
    "The Conjuring: The Devil Made Me Do It": "Закляття 3: За велінням диявола",
    "The Equalizer": "Праведник",
    "The Equalizer 3": "Праведник 3",
    "The Flash": "Флеш",
    "The Godfather": "Хрещений батько",
    "The Last Voyage of the Demeter": "Остання подорож Деметри",
    "The Little Mermaid": "Русалонька",
    "The Nun": "Прокляття монахині",
    "The Nun II": "Прокляття монахині 2",
    "The Pope's Exorcist": "Екзорцист Ватикану",
    "Transformers: Rise of the Beasts": "Трансформери: Час Звіроботів",
    "Zom 100: Bucket List of the Dead": "Зом 100: Список бажань мерця",
})

OVERVIEW_UA_MAP.update({
    "A Haunting in Venice": "Еркюль Пуаро після відставки потрапляє на спіритичний сеанс у Венеції, де загадкова смерть змушує його знову взятися за розслідування.",
    "A Million Miles Away": "Історія Хосе Ернандеса, який пройшов шлях від роботи на полях до мрії стати астронавтом NASA.",
    "Blue Beetle": "Молодий Хайме Рейєс випадково отримує інопланетний артефакт, що дарує йому потужний костюм і змінює життя всієї його родини.",
    "Cobweb": "Хлопчик чує дивні звуки у стінах свого будинку й поступово розуміє, що батьки приховують від нього моторошну таємницю.",
    "Evil Dead Rise": "Дві сестри стикаються з давнім злом, яке пробуджується у багатоповерхівці та перетворює сімейну зустріч на ніч виживання.",
    "Extraction 2": "Тайлер Рейк повертається після майже смертельної місії та береться за нове завдання: врятувати родину з небезпечної в'язниці.",
    "Fast X": "Дом Торетто та його родина стикаються з ворогом із минулого, який хоче помститися й знищити все, що для них важливе.",
    "Guy Ritchie's The Covenant": "Американський військовий намагається повернути борг афганському перекладачу, який урятував йому життя під час небезпечної операції.",
    "Heart of Stone": "Агентка секретної організації мусить захистити потужну технологію, здатну змінити баланс сил у світі.",
    "Indiana Jones and the Dial of Destiny": "Індіана Джонс вирушає в останню велику пригоду, пов'язану з давнім артефактом, який може змінити хід історії.",
    "Insidious: The Red Door": "Родина Ламбертів знову стикається з темним світом, коли старі страхи повертаються через двері, які мали залишитися зачиненими.",
    "Kandahar": "Агент ЦРУ після проваленої місії мусить прорватися через ворожу територію до точки евакуації.",
    "Mavka: The Forest Song": "Мавка, душа лісу, закохується в людину й мусить обрати між почуттями та обов'язком захищати свій світ.",
    "Mission: Impossible - Dead Reckoning Part One": "Ітан Гант і його команда полюють на небезпечну технологію, яка може потрапити до рук ворогів і змінити майбутнє світу.",
    "My Fault": "Молода дівчина переїжджає до нового дому матері й несподівано зближується зі зведеним братом, попри всі заборони й небезпеки.",
    "No Hard Feelings": "Жінка з фінансовими проблемами погоджується на незвичну роботу: допомогти сором'язливому хлопцю стати впевненішим перед коледжем.",
    "No One Will Save You": "Самотня дівчина мусить захищати дім від неземної загрози, коли навколо не залишається нікого, хто міг би допомогти.",
    "PAW Patrol: The Mighty Movie": "Щенячий патруль отримує суперсили після падіння магічного метеорита й мусить зупинити нову загрозу для міста.",
    "Puss in Boots: The Last Wish": "Кіт у чоботях дізнається, що витратив майже всі свої життя, і вирушає на пошуки чарівного бажання.",
    "Ruby Gillman, Teenage Kraken": "Сором'язлива школярка дізнається, що належить до давнього роду морських кракенів, і відкриває свою справжню силу.",
    "Scream VI": "Ті, хто вижив після попередніх нападів, переїжджають до Нью-Йорка, але привид у масці знову починає полювання.",
    "Sound of Freedom": "Колишній урядовий агент вирушає на небезпечну місію, щоб урятувати дітей від торгівлі людьми.",
    "Spider-Man: No Way Home": "Після розкриття особи Пітера Паркера магічне заклинання відкриває двері мультивсесвіту й приводить нових ворогів.",
    "Strays": "Домашній пес, якого покинув господар, об'єднується з вуличними собаками, щоб знайти себе й помститися.",
    "Talk to Me": "Група підлітків знаходить спосіб викликати духів через загадкову руку, але гра швидко перетворюється на небезпечну залежність.",
    "The Boogeyman": "Після сімейної трагедії дві сестри стикаються з темною істотою, яка живиться страхом і ховається в темряві.",
    "The Equalizer 3": "Роберт МакКолл знаходить спокій в Італії, але коли місцевим людям загрожує мафія, він знову стає на захист слабших.",
    "The Flash": "Баррі Аллен змінює минуле, щоб урятувати родину, але його вчинок створює нову реальність із небезпечними наслідками.",
    "The Last Voyage of the Demeter": "Екіпаж торгового корабля перевозить таємничий вантаж, не підозрюючи, що на борту ховається смертельне зло.",
    "The Little Mermaid": "Молода русалка Аріель мріє про життя серед людей і укладає ризиковану угоду, щоб опинитися на поверхні.",
    "The Nun II": "Після нових загадкових смертей сестра Ірен знову стикається з демонічною монахинею Валак.",
    "The Pope's Exorcist": "Головний екзорцист Ватикану розслідує одержимість хлопчика й відкриває змову, яку церква приховувала століттями.",
    "Transformers: Rise of the Beasts": "Люди й автоботи об'єднуються з новими трансформерами, щоб зупинити космічну загрозу.",
})

GENRE_UA_MAP = {
    "Action": "Бойовик",
    "Adventure": "Пригоди",
    "Animation": "Анімація",
    "Anime": "Аніме",
    "Biography": "Біографія",
    "Comedy": "Комедія",
    "Crime": "Кримінал",
    "Documentary": "Документальний",
    "Drama": "Драма",
    "Family": "Сімейний",
    "Fantasy": "Фентезі",
    "History": "Історичний",
    "Horror": "Жахи",
    "Music": "Музичний",
    "Musical": "Мюзикл",
    "Mystery": "Детектив",
    "Romance": "Романтика",
    "Science Fiction": "Наукова фантастика",
    "Sci-Fi": "Наукова фантастика",
    "Sport": "Спорт",
    "Thriller": "Трилер",
    "War": "Війна",
    "Western": "Вестерн",
}

USER_STORE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "user_profiles.json"))
MONGO_URI = "mongodb://localhost:27018/"
MONGO_DB_NAME = "ai_movie_recommender"
MONGO_USERS_COLLECTION = "users"
AUTH_QUERY_PARAM = "auth_user"
LANG_QUERY_PARAM = "lang"
SUPPORTED_LANGS = {"UA", "EN"}
_mongo_users_collection = None


def normalize_username(username: str) -> str:
    return re.sub(r"\s+", " ", username.strip()).lower()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def load_legacy_user_store() -> dict:
    if not os.path.exists(USER_STORE_PATH):
        return {"users": {}}
    try:
        with open(USER_STORE_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        return {"users": {}}
    if not isinstance(data, dict) or "users" not in data or not isinstance(data["users"], dict):
        return {"users": {}}
    return data


def user_store_error() -> str:
    if MongoClient is None:
        return "Не встановлено pymongo. Виконайте: pip install -r requirements.txt"
    return "MongoDB недоступна. Перевірте, що сервер запущений на mongodb://localhost:27018/"


def migrate_legacy_users(collection: object) -> None:
    legacy_users = load_legacy_user_store().get("users", {})
    if not isinstance(legacy_users, dict) or not legacy_users:
        return
    for username, profile in legacy_users.items():
        if not isinstance(profile, dict):
            continue
        normalized = normalize_username(username)
        if not normalized:
            continue
        document = {
            "username": normalized,
            "display_name": profile.get("display_name") or username,
            "email": str(profile.get("email", "")).strip().lower(),
            "password_hash": profile.get("password_hash", ""),
            "watch_later": profile.get("watch_later", []) if isinstance(profile.get("watch_later", []), list) else [],
        }
        try:
            collection.update_one({"username": normalized}, {"$setOnInsert": document}, upsert=True)
        except PyMongoError:
            continue


def get_users_collection():
    global _mongo_users_collection
    if _mongo_users_collection is not None:
        return _mongo_users_collection
    if MongoClient is None:
        return None
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=1200)
        client.admin.command("ping")
        collection = client[MONGO_DB_NAME][MONGO_USERS_COLLECTION]
        collection.create_index("username", unique=True)
        collection.create_index("email", unique=True)
        migrate_legacy_users(collection)
        _mongo_users_collection = collection
        return collection
    except PyMongoError:
        return None
    return None


def get_current_user() -> Optional[str]:
    user = st.session_state.get("current_user")
    return str(user) if user else None


def first_query_value(value: object) -> str:
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value or "")


def get_user_profile(username: str) -> dict:
    collection = get_users_collection()
    if collection is None:
        return {}
    try:
        profile = collection.find_one({"username": normalize_username(username)}, {"_id": 0})
    except PyMongoError:
        return {}
    return profile or {}


def hydrate_current_user_from_query() -> None:
    if st.session_state.get("current_user"):
        return
    auth_user = normalize_username(first_query_value(st.query_params.get(AUTH_QUERY_PARAM)))
    if not auth_user:
        return
    if get_user_profile(auth_user):
        st.session_state["current_user"] = auth_user
    elif AUTH_QUERY_PARAM in st.query_params:
        del st.query_params[AUTH_QUERY_PARAM]


def set_current_user(username: str) -> None:
    normalized = normalize_username(username)
    st.session_state["current_user"] = normalized
    st.query_params[AUTH_QUERY_PARAM] = normalized


def clear_current_user() -> None:
    st.session_state["current_user"] = None
    if AUTH_QUERY_PARAM in st.query_params:
        del st.query_params[AUTH_QUERY_PARAM]


def auth_hidden_input() -> str:
    current_user = get_current_user()
    if not current_user:
        return ""
    return f'<input type="hidden" name="{AUTH_QUERY_PARAM}" value="{html.escape(current_user, quote=True)}" />'


def normalize_lang(value: object) -> str:
    lang = first_query_value(value).strip().upper()
    return lang if lang in SUPPORTED_LANGS else "UA"


def hydrate_lang_from_query() -> None:
    st.session_state["lang"] = normalize_lang(st.query_params.get(LANG_QUERY_PARAM) or st.session_state.get("lang", "UA"))
    st.query_params[LANG_QUERY_PARAM] = st.session_state["lang"]


def lang_hidden_input() -> str:
    return f'<input type="hidden" name="{LANG_QUERY_PARAM}" value="{html.escape(st.session_state.get("lang", "UA"), quote=True)}" />'


def query_href_with_updates(**updates: object) -> str:
    params = {name: value for name, value in st.query_params.items()}
    current_user = get_current_user()
    if current_user:
        params[AUTH_QUERY_PARAM] = current_user
    params[LANG_QUERY_PARAM] = st.session_state.get("lang", "UA")
    for name, value in updates.items():
        if value is None:
            params.pop(name, None)
        else:
            params[name] = value
    query = urllib.parse.urlencode(params)
    return f"?{query}" if query else "?"


def panel_switch_href(panel: str) -> str:
    resets = {
        "title": {
            "hero_panel": "title",
            "movie": None,
            "genre": None,
            "year_min": None,
            "year_max": None,
            "sort_by": None,
            "ai_message": None,
            "chat_memory": None,
        },
        "filters": {
            "hero_panel": "filters",
            "movie": None,
            "title_search": None,
            "ai_message": None,
            "chat_memory": None,
        },
        "ai": {
            "hero_panel": "ai",
            "movie": None,
            "title_search": None,
            "genre": None,
            "year_min": None,
            "year_max": None,
            "sort_by": None,
        },
    }
    return query_href_with_updates(**resets.get(panel, {"hero_panel": panel, "movie": None}))


def register_user(username: str, email: str, password: str, confirm_password: str) -> tuple[bool, str]:
    normalized = normalize_username(username)
    email = email.strip().lower()
    if len(normalized) < 3:
        return False, "Ім'я має містити щонайменше 3 символи."
    if "@" not in email or "." not in email:
        return False, "Введіть коректну електронну пошту."
    if len(password) < 6:
        return False, "Пароль має містити щонайменше 6 символів."
    if password != confirm_password:
        return False, "Паролі не збігаються."

    collection = get_users_collection()
    if collection is None:
        return False, user_store_error()
    try:
        existing = collection.find_one({"$or": [{"username": normalized}, {"email": email}]})
    except PyMongoError:
        return False, user_store_error()
    if existing and existing.get("username") == normalized:
        return False, "Такий користувач уже існує."
    if existing and existing.get("email") == email:
        return False, "Користувач із такою поштою вже існує."

    try:
        collection.insert_one(
            {
                "username": normalized,
                "display_name": username.strip(),
                "email": email,
                "password_hash": hash_password(password),
                "watch_later": [],
            }
        )
    except DuplicateKeyError:
        return False, "Користувач із такими даними вже існує."
    except PyMongoError:
        return False, user_store_error()
    return True, normalized


def login_user(identifier: str, password: str) -> tuple[bool, str]:
    normalized = normalize_username(identifier)
    collection = get_users_collection()
    if collection is None:
        return False, user_store_error()
    try:
        profile = collection.find_one({"$or": [{"username": normalized}, {"email": normalized}]})
    except PyMongoError:
        return False, user_store_error()
    if not profile or profile.get("password_hash") != hash_password(password):
        return False, "Неправильне ім'я або пароль."
    return True, profile.get("username", normalized)


def get_watch_later(username: str) -> list[str]:
    profile = get_user_profile(username)
    items = profile.get("watch_later", [])
    return items if isinstance(items, list) else []


def update_watch_later(username: str, items: list[str]) -> None:
    collection = get_users_collection()
    if collection is None:
        return
    try:
        collection.update_one(
            {"username": normalize_username(username)},
            {"$set": {"watch_later": list(dict.fromkeys(items))}},
        )
    except PyMongoError:
        return


def add_watch_later(username: str, key: str) -> bool:
    items = get_watch_later(username)
    if key in items:
        return False
    items.append(key)
    update_watch_later(username, items)
    return True


def remove_watch_later(username: str, key: str) -> None:
    items = [item for item in get_watch_later(username) if item != key]
    update_watch_later(username, items)


def inject_css() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  --ms-page-bg: #10071f;
  --ms-page-bg-soft: #170d35;
  --ms-surface: rgba(35, 20, 80, 0.78);
  --ms-surface-strong: rgba(49, 26, 107, 0.86);
  --ms-surface-soft: rgba(79, 70, 229, 0.16);
  --ms-border: rgba(139, 92, 246, 0.28);
  --ms-border-strong: rgba(139, 92, 246, 0.48);
  --ms-shadow: 0 20px 50px rgba(8, 5, 24, 0.42);
}

html, body, [class*="css"] {
  font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
  color: #eef2ff;
}

.stApp {
  background:
    radial-gradient(circle at 10% 5%, rgba(124, 58, 237, 0.28), transparent 24%),
    radial-gradient(circle at 88% 12%, rgba(79, 70, 229, 0.22), transparent 22%),
    linear-gradient(180deg, var(--ms-page-bg), var(--ms-page-bg-soft)) !important;
  color: #eef2ff;
}

.stApp::before {
  content: "";
  position: fixed;
  inset: 0;
  background:
    radial-gradient(circle at 10% 5%, rgba(124, 58, 237, 0.22), transparent 18%),
    radial-gradient(circle at 88% 12%, rgba(79, 70, 229, 0.18), transparent 16%),
    linear-gradient(180deg, rgba(16, 7, 31, 0.94), rgba(23, 13, 53, 0.98));
  pointer-events: none;
}

.stApp::after {
  content: "";
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
  background-size: 72px 72px, 72px 72px;
  opacity: 0.45;
  pointer-events: none;
}

section.main > div {
  position: relative;
  z-index: 1;
  max-width: 1480px;
  margin: 50px auto;
  padding: 30px 34px 56px 34px;
}

section.main > div:has(.ms-auth-form-marker) {
  margin-top: 0 !important;
  padding-top: 0 !important;
}

div[data-testid="stHorizontalBlock"]:has(.ms-hero) {
  margin-top: -60px;
}

header[data-testid="stHeader"],
footer {
  visibility: hidden;
  height: 0;
}

.ms-hero {
  position: relative;
  isolation: isolate;
  overflow: visible;
  width: calc(100% + 326px);
  max-width: none;
  border-radius: 32px;
  min-height: 400px;
  padding: 54px 52px 56px 52px;
  border: 1px solid rgba(255,255,255,0.1);
  background:
    linear-gradient(180deg, rgba(24, 13, 54, 0.94), rgba(36, 20, 84, 0.95)),
    radial-gradient(circle at 15% 8%, rgba(79, 70, 229, 0.18), transparent 25%),
    radial-gradient(circle at 90% 12%, rgba(56, 189, 248, 0.15), transparent 20%);
  box-shadow: 0 42px 120px rgba(0, 0, 0, 0.28), inset 0 1px 0 rgba(255,255,255,0.06);
  backdrop-filter: blur(18px);
}

.ms-language-row {
  position: relative;
  z-index: 5;
  display: flex;
  justify-content: flex-end;
  margin: 0;
}

.ms-language-switch {
  display: inline-flex;
  gap: 4px;
  padding: 5px;
  border-radius: 999px;
  background: rgba(16, 7, 31, 0.42);
  border: 1px solid rgba(167, 139, 250, 0.26);
  box-shadow: 0 14px 34px rgba(8, 5, 24, 0.22);
}

.ms-language-option {
  min-width: 48px;
  min-height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 13px;
  border-radius: 999px;
  color: rgba(226, 232, 255, 0.72) !important;
  font-size: 13px;
  font-weight: 800;
  text-decoration: none !important;
}

.ms-language-option-active {
  color: #ffffff !important;
  background: linear-gradient(135deg, rgba(79, 70, 229, 0.56), rgba(139, 92, 246, 0.42));
  box-shadow: 0 10px 24px rgba(79, 70, 229, 0.2);
}

.ms-account-actions {
  position: relative;
  z-index: 6;
  margin-top: 54px;
  transform: none !important;
  display: flex;
  align-self: start;
  align-items: stretch;
  justify-content: flex-end;
  gap: 10px;
  line-height: 1;
}

.ms-account-actions .ms-language-switch,
.ms-account-actions .ms-account-login-link {
  height: 46px;
  min-height: 46px;
  box-sizing: border-box;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin: 0;
}

.ms-account-actions .ms-language-switch {
  flex: 0 0 auto;
  padding: 0;
  overflow: hidden;
}

.ms-account-actions .ms-language-option {
  height: 46px;
  min-height: 46px;
  min-width: 54px;
  box-sizing: border-box;
  border-radius: 0;
}

.ms-account-actions .ms-language-option:first-child {
  border-radius: 999px 0 0 999px;
}

.ms-account-actions .ms-language-option:last-child {
  border-radius: 0 999px 999px 0;
}

.ms-account-login-link {
  flex: 0 0 auto;
  min-width: 150px;
  padding: 0 22px;
  border-radius: 999px;
  color: #eef2ff !important;
  font-size: 14px;
  font-weight: 800;
  text-decoration: none !important;
  background: linear-gradient(135deg, rgba(79, 70, 229, 0.28), rgba(139, 92, 246, 0.22));
  border: 1px solid var(--ms-border-strong);
  box-shadow: 0 18px 38px rgba(79, 70, 229, 0.18), inset 0 1px 0 rgba(255,255,255,0.08);
}

.ms-hero::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: 0;
  border-radius: inherit;
  background:
    radial-gradient(circle 680px at 10% 0%, rgba(124, 58, 237, 0.24), transparent 38%),
    radial-gradient(circle 420px at 92% 10%, rgba(56, 189, 248, 0.18), transparent 35%),
    radial-gradient(circle at 35% 90%, rgba(255,255,255,0.08), transparent 24%);
  opacity: 0.95;
  pointer-events: none;
}

.ms-hero::after {
  content: "";
  position: absolute;
  inset: 0;
  z-index: 0;
  border-radius: inherit;
  background: linear-gradient(180deg, rgba(255,255,255,0.08), transparent 18%, transparent 82%, rgba(0,0,0,0.16));
  pointer-events: none;
  mix-blend-mode: overlay;
}

.ms-hero-content {
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 270px;
  gap: 24px;
  align-items: start;
}

div[data-testid="stHorizontalBlock"]:has(.ms-hero) > div[data-testid="stColumn"]:last-child div[data-testid="stButton"] {
  margin-top: 0;
  max-width: 150px;
}

div[data-testid="stHorizontalBlock"]:has(.ms-hero) > div[data-testid="stColumn"]:last-child div[data-testid="stHorizontalBlock"] {
  margin-top: 54px;
  align-items: center !important;
}

div[data-testid="stHorizontalBlock"]:has(.ms-hero) > div[data-testid="stColumn"]:last-child div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
  display: flex !important;
  align-items: center !important;
}

div[data-testid="stHorizontalBlock"]:has(.ms-hero) > div[data-testid="stColumn"]:last-child div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] {
  margin-top: 0 !important;
  transform: none !important;
}

.ms-hero-text {
  max-width: 900px;
}

.ms-hero-copy-header,
.ms-hero-text > p {
  text-align: center;
}

.ms-hero-text > p {
  margin-left: auto;
  margin-right: auto;
}

.ms-hero-center {
  grid-column: 1 / -1;
  width: min(100%, 860px);
  margin: 18px auto 0 auto;
  text-align: center;
}

.ms-hero-center .ms-hero-copy-header {
  justify-content: center;
}

.ms-hero-center > p {
  margin: 10px auto 0 auto;
  max-width: 760px;
  transform: translateX(35px);
}

.ms-hero-actions {
  display: flex;
  flex-direction: column;
  gap: 14px;
  align-items: stretch;
}

.ms-hero-card {
  border-radius: 20px;
  padding: 18px 20px;
  background: var(--ms-surface);
  border: 1px solid var(--ms-border);
  box-shadow: 0 18px 48px rgba(8, 5, 24, 0.28);
}

.ms-hero-card-link {
  display: block;
  color: inherit !important;
  text-decoration: none !important;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.ms-hero-card-link:hover {
  border-color: var(--ms-border-strong);
  transform: translateY(-2px);
}

.ms-hero-card-active {
  border-color: var(--ms-border-strong);
  box-shadow: 0 20px 54px rgba(79, 70, 229, 0.24);
}

.ms-hero-panel {
  position: relative;
  z-index: 70;
  pointer-events: auto;
  margin-top: 68px;
  margin-left: auto;
  margin-right: auto;
  width: 100%;
  padding: 16px;
  border-radius: 20px;
  background: rgba(49, 26, 107, 0.58);
  border: 1px solid var(--ms-border);
  box-shadow: 0 18px 48px rgba(8, 5, 24, 0.22);
}

.ms-hero-form {
  position: relative;
  z-index: 75;
  display: grid;
  grid-template-columns: minmax(180px, 1fr) auto;
  gap: 12px;
  align-items: end;
}

.ms-hero-filter-form {
  overflow: visible;
  grid-template-columns: minmax(150px, 1.2fr) minmax(110px, 0.8fr) minmax(110px, 0.8fr) minmax(150px, 1fr) auto;
}

.ms-hero-ai-form {
  grid-template-columns: minmax(180px, 1fr) auto;
}

.ms-hero-field {
  display: grid;
  gap: 6px;
}

.ms-hero-field span {
  color: rgba(226, 232, 255, 0.82);
  font-size: 13px;
  font-weight: 700;
}

.ms-hero-input,
.ms-hero-select {
  position: relative;
  z-index: 80;
  pointer-events: auto !important;
  user-select: text;
  width: 100%;
  min-height: 44px;
  border-radius: 12px;
  border: 1px solid var(--ms-border);
  background: rgba(16, 7, 31, 0.72);
  color: #f8fafc;
  padding: 0 14px;
  font: inherit;
}

.ms-genre-dropdown {
  position: relative;
  z-index: 120;
}

.ms-genre-dropdown[open] {
  z-index: 300;
}

.ms-genre-dropdown summary {
  list-style: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.ms-genre-dropdown summary::-webkit-details-marker {
  display: none;
}

.ms-genre-dropdown summary::after {
  content: "⌄";
  color: rgba(226, 232, 255, 0.78);
}

.ms-genre-menu {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  z-index: 320;
  pointer-events: auto;
  max-height: 196px;
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
  padding: 8px;
  border-radius: 12px;
  border: 1px solid var(--ms-border);
  background: rgba(16, 7, 31, 0.98);
  box-shadow: 0 18px 48px rgba(8, 5, 24, 0.36);
}

.ms-genre-option {
  position: relative;
  z-index: 330;
  pointer-events: auto;
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-height: 34px;
  padding: 7px 8px;
  border-radius: 9px;
  border: 0;
  color: #f8fafc;
  background: transparent;
  font-size: 14px;
  font: inherit;
  text-align: left;
  cursor: pointer;
  text-decoration: none !important;
}

.ms-genre-option:hover {
  background: rgba(79, 70, 229, 0.24);
}

.ms-genre-option-active {
  background: rgba(79, 70, 229, 0.32);
  border: 1px solid rgba(139, 92, 246, 0.42);
}

.ms-hero-submit {
  position: relative;
  z-index: 80;
  pointer-events: auto;
  min-height: 44px;
  border-radius: 999px;
  border: 1px solid var(--ms-border-strong);
  background: linear-gradient(135deg, rgba(79, 70, 229, 0.34), rgba(139, 92, 246, 0.28));
  color: #eef2ff;
  padding: 0 22px;
  font: inherit;
  font-weight: 800;
  cursor: pointer;
}

.ms-hero-textarea {
  min-height: 44px;
  height: 44px;
  padding-top: 10px;
  padding-bottom: 10px;
  resize: none;
  overflow-y: hidden;
}

.ms-hero-title-textarea {
  min-height: 44px;
  height: 44px;
  padding-top: 10px;
  padding-bottom: 10px;
  resize: none;
  overflow-y: hidden;
}

.ms-hero-card-value {
  color: #eef2ff;
  font-size: 18px;
  font-weight: 800;
  margin-bottom: 8px;
  text-align: center;
}

.ms-hero-card-label {
  color: rgba(226, 232, 255, 0.78);
  font-size: 14px;
  line-height: 1.6;
  text-align: center;
}

.ms-hero-copy {
  position: relative;
  z-index: 2;
  display: grid;
  gap: 24px;
}

.ms-hero-copy-topline {
  display: inline-flex;
  padding: 14px 22px;
  border-radius: 999px;
  align-items: center;
  background: rgba(79, 70, 229, 0.18);
  border: 1px solid rgba(79, 70, 229, 0.35);
  color: #dbeafe;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-weight: 700;
  box-shadow: 0 10px 30px rgba(79, 70, 229, 0.14);
}

.ms-hero-copy-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
}

.ms-hero-copy h1 {
  margin: 0;
  font-size: clamp(3.4rem, 5vw, 5.8rem);
  line-height: 0.98;
  max-width: 900px;
  font-weight: 900;
  color: #fff;
  letter-spacing: -0.03em;
  text-shadow: 0 18px 38px rgba(0,0,0,0.24);
}

.ms-hero-copy p {
  max-width: 780px;
  margin: 0;
  color: rgba(226,232,255,0.86);
  font-size: 1rem;
  line-height: 1.82;
  font-weight: 400;
  letter-spacing: 0.24px;
}

.ms-hero h1 {
  margin: 0;
  color: #ffffff;
  font-size: 42px;
  line-height: 1.08;
  font-weight: 800;
  letter-spacing: 0;
}

.ms-hero p {
  margin: 10px 0 0 0;
  max-width: 760px;
  color: rgba(255,255,255,0.82);
  font-size: 16px;
  line-height: 1.55;
}

.ms-hero-text .ms-hero-copy-header {
  justify-content: center;
}

.ms-hero-text .ms-hero-copy-header h1,
.ms-hero-text > p {
  width: 100%;
  margin-left: auto;
  margin-right: auto;
  text-align: center;
}

.ms-card,
.ms-section-card {
  position: relative;
  border-radius: 16px;
  background: var(--ms-surface);
  border: 1px solid var(--ms-border);
  box-shadow: var(--ms-shadow);
  backdrop-filter: blur(14px);
}

.ms-card-link {
  display: block;
  text-decoration: none !important;
  color: inherit !important;
  cursor: pointer;
}

.ms-eyebrow,
.ms-toolbar-caption,
.ms-ai-note {
  margin: 0 0 10px 0;
  color: #b8c0ff;
  font-size: 14px;
  line-height: 1.5;
}

.ms-eyebrow {
  color: #dbeafe;
  font-weight: 700;
  letter-spacing: 0;
}

.ms-block-title {
  margin: 0 0 8px 0;
  color: #f8fafc;
  font-size: 20px;
  font-weight: 700;
}

.ms-plain-section {
  margin-top: 31px;
  margin-bottom: 14px;
}

.ms-filter-section {
  margin-top: 30px;
  margin-bottom: 6px;
}

.ms-card {
  position: relative;
  overflow: hidden;
  padding: 0 0 14px 0;
  margin-bottom: 20px;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.ms-card:hover {
  transform: translateY(-6px);
  border-color: rgba(139, 92, 246, 0.65);
  box-shadow: 0 24px 58px rgba(0,0,0,0.48);
}

.ms-poster-frame {
  width: 100%;
  height: 390px;
  border-radius: 12px 12px 0 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background:
    radial-gradient(circle at 50% 18%, rgba(79, 70, 229, 0.18), transparent 34%),
    rgba(16, 7, 31, 0.52);
}

.ms-poster {
  display: block;
  width: auto !important;
  height: auto !important;
  max-width: 100% !important;
  max-height: 100% !important;
  object-fit: contain !important;
  object-position: center center !important;
}

.ms-poster.ms-skeleton {
  width: 100% !important;
  height: 100% !important;
  max-width: none !important;
  max-height: none !important;
  background: linear-gradient(120deg, rgba(49, 26, 107, 0.72) 0%, rgba(79, 70, 229, 0.42) 50%, rgba(49, 26, 107, 0.72) 100%);
  background-size: 180% 180%;
  animation: ms-skeleton 1.1s ease-in-out infinite;
}

.ms-card-overlay {
  position: absolute;
  inset: 8px 8px auto 8px;
  height: 36px;
  display: flex;
  justify-content: flex-end;
  opacity: 0;
  transition: opacity 0.16s ease;
}

.ms-card:hover .ms-card-overlay {
  opacity: 1;
}

.ms-card-overlay-pill,
.ms-badge,
.ms-meta-chip,
.ms-ai-pill {
  border-radius: 999px;
  border: 1px solid rgba(99, 102, 241, 0.22);
  background: rgba(79, 70, 229, 0.14);
}

.ms-card-overlay-pill {
  height: 28px;
  padding: 5px 12px;
  color: #eef2ff;
  font-size: 12px;
}

.ms-title {
  margin: 12px 12px 0 12px;
  display: block;
  font-weight: 700;
  font-size: 16px;
  line-height: 1.25;
  color: #eef2ff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ms-meta {
  margin: 5px 12px 0 12px;
  color: rgba(226, 232, 255, 0.78);
  font-size: 13px;
  line-height: 1.35;
}

.ms-badge {
  display: inline-block;
  margin: 8px 0 0 12px;
  padding: 3px 8px;
  color: #dbeafe;
  font-size: 12px;
}

.ms-section-card {
  margin: 18px 0 16px 0;
  padding: 14px 16px;
}

.ms-meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 8px 0 14px 0;
}

.ms-meta-chip,
.ms-ai-pill {
  display: inline-block;
  padding: 6px 10px;
  color: #d6e3f3;
  font-size: 13px;
}

.ms-detail-image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain !important;
  object-position: center center !important;
  border-radius: 16px;
  background:
    radial-gradient(circle at 50% 18%, rgba(79, 70, 229, 0.18), transparent 34%),
    rgba(16, 7, 31, 0.52);
}

.ms-detail-hero {
  display: grid;
  grid-template-columns: minmax(320px, 0.92fr) minmax(320px, 1fr);
  gap: 28px;
  align-items: stretch;
  margin: -50px 0 22px 0;
  padding: 18px;
  border-radius: 24px;
  background: rgba(49, 26, 107, 0.42);
  border: 1px solid var(--ms-border);
  box-shadow: 0 28px 80px rgba(0, 0, 0, 0.34);
}

.ms-detail-media {
  position: relative;
  min-height: 340px;
  max-height: 430px;
  overflow: hidden;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: var(--ms-surface);
}

.ms-detail-info {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  min-width: 0;
  padding: 14px 12px 18px 0;
}

.ms-detail-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-bottom: 18px;
}

.ms-detail-action {
  min-width: 132px;
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 18px;
  border-radius: 999px;
  color: #dbeafe !important;
  font-size: 14px;
  font-weight: 700;
  text-decoration: none !important;
  background: linear-gradient(135deg, rgba(79, 70, 229, 0.32), rgba(139, 92, 246, 0.24));
  border: 1px solid rgba(139, 92, 246, 0.58);
  box-shadow: 0 14px 34px rgba(79, 70, 229, 0.18);
}

.ms-detail-action:hover {
  border-color: rgba(196, 181, 253, 0.78);
  transform: translateY(-1px);
}

.ms-detail-back {
  position: absolute;
  top: 14px;
  left: 14px;
  z-index: 2;
  min-width: 104px;
  min-height: 34px;
  padding: 0 14px;
  color: rgba(238, 242, 255, 0.78) !important;
  font-size: 13px;
  background: rgba(16, 7, 31, 0.34);
  border-color: rgba(226, 232, 255, 0.2);
  box-shadow: none;
  backdrop-filter: blur(8px);
}

.ms-detail-back:hover {
  color: #ffffff !important;
  background: rgba(49, 26, 107, 0.56);
}

.ms-detail-title {
  margin: 0 0 16px 0;
  color: #ffffff;
  font-size: 42px;
  line-height: 1.08;
  font-weight: 800;
}

.ms-detail-rating-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(110px, 1fr));
  gap: 12px;
  margin-top: 18px;
}

.ms-detail-rating {
  padding: 14px;
  border-radius: 16px;
  background: rgba(16, 7, 31, 0.54);
  border: 1px solid rgba(99, 102, 241, 0.22);
}

.ms-detail-rating-label {
  display: block;
  margin-bottom: 7px;
  color: rgba(226, 232, 255, 0.76);
  font-size: 12px;
  font-weight: 700;
}

.ms-detail-rating-value {
  display: block;
  color: #ffffff;
  font-size: 30px;
  line-height: 1;
  font-weight: 800;
}

.ms-detail-signin-note {
  margin: 5px 0 0 0;
  color: rgba(203, 213, 225, 0.74);
  font-size: 13px;
  line-height: 1.45;
}

.ms-detail-watch-later {
  width: fit-content;
  min-height: 42px;
  margin-top: 15px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 18px;
  border-radius: 999px;
  color: #eef2ff !important;
  font-size: 14px;
  font-weight: 800;
  text-decoration: none !important;
  background: linear-gradient(135deg, rgba(79, 70, 229, 0.48), rgba(139, 92, 246, 0.36));
  border: 1px solid rgba(167, 139, 250, 0.46);
  box-shadow: 0 14px 34px rgba(79, 70, 229, 0.18), inset 0 1px 0 rgba(255,255,255,0.08);
}

.ms-detail-watch-later-disabled {
  opacity: 0.72;
  pointer-events: none;
}

.ms-section-shell {
  margin-top: 14px;
}

.ms-page-intro {
  margin: 4px 0 18px 0;
  color: #9fb2c8;
  font-size: 16px;
  line-height: 1.55;
}

.ms-results-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin: 28px 0 16px 0;
}

.ms-results-head h2 {
  margin: 0;
  color: #f8fafc;
  font-size: 26px;
}

.ms-results-count {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(79, 70, 229, 0.18);
  color: #eef2ff;
  font-weight: 700;
  font-size: 14px;
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.ms-hero-title-actions {
  display: flex;
  align-items: center;
  gap: 14px;
}

.ms-hero-action-circle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  border: 1.5px solid rgba(255,255,255,0.24);
  color: #ffffff;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-decoration: none;
  box-shadow: 0 24px 56px rgba(0,0,0,0.28), inset 0 1px 0 rgba(255,255,255,0.12);
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), background 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
}

.ms-hero-action-circle:hover {
  transform: translateY(-3px) scale(1.05);
  background: rgba(255, 255, 255, 0.18);
  border-color: rgba(255,255,255,0.32);
  box-shadow: 0 28px 70px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.16);
}

.ms-filter-circle {
  background: linear-gradient(135deg, rgba(72, 163, 255, 0.18), rgba(59, 130, 246, 0.12));
  border-color: rgba(72, 163, 255, 0.42);
  box-shadow: 0 24px 56px rgba(59, 130, 246, 0.15), inset 0 1px 0 rgba(255,255,255,0.1);
}

.ms-filter-circle:hover {
  background: linear-gradient(135deg, rgba(72, 163, 255, 0.28), rgba(59, 130, 246, 0.2));
  border-color: rgba(72, 163, 255, 0.58);
}

.ms-ai-chat-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(102, 126, 234, 0.15));
  border: 1.5px solid rgba(139, 92, 246, 0.4);
  color: #ffffff;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  text-decoration: none;
  box-shadow: 0 24px 56px rgba(139, 92, 246, 0.18), inset 0 1px 0 rgba(255,255,255,0.1);
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), background 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
}

.ms-ai-chat-badge:hover {
  transform: translateY(-3px) scale(1.05);
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(102, 126, 234, 0.25));
  border-color: rgba(139, 92, 246, 0.6);
  box-shadow: 0 28px 70px rgba(139, 92, 246, 0.25), inset 0 1px 0 rgba(255,255,255,0.14);
}

.ms-ai-chat-active {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.3), rgba(59, 130, 246, 0.25));
  border-color: rgba(102, 126, 234, 0.68);
  box-shadow: 0 28px 70px rgba(59, 130, 246, 0.25), inset 0 1px 0 rgba(255,255,255,0.14);
}

div[data-testid="stColumn"],
div[data-testid="stVerticalBlock"],
div[data-testid="stElementContainer"],
div[data-testid="stVerticalBlockBorderWrapper"],
div.stColumn,
div.stVerticalBlock,
div.stElementContainer,
div.stVerticalBlockBorderWrapper {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

div[data-testid="stTextInput"],
div[data-testid="stSelectbox"],
div[data-testid="stMultiSelect"],
div[data-testid="stTextArea"],
div[data-testid="stSlider"],
div[data-testid="stRadio"] {
  background: var(--ms-surface-soft) !important;
  border: 1px solid var(--ms-border) !important;
  border-radius: 16px !important;
}

div.stTabs,
div[data-baseweb="tab-list"],
div[data-baseweb="tab-border"],
div[data-baseweb="tab-highlight"] {
  background: transparent !important;
}

div[data-baseweb="tab"] {
  background: rgba(79, 70, 229, 0.14) !important;
  border: 1px solid rgba(79, 70, 229, 0.28) !important;
}

div[data-testid="stRadio"] {
  border: 1.5px solid rgba(255,255,255,0.14) !important;
  background: linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02)) !important;
  border-radius: 999px !important;
  padding: 10px 14px !important;
  box-shadow: 0 8px 24px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.08) !important;
  backdrop-filter: blur(8px) !important;
}

div[data-testid="stRadio"] label {
  color: #f8fafc !important;
  font-weight: 500 !important;
  cursor: pointer !important;
  transition: color 0.2s ease !important;
}

div[data-testid="stRadio"] label:hover {
  color: #c7d2fe !important;
}

.ms-tabs-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  margin-bottom: 14px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.ms-tab-label {
  padding: 10px 18px;
  border-radius: 999px;
  background: rgba(79, 70, 229, 0.14);
  border: 1px solid rgba(79, 70, 229, 0.28);
  color: rgba(243, 244, 255, 0.92);
  font-size: 14px;
  font-weight: 700;
  backdrop-filter: blur(8px);
}

.ms-tab-label:hover {
  background: rgba(79, 70, 229, 0.22);
}

.ms-tab-ai-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 38px;
  height: 38px;
  padding: 0 12px;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.25), rgba(59, 130, 246, 0.18));
  border: 1.5px solid rgba(99, 102, 241, 0.4);
  color: #f8fafc;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  text-decoration: none;
  box-shadow: 0 14px 40px rgba(56, 189, 248, 0.15);
  transition: transform 0.2s ease, background 0.2s ease, border-color 0.2s ease;
}

.ms-tab-ai-badge:hover {
  transform: translateY(-1px);
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.35), rgba(59, 130, 246, 0.28));
  border-color: rgba(99, 102, 241, 0.6);
}

.ms-footer {
  margin: 52px 0 10px 0;
  padding: 1px;
  border-radius: 24px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.62), rgba(56, 189, 248, 0.34));
}

.ms-footer-content {
  display: flex;
  flex-direction: column;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  justify-content: center;
  padding: 22px 24px;
  border-radius: 23px;
  background:
    radial-gradient(circle at 12% 0%, rgba(79, 70, 229, 0.24), transparent 34%),
    rgba(24, 13, 54, 0.92);
  color: #c7d2fe;
  font-size: 14px;
  line-height: 1.6;
  box-shadow: 0 22px 58px rgba(0, 0, 0, 0.24);
}

.ms-footer-brand {
  color: #ffffff;
  font-size: 16px;
  font-weight: 800;
  text-align: center;
}

.ms-footer-text {
  color: rgba(226, 232, 255, 0.76);
  text-align: center;
  max-width: 760px;
}

.st-key-floating_ai_chat_open {
  position: static !important;
}

.st-key-floating_ai_chat_open div[data-testid="stForm"] {
  border: 0 !important;
  padding: 0 !important;
  background: transparent !important;
}

.st-key-floating_ai_chat_open div[data-testid="stTextArea"] textarea {
  background: rgba(255,255,255,0.09) !important;
  border-color: rgba(255,255,255,0.16) !important;
}

.ms-chat-panel {
  padding: 0;
}

.ms-chat-title {
  color: #f8fafc;
  font-size: 18px;
  font-weight: 800;
  margin-bottom: 4px;
}

.ms-chat-subtitle {
  color: #a8a8b3;
  font-size: 13px;
  line-height: 1.45;
  margin-bottom: 14px;
}

.ms-chat-scroll {
  max-height: 300px;
  overflow-y: auto;
  padding-right: 4px;
  margin-bottom: 12px;
}

.ms-hero-panel .ms-chat-scroll {
  max-height: 260px;
  display: flex;
  flex-direction: column-reverse;
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
}

.ms-hero-panel .ms-chat-msg {
  flex: 0 0 auto;
}

.ms-chat-msg {
  margin-bottom: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.45;
}

.ms-chat-ai {
  background: rgba(79, 70, 229, 0.16);
  color: #e5e7eb;
  border: 1px solid var(--ms-border);
}

.ms-chat-user {
  margin-left: 26px;
  background: linear-gradient(135deg, #8b5cf6, #5b21b6);
  color: #ffffff;
}

.ms-chat-typing {
  overflow: hidden;
}

.ms-chat-typing > span:first-child {
  display: inline-block;
  animation: ms-type-reveal 2.1s steps(72, end) both;
  clip-path: inset(0 100% 0 0);
}

.ms-chat-cursor {
  display: inline-block;
  width: 7px;
  height: 16px;
  margin-left: 3px;
  border-radius: 999px;
  background: #c4b5fd;
  vertical-align: -2px;
  animation: ms-cursor-blink 0.85s infinite;
}

.ms-profile-box {
  margin-top: 12px;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid var(--ms-border);
  background: var(--ms-surface-soft);
}

.ms-profile-name {
  color: #f8fafc;
  font-weight: 700;
  margin-bottom: 4px;
}

.ms-watch-list {
  margin-top: 12px;
}

.ms-watch-empty {
  color: #9fb2c8;
  font-size: 14px;
}

div[data-testid="stVerticalBlock"]:has(.ms-auth-form-marker) {
  width: min(760px, 100%) !important;
  margin: 60px auto 24px auto !important;
  padding: 30px !important;
  border-radius: 28px !important;
  background: linear-gradient(135deg, rgba(24, 13, 54, 0.96), rgba(49, 26, 107, 0.92)) !important;
  border: 1px solid var(--ms-border) !important;
  box-shadow: 0 34px 100px rgba(0, 0, 0, 0.3) !important;
}

div[data-testid="stVerticalBlock"]:has(.ms-auth-form-marker) div[data-baseweb="tab-list"] {
  width: 100% !important;
  gap: 8px !important;
  padding: 6px !important;
  border-radius: 999px !important;
  background: rgba(16, 7, 31, 0.36) !important;
  border: 1px solid rgba(167, 139, 250, 0.22) !important;
}

div[data-testid="stVerticalBlock"]:has(.ms-auth-form-marker) button[data-baseweb="tab"] {
  flex: 1 1 0 !important;
  height: 42px !important;
  border-radius: 999px !important;
  color: rgba(226, 232, 255, 0.74) !important;
}

div[data-testid="stVerticalBlock"]:has(.ms-auth-form-marker) button[data-baseweb="tab"][aria-selected="true"] {
  color: #ffffff !important;
  background: linear-gradient(135deg, rgba(79, 70, 229, 0.52), rgba(139, 92, 246, 0.4)) !important;
  box-shadow: 0 12px 28px rgba(79, 70, 229, 0.22) !important;
}

div[data-testid="stVerticalBlock"]:has(.ms-auth-form-marker) div[data-baseweb="tab-highlight"] {
  display: none !important;
}

div[data-testid="stVerticalBlock"]:has(.ms-auth-form-marker) div[data-testid="stTextInput"] {
  margin-bottom: 10px !important;
}

div[data-testid="stVerticalBlock"]:has(.ms-auth-form-marker) div[data-testid="stTextInput"] input {
  min-height: 48px !important;
  color: #f8fafc !important;
}

div[data-testid="stVerticalBlock"]:has(.ms-auth-form-marker) div[data-testid="stTextInputRootElement"],
div[data-testid="stVerticalBlock"]:has(.ms-auth-form-marker) div[data-baseweb="input"],
.st-key-login_username div[data-testid="stTextInputRootElement"],
.st-key-login_password div[data-testid="stTextInputRootElement"],
.st-key-register_username div[data-testid="stTextInputRootElement"],
.st-key-register_email div[data-testid="stTextInputRootElement"],
.st-key-register_password div[data-testid="stTextInputRootElement"],
.st-key-register_confirm div[data-testid="stTextInputRootElement"],
.st-key-login_username div[data-baseweb="input"],
.st-key-login_password div[data-baseweb="input"],
.st-key-register_username div[data-baseweb="input"],
.st-key-register_email div[data-baseweb="input"],
.st-key-register_password div[data-baseweb="input"],
.st-key-register_confirm div[data-baseweb="input"] {
  min-height: 48px !important;
  border-radius: 14px !important;
  overflow: hidden !important;
  background: rgba(49, 26, 107, 0.46) !important;
  border: 1px solid rgba(167, 139, 250, 0.28) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.05) !important;
}

div[data-testid="stVerticalBlock"]:has(.ms-auth-form-marker) div[data-baseweb="base-input"],
div[data-testid="stVerticalBlock"]:has(.ms-auth-form-marker) div[data-testid="stTextInput"] input,
.st-key-login_username div[data-baseweb="base-input"],
.st-key-login_password div[data-baseweb="base-input"],
.st-key-register_username div[data-baseweb="base-input"],
.st-key-register_email div[data-baseweb="base-input"],
.st-key-register_password div[data-baseweb="base-input"],
.st-key-register_confirm div[data-baseweb="base-input"],
.st-key-login_username input,
.st-key-login_password input,
.st-key-register_username input,
.st-key-register_email input,
.st-key-register_password input,
.st-key-register_confirm input {
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  outline: 0 !important;
}

div[data-testid="stVerticalBlock"]:has(.ms-auth-form-marker) div[data-testid="stButton"] button {
  min-height: 48px !important;
  margin-top: 8px !important;
  background: linear-gradient(135deg, rgba(79, 70, 229, 0.72), rgba(139, 92, 246, 0.55)) !important;
}

.ms-auth-compact-title {
  margin: 0 0 18px 0;
  text-align: center;
}

.ms-auth-compact-title strong {
  display: block;
  color: #ffffff;
  font-size: 28px;
  line-height: 1.12;
  font-weight: 800;
}

.ms-auth-compact-title span {
  display: block;
  margin-top: 8px;
  color: rgba(203, 213, 225, 0.78);
  font-size: 14px;
  line-height: 1.45;
}

.ms-auth-info-bottom {
  margin-top: 18px;
  padding: 16px;
  border-radius: 18px;
  background: rgba(16, 7, 31, 0.2);
  border: 1px solid rgba(167, 139, 250, 0.16);
}

.ms-auth-info-title {
  display: block;
  margin: 0;
  color: #f8fafc;
  font-size: 18px;
  line-height: 1.25;
  font-weight: 800;
}

.ms-auth-info-bottom p {
  margin: 8px 0 14px 0;
  color: rgba(226, 232, 255, 0.76);
  font-size: 13px;
  line-height: 1.5;
}

.ms-auth-info-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.ms-auth-info-item {
  min-height: 58px;
  padding: 10px 11px;
  border-radius: 14px;
  color: #dbeafe;
  font-size: 12px;
  line-height: 1.35;
  background: rgba(255, 255, 255, 0.055);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

@media (max-width: 760px) {
  div[data-testid="stVerticalBlock"]:has(.ms-auth-form-marker) {
    padding: 22px !important;
  }

  .ms-auth-info-grid {
    grid-template-columns: 1fr;
  }
}

.ms-profile-page {
  max-width: 1180px;
  margin: -12px auto 0 auto;
}

.ms-profile-top {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 12px;
  align-items: center;
  margin-bottom: 18px;
  padding: 24px;
  border-radius: 24px;
  background:
    radial-gradient(circle at 12% 0%, rgba(79, 70, 229, 0.2), transparent 34%),
    linear-gradient(135deg, rgba(24, 13, 54, 0.94), rgba(49, 26, 107, 0.76));
  border: 1px solid rgba(167, 139, 250, 0.24);
  box-shadow: 0 28px 80px rgba(0, 0, 0, 0.28);
}

.ms-brand {
  color: #ffffff;
  font-size: 28px;
  line-height: 1.1;
  font-weight: 800;
}

.ms-profile-subtitle {
  margin-top: 8px;
  color: rgba(226, 232, 255, 0.72);
  font-size: 14px;
  line-height: 1.5;
}

.ms-profile-layout {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 22px;
  align-items: start;
}

.ms-profile-action-row {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr) auto;
  gap: 22px;
  align-items: center;
  margin-bottom: 12px;
}

.ms-profile-action-row .ms-detail-action {
  min-width: 0;
}

.ms-profile-home-action,
.ms-profile-logout-action {
  width: 132px !important;
}

.ms-profile-logout-action {
  color: #fecaca !important;
  background: rgba(16, 7, 31, 0.28) !important;
  border-color: rgba(248, 113, 113, 0.28) !important;
}

.ms-profile-side {
  display: grid;
  gap: 12px;
}

.ms-profile-card,
.ms-profile-content {
  border-radius: 24px;
  background:
    linear-gradient(135deg, rgba(49, 26, 107, 0.74), rgba(24, 13, 54, 0.86));
  border: 1px solid rgba(167, 139, 250, 0.22);
  box-shadow: 0 24px 70px rgba(0,0,0,0.32);
  backdrop-filter: blur(16px);
}

.ms-profile-card {
  padding: 26px 22px;
  text-align: center;
  position: sticky;
  top: 24px;
  overflow: hidden;
}

.ms-profile-card::before {
  content: "";
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 50% 0%, rgba(139, 92, 246, 0.2), transparent 34%),
    radial-gradient(circle at 10% 92%, rgba(56, 189, 248, 0.12), transparent 28%);
  pointer-events: none;
}

.ms-avatar {
  position: relative;
  width: 120px;
  height: 120px;
  margin: 0 auto 18px auto;
  border-radius: 999px;
  display: grid;
  place-items: center;
  color: #ffffff;
  font-size: 48px;
  font-weight: 900;
  border: 1px solid rgba(196, 181, 253, 0.52);
  background:
    radial-gradient(circle at 32% 22%, rgba(255, 255, 255, 0.22), transparent 28%),
    linear-gradient(135deg, rgba(79, 70, 229, 0.86), rgba(139, 92, 246, 0.7));
  box-shadow: 0 18px 48px rgba(79, 70, 229, 0.28);
}

.ms-profile-username {
  position: relative;
  color: #f8fafc;
  font-size: 24px;
  line-height: 1.18;
  font-weight: 800;
}

.ms-profile-email {
  position: relative;
  margin-top: 8px;
  color: rgba(203, 213, 225, 0.78);
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ms-stat-row {
  position: relative;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 24px;
}

.ms-stat {
  min-height: 78px;
  padding: 12px 7px;
  border-radius: 16px;
  background: rgba(16, 7, 31, 0.34);
  border: 1px solid rgba(167, 139, 250, 0.16);
}

.ms-stat strong {
  display: block;
  color: #ffffff;
  font-size: 24px;
  line-height: 1;
}

.ms-stat span {
  display: block;
  margin-top: 7px;
  color: rgba(203, 213, 225, 0.74);
  font-size: 12px;
  line-height: 1.25;
}

.ms-profile-note {
  position: relative;
  margin-top: 20px;
  padding-top: 18px;
  border-top: 1px solid rgba(167, 139, 250, 0.16);
  text-align: left;
}

.ms-profile-note-title {
  color: #ffffff;
  font-size: 18px;
  line-height: 1.2;
  font-weight: 800;
}

.ms-profile-note-text {
  margin-top: 8px;
  color: rgba(226, 232, 255, 0.72);
  font-size: 13px;
  line-height: 1.55;
}

.ms-profile-content {
  min-height: 420px;
  padding: 18px;
}

.ms-profile-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 18px;
  padding: 6px;
  border-radius: 999px;
  background: rgba(16, 7, 31, 0.32);
  border: 1px solid rgba(167, 139, 250, 0.18);
}

.ms-profile-tab {
  flex: 1 1 160px;
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 14px;
  border-radius: 999px;
  color: rgba(226, 232, 255, 0.76) !important;
  font-size: 14px;
  font-weight: 800;
  text-decoration: none !important;
  border: 1px solid transparent;
}

.ms-profile-tab-active {
  color: #ffffff !important;
  background: linear-gradient(135deg, rgba(79, 70, 229, 0.58), rgba(139, 92, 246, 0.42));
  border-color: rgba(196, 181, 253, 0.42);
  box-shadow: 0 14px 34px rgba(79, 70, 229, 0.2);
}

.ms-profile-section-title {
  margin: 0 0 14px 0;
  color: #f8fafc;
  font-size: 18px;
  line-height: 1.25;
  font-weight: 800;
}

.ms-mini-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 18px;
}

.ms-mini-card {
  display: block;
  color: inherit;
  text-decoration: none;
  cursor: pointer;
  padding: 10px;
  border-radius: 18px;
  background: rgba(16, 7, 31, 0.24);
  border: 1px solid rgba(167, 139, 250, 0.14);
  transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease;
}

.ms-mini-card:hover {
  transform: translateY(-4px);
  border-color: rgba(167, 139, 250, 0.44);
  background: rgba(49, 26, 107, 0.38);
}

.ms-mini-card img,
.ms-mini-empty-poster {
  width: 100%;
  aspect-ratio: 2 / 3;
  object-fit: contain;
  border-radius: 14px;
  background:
    radial-gradient(circle at 50% 18%, rgba(79, 70, 229, 0.2), transparent 34%),
    rgba(16, 7, 31, 0.54);
}

.ms-mini-card-title {
  margin-top: 10px;
  color: #f8fafc;
  font-size: 14px;
  line-height: 1.28;
  font-weight: 800;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ms-mini-card-meta {
  margin-top: 5px;
  color: rgba(203, 213, 225, 0.68);
  font-size: 12px;
  line-height: 1.35;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 800px) {
  .ms-profile-layout {
    grid-template-columns: 1fr;
  }

  .ms-hero-content {
    grid-template-columns: 1fr;
  }

  .ms-detail-hero {
    grid-template-columns: 1fr;
  }

  .ms-detail-info {
    padding: 4px 2px 8px 2px;
  }

  .ms-detail-actions {
    flex-direction: column;
  }

  .ms-detail-title {
    font-size: 30px;
  }

  .ms-detail-rating-grid {
    grid-template-columns: 1fr;
  }
}

.ms-pagination-sticky {
  display: none !important;
}

.ms-page-pill,
.ms-page-disabled,
.ms-page-ellipsis {
  min-width: 44px;
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  color: #dbeafe !important;
  font-size: 14px;
  font-weight: 800;
  text-decoration: none !important;
}

.ms-page-pill {
  color: #ffffff !important;
  background:
    radial-gradient(circle at 30% 20%, rgba(255, 255, 255, 0.18), transparent 34%),
    linear-gradient(135deg, rgba(79, 70, 229, 0.92), rgba(139, 92, 246, 0.74));
  border: 1px solid rgba(196, 181, 253, 0.82);
  box-shadow: 0 14px 34px rgba(79, 70, 229, 0.42), inset 0 1px 0 rgba(255,255,255,0.16);
}

.ms-page-disabled,
.ms-page-ellipsis {
  color: rgba(148, 163, 184, 0.64) !important;
}

div[data-testid="stHorizontalBlock"]:has(.st-key-page_prev) {
  width: fit-content !important;
  max-width: 100% !important;
  margin: 30px auto 12px auto !important;
  padding: 12px !important;
  border-radius: 999px !important;
  background:
    linear-gradient(135deg, rgba(49, 26, 107, 0.72), rgba(24, 13, 54, 0.86)) !important;
  border: 1px solid rgba(167, 139, 250, 0.36) !important;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.34) !important;
}

div[data-testid="stHorizontalBlock"]:has(.st-key-page_prev) > div[data-testid="stColumn"] {
  width: 50px !important;
  min-width: 50px !important;
  flex: 0 0 50px !important;
  padding: 0 3px !important;
}

div[class*="st-key-page_"],
.st-key-page_prev,
.st-key-page_next {
  width: 44px !important;
  min-width: 44px !important;
  max-width: 44px !important;
  margin: 0 auto !important;
}

div[class*="st-key-page_"] button,
.st-key-page_prev button,
.st-key-page_next button {
  width: 44px !important;
  min-width: 44px !important;
  height: 44px !important;
  min-height: 44px !important;
  padding: 0 !important;
  border-radius: 999px !important;
  color: #dbeafe !important;
  font-size: 14px !important;
  font-weight: 800 !important;
  background:
    radial-gradient(circle at 30% 18%, rgba(255, 255, 255, 0.12), transparent 35%),
    linear-gradient(135deg, rgba(16, 7, 31, 0.78), rgba(49, 26, 107, 0.54)) !important;
  border: 1px solid rgba(139, 92, 246, 0.42) !important;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.22), inset 0 1px 0 rgba(255,255,255,0.08) !important;
}

div[class*="st-key-page_"] button p,
.st-key-page_prev button p,
.st-key-page_next button p {
  color: inherit !important;
  font-size: inherit !important;
  font-weight: inherit !important;
}

div[class*="st-key-page_"] button:hover,
.st-key-page_prev button:hover,
.st-key-page_next button:hover {
  background: linear-gradient(135deg, rgba(79, 70, 229, 0.48), rgba(139, 92, 246, 0.38)) !important;
  border-color: rgba(167, 139, 250, 0.58) !important;
}

div[class*="st-key-page_"] button:disabled,
.st-key-page_prev button:disabled,
.st-key-page_next button:disabled {
  color: rgba(148, 163, 184, 0.64) !important;
  background: transparent !important;
  border-color: transparent !important;
}

div[data-testid="stTextInput"] input,
div[data-testid="stSelectbox"] div[role="combobox"],
div[data-testid="stMultiSelect"] div[role="combobox"],
div[data-testid="stTextArea"] textarea {
  border-radius: 10px !important;
  border: 1px solid var(--ms-border) !important;
  color: #f8fafc !important;
  font-size: 15px !important;
  background: rgba(49, 26, 107, 0.42) !important;
  min-height: 42px !important;
}

div[data-baseweb="input"],
div[data-baseweb="base-input"],
div[data-baseweb="select"],
div[data-testid="stTextInputRootElement"],
div[data-testid="stSelectbox"] [data-baseweb],
div[data-testid="stMultiSelect"] [data-baseweb] {
  background: rgba(49, 26, 107, 0.42) !important;
  border-color: var(--ms-border) !important;
  color: #f8fafc !important;
}

div[data-testid="stTextInput"] input::placeholder,
div[data-testid="stTextArea"] textarea::placeholder {
  color: rgba(203, 213, 225, 0.68) !important;
}

div[data-testid="stMarkdownContainer"] p,
label,
.stCaptionContainer {
  color: #9fb2c8 !important;
}

div[data-testid="stCheckbox"] label {
  color: #f8fafc !important;
}
div[data-testid="stCheckbox"] input {
  accent-color: #8b5cf6 !important;
}

div[data-testid="stSlider"] [role="slider"] {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.35), rgba(59, 130, 246, 0.35)) !important;
  border-color: rgba(255,255,255,0.16) !important;
}

div[data-testid="stMainContent"],
section.main,
main[role="main"] {
  background: transparent !important;
  color: #eef2ff !important;
}

div[data-testid="stAppViewContainer"],
div[data-testid="stMain"],
body {
  background: var(--ms-page-bg) !important;
}

/* Keep Streamlit button wrappers invisible and style only the real button element. */
div[data-testid="stButton"],
div.stButton,
div[class*="stButton"],
div[data-testid="stFormSubmitButton"] {
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
}

div[data-testid="stButton"] button,
div.stButton button,
div[class*="stButton"] button,
div[data-testid="stFormSubmitButton"] button,
button[data-testid^="stBaseButton"],
button[data-testid$="FormSubmitButton"],
button[class*="stBaseButton"],
button[kind="secondary"],
button[kind="primary"],
button[kind="tertiary"],
button[title="Submit"] {
  color: #eef2ff !important;
  background: linear-gradient(135deg, rgba(79, 70, 229, 0.28), rgba(139, 92, 246, 0.22)) !important;
  border: 1px solid var(--ms-border-strong) !important;
  box-shadow: 0 18px 38px rgba(79, 70, 229, 0.18), inset 0 1px 0 rgba(255,255,255,0.08) !important;
  border-radius: 999px !important;
  min-height: 46px !important;
  outline: none !important;
}

div[data-testid="stButton"] button *,
div.stButton button *,
div[class*="stButton"] button *,
div[data-testid="stFormSubmitButton"] button * {
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
}

button[data-testid^="stBaseButton"] > div[data-testid="stMarkdownContainer"],
button[class*="stBaseButton"] > div[data-testid="stMarkdownContainer"] {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
}

div[data-testid="stButton"] button:hover,
div.stButton button:hover,
div[class*="stButton"] button:hover,
div[data-testid="stFormSubmitButton"] button:hover,
button[data-testid^="stBaseButton"]:hover,
button[data-testid$="FormSubmitButton"]:hover,
button[class*="stBaseButton"]:hover,
button[kind="secondary"]:hover,
button[kind="primary"]:hover,
button[kind="tertiary"]:hover,
button[title="Submit"]:hover {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.34), rgba(139, 92, 246, 0.32)) !important;
  border-color: rgba(167, 139, 250, 0.62) !important;
}

div[data-testid="stButton"] button:disabled,
div.stButton button:disabled,
div[class*="stButton"] button:disabled,
div[data-testid="stFormSubmitButton"] button:disabled,
button[data-testid^="stBaseButton"]:disabled,
button[data-testid$="FormSubmitButton"]:disabled,
button[class*="stBaseButton"]:disabled,
button[kind="secondary"]:disabled,
button[kind="primary"]:disabled,
button[kind="tertiary"]:disabled,
button[title="Submit"]:disabled {
  opacity: 0.65 !important;
  cursor: not-allowed !important;
}

h1, h2, h3 {
  color: #f8fafc;
}

@media (max-width: 900px) {
  section.main > div {
    padding-top: 18px;
  }

  .ms-hero {
    width: 100%;
    min-height: 220px;
    padding: 22px;
  }

  div[data-testid="stHorizontalBlock"]:has(.ms-hero) > div[data-testid="stColumn"]:last-child div[data-testid="stButton"] {
    margin-top: 0;
  }

  .ms-hero-form,
  .ms-hero-filter-form {
    grid-template-columns: 1fr;
  }

  .ms-hero h1 {
    font-size: 34px;
  }

  .ms-poster-frame {
    height: 340px;
  }

  .ms-results-head {
    display: block;
  }
}

@keyframes ms-skeleton {
  0% { background-position: 0% 50%; }
  100% { background-position: 100% 50%; }
}

@keyframes ms-cursor-blink {
  0%, 45% { opacity: 1; }
  46%, 100% { opacity: 0; }
}

@keyframes ms-type-reveal {
  from { clip-path: inset(0 100% 0 0); }
  to { clip-path: inset(0 0 0 0); }
}
</style>
        """,
        unsafe_allow_html=True,
    )


def t(lang: str, ua: str, en: str) -> str:
    return ua if lang == "UA" else en


def clean_rating(value: object) -> Optional[float]:
    try:
        rating = float(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(rating) or rating <= 0:
        return None
    return rating


def translate_genres(genres: object, lang: str) -> str:
    text = str(genres or "").strip()
    if not text:
        return "-"
    if lang != "UA":
        return text

    translated = []
    for part in text.split(","):
        genre = part.strip()
        translated.append(GENRE_UA_MAP.get(genre, genre))
    return ", ".join(translated)


def clean_display_text(value: object) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    text = str(value).replace("\u00a0", " ").strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return ""
    return re.sub(r"\s+", " ", text)


def get_title_display(row: pd.Series, lang: str) -> str:
    base = clean_display_text(row.get("title", ""))
    if lang == "UA":
        for key in ["tmdb_title_ua", "title_ua"]:
            val = clean_display_text(row.get(key, ""))
            if val:
                return val
        return TITLE_UA_MAP.get(base, base)
    return base


def filter_by_title_query(movies: pd.DataFrame, query: str) -> pd.DataFrame:
    query = clean_display_text(str(query or "").replace("\r", " ").replace("\n", " "))
    if not query:
        return movies
    search_terms = {query}
    alias = resolve_known_title_alias(query)
    if alias:
        search_terms.add(alias)
    query_norm = normalize_title_match_text(query)
    if query_norm:
        for alias_key, alias_title in MOVIE_TITLE_ALIASES.items():
            alias_key_norm = normalize_title_match_text(alias_key)
            if not alias_key_norm:
                continue
            if query_norm == alias_key_norm or query_norm in alias_key_norm or alias_key_norm in query_norm:
                search_terms.add(alias_title)
    mask = pd.Series(False, index=movies.index)
    for column in ["title", "title_ua", "tmdb_title", "tmdb_title_ua"]:
        if column not in movies.columns:
            continue
        column_values = movies[column].fillna("").astype(str)
        for term in search_terms:
            term = clean_display_text(term)
            if term:
                mask = mask | column_values.str.contains(term, case=False, na=False, regex=False)
    for title_en, title_ua in TITLE_UA_MAP.items():
        title_ua_norm = normalize_title_match_text(title_ua)
        title_en_norm = normalize_title_match_text(title_en)
        if query_norm and (
            query_norm == title_ua_norm
            or query_norm == title_en_norm
            or query_norm in title_ua_norm
            or query_norm in title_en_norm
        ):
            mask = mask | movies["title"].fillna("").astype(str).str.contains(title_en, case=False, na=False, regex=False)
    return movies.loc[mask].copy()


def normalize_poster_url(value: object) -> str:
    if not isinstance(value, str):
        return ""
    poster = value.strip()
    if not poster or poster.lower() in {"nan", "none", "null"}:
        return ""
    if poster.startswith("/"):
        return f"https://image.tmdb.org/t/p/w500{poster}"
    return poster


def get_poster_display(row: pd.Series, lang: str) -> str:
    preferred_keys = ["tmdb_poster_url", "poster_src"]
    if lang == "UA":
        preferred_keys = ["tmdb_poster_url_ua", "poster_src_ua", "tmdb_poster_url", "poster_src"]

    for key in preferred_keys:
        poster = normalize_poster_url(row.get(key, ""))
        if poster:
            return poster
    return ""


def has_display_poster_frame(df: pd.DataFrame) -> pd.Series:
    if "tmdb_poster_url" not in df.columns:
        return pd.Series(False, index=df.index)
    return df["tmdb_poster_url"].apply(lambda value: bool(normalize_poster_url(value)))


def get_backdrop(row: pd.Series) -> str:
    backdrop = row.get("tmdb_backdrop_url", "")
    return backdrop if isinstance(backdrop, str) and backdrop.strip() else ""


def movie_key(row: pd.Series) -> str:
    year = row.get("year", "")
    return f"{row.get('title', '')}|{int(year) if not pd.isna(year) else ''}"


def get_overview_display(row: pd.Series, lang: str) -> str:
    base_title = clean_display_text(row.get("title", ""))
    if lang == "UA":
        for key in ["tmdb_overview_ua", "overview_ua"]:
            value = clean_display_text(row.get(key, ""))
            if value:
                return value
        mapped_overview = OVERVIEW_UA_MAP.get(base_title, "")
        if mapped_overview:
            return mapped_overview
        genres_text = translate_genres(row.get("genres", ""), lang)
        year_text = clean_display_text(row.get("year", ""))
        if year_text.endswith(".0"):
            year_text = year_text[:-2]
        fallback_parts = []
        if genres_text and genres_text != "-":
            fallback_parts.append(f"жанр: {genres_text}")
        if year_text:
            fallback_parts.append(f"рік: {year_text}")
        if fallback_parts:
            return f"Український опис для цього фільму поки не додано. Основна інформація: {', '.join(fallback_parts)}."
        return "Український опис для цього фільму поки не додано."
    return clean_display_text(row.get("tmdb_overview", ""))


def movie_details_href(movie_key_val: str) -> str:
    return query_href_with_updates(movie=movie_key_val)


def query_href_without(*excluded_names: str) -> str:
    return query_href_with_updates(**{name: None for name in excluded_names})


def app_view_href(view: str) -> str:
    return query_href_with_updates(movie=None, app_view=view)


def language_switch_html(lang: str) -> str:
    ua_class = "ms-language-option ms-language-option-active" if lang == "UA" else "ms-language-option"
    en_class = "ms-language-option ms-language-option-active" if lang == "EN" else "ms-language-option"
    ua_href = query_href_with_updates(lang="UA", ai_message=None)
    en_href = query_href_with_updates(lang="EN", ai_message=None)
    return f"""
<div class="ms-language-row">
  <div class="ms-language-switch" aria-label="{html.escape(t(lang, "Перемикач мови", "Language switcher"))}">
    <a class="{ua_class}" href="{html.escape(ua_href, quote=True)}" target="_self">UA</a>
    <a class="{en_class}" href="{html.escape(en_href, quote=True)}" target="_self">EN</a>
  </div>
</div>
    """


def inline_language_switch_html(lang: str) -> str:
    ua_class = "ms-language-option ms-language-option-active" if lang == "UA" else "ms-language-option"
    en_class = "ms-language-option ms-language-option-active" if lang == "EN" else "ms-language-option"
    ua_href = query_href_with_updates(lang="UA", ai_message=None)
    en_href = query_href_with_updates(lang="EN", ai_message=None)
    return f"""
<div class="ms-language-switch" aria-label="{html.escape(t(lang, "Перемикач мови", "Language switcher"))}">
  <a class="{ua_class}" href="{html.escape(ua_href, quote=True)}" target="_self">UA</a>
  <a class="{en_class}" href="{html.escape(en_href, quote=True)}" target="_self">EN</a>
</div>
    """


def render_language_switch(lang: str) -> None:
    st.markdown(
        language_switch_html(lang),
        unsafe_allow_html=True,
    )


def render_card(row: pd.Series, lang: str) -> None:
    img = get_poster_display(row, lang)
    year = int(row["year"]) if not pd.isna(row.get("year")) else "N/A"
    imdb = clean_rating(row.get("imdb_rating"))
    tmdb = clean_rating(row.get("tmdb_vote_average"))
    rating_values = [rating for rating in [imdb, tmdb] if rating is not None]
    combined = sum(rating_values) / len(rating_values) if rating_values else None

    title_display = get_title_display(row, lang)
    genres_display = translate_genres(row.get("genres", ""), lang)
    movie_key_val = movie_key(row)
    movie_href = movie_details_href(movie_key_val)

    poster_html = (
        f'<div class="ms-poster-frame"><img class="ms-poster" src="{html.escape(img)}" alt="{html.escape(title_display)}" /></div>'
        if img
        else '<div class="ms-poster-frame"><div class="ms-poster ms-skeleton"></div></div>'
    )

    combined_text = f"{combined:.1f}" if combined is not None else "-"
    imdb_text = f"{imdb:.1f}" if imdb is not None else "-"
    tmdb_text = f"{tmdb:.1f}" if tmdb is not None else "-"
    badges = [
        f'{t(lang, "Загальний", "Combined")}: {combined_text}',
        f"IMDb: {imdb_text}",
        f"TMDB: {tmdb_text}",
    ]
    badges_html = " ".join([f'<span class="ms-badge">{html.escape(badge)}</span>' for badge in badges])

    st.markdown(
        f"""
<a class="ms-card-link" href="{html.escape(movie_href, quote=True)}" target="_self">
<div class="ms-card">
    {poster_html}
    <div class="ms-card-overlay">
      <div class="ms-card-overlay-pill">{html.escape(t(lang, "Детальніше", "Details"))}</div>
    </div>
    <div class="ms-title" title="{html.escape(title_display, quote=True)}">{html.escape(title_display)}</div>
    <div class="ms-meta">{html.escape(str(year))} / {html.escape(genres_display)}</div>
    <div>{badges_html}</div>
</div>
</a>
        """,
        unsafe_allow_html=True,
    )


def clear_selected_movie() -> None:
    st.session_state["selected_movie"] = None
    st.session_state["show_movie_details"] = False
    if "movie" in st.query_params:
        del st.query_params["movie"]


def details_view(movies: pd.DataFrame, lang: str) -> None:
    key = st.query_params.get("movie") or st.session_state.get("selected_movie")
    if not key:
        return

    if isinstance(key, list):
        key = key[0] if key else ""
    key = urllib.parse.unquote(str(key))
    if "|" not in key:
        st.warning(t(lang, "Фільм не знайдено.", "Movie not found."))
        clear_selected_movie()
        return

    title, year = key.split("|", 1)
    year_val = pd.to_numeric(year, errors="coerce") if year else np.nan
    if pd.isna(year_val):
        mask = movies["title"] == title
    else:
        mask = (movies["title"] == title) & (movies["year"] == year_val)
    idxs = movies.index[mask].tolist()
    if not idxs:
        st.warning(t(lang, "Фільм не знайдено.", "Movie not found."))
        clear_selected_movie()
        return

    row = movies.loc[idxs[0]]

    detail_image = get_backdrop(row) or get_poster_display(row, lang)
    detail_title = get_title_display(row, lang)
    detail_year = int(row["year"]) if not pd.isna(row.get("year")) else "N/A"
    current_user = get_current_user()
    account_label = t(lang, "Профіль", "Profile") if current_user else t(lang, "Увійти", "Login")
    account_href = app_view_href("profile" if current_user else "auth")
    back_href = query_href_without("movie")
    imdb = clean_rating(row.get("imdb_rating"))
    tmdb = clean_rating(row.get("tmdb_vote_average"))
    rating_values = [rating for rating in [imdb, tmdb] if rating is not None]
    combined = sum(rating_values) / len(rating_values) if rating_values else None
    combined_text = f"{combined:.1f}" if combined is not None else "-"
    imdb_text = f"{imdb:.1f}" if imdb is not None else "-"
    tmdb_text = f"{tmdb:.1f}" if tmdb is not None else "-"
    genres_text = translate_genres(row.get("genres", ""), lang)
    director_text = str(row.get("director", "") or "-")
    back_button_html = f'<a class="ms-detail-action ms-detail-back" href="{html.escape(back_href, quote=True)}" target="_self">{html.escape(t(lang, "<- Назад", "<- Back"))}</a>'
    watch_later_html = ""
    if current_user:
        detail_key = movie_key(row)
        in_list = detail_key in set(get_watch_later(current_user))
        watch_href = query_href_with_updates(add_watch_later=detail_key)
        watch_label = t(lang, "Уже в списку 'Подивитись потім'", "Already in watch later") if in_list else t(lang, "Додати в 'Подивитись потім'", "Add to watch later")
        watch_disabled_class = " ms-detail-watch-later-disabled" if in_list else ""
        watch_later_html = f'<a class="ms-detail-watch-later{watch_disabled_class}" href="{html.escape(watch_href, quote=True)}" target="_self">{html.escape(watch_label)}</a>'
    signin_note = t(
        lang,
        "Увійдіть у профіль, щоб додавати фільми в список Подивитись потім.",
        "Sign in to add movies to Watch later.",
    )
    image_html = (
        f'<div class="ms-detail-media">{back_button_html}<img class="ms-detail-image" src="{html.escape(detail_image, quote=True)}" alt="{html.escape(detail_title, quote=True)}" /></div>'
        if detail_image
        else f'<div class="ms-detail-media">{back_button_html}</div>'
    )
    st.markdown(
        f"""
<div class="ms-detail-hero">
  {image_html}
  <div class="ms-detail-info">
    <div class="ms-detail-actions">
      <a class="ms-detail-action" href="{html.escape(account_href, quote=True)}" target="_self">{html.escape(account_label)}</a>
    </div>
    <h1 class="ms-detail-title">{html.escape(detail_title)} ({html.escape(str(detail_year))})</h1>
    <div class="ms-meta-row">
      <span class="ms-meta-chip">{html.escape(t(lang, "Жанри", "Genres"))}: {html.escape(genres_text)}</span>
      <span class="ms-meta-chip">{html.escape(t(lang, "Режисер", "Director"))}: {html.escape(director_text)}</span>
    </div>
    <div class="ms-detail-rating-grid">
      <div class="ms-detail-rating">
        <span class="ms-detail-rating-label">{html.escape(t(lang, "Загальний рейтинг", "Combined rating"))}</span>
        <strong class="ms-detail-rating-value">{html.escape(combined_text)}</strong>
      </div>
      <div class="ms-detail-rating">
        <span class="ms-detail-rating-label">IMDb</span>
        <strong class="ms-detail-rating-value">{html.escape(imdb_text)}</strong>
      </div>
      <div class="ms-detail-rating">
        <span class="ms-detail-rating-label">TMDB</span>
        <strong class="ms-detail-rating-value">{html.escape(tmdb_text)}</strong>
      </div>
    </div>
    <div class="ms-detail-signin-note">{html.escape(signin_note) if not current_user else ""}</div>
    {watch_later_html}
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    overview = get_overview_display(row, lang)
    if isinstance(overview, str) and overview.strip():
            st.markdown(
            f'<div class="ms-section-card"><strong>{html.escape(t(lang, "Опис", "Overview"))}</strong><br><br>{html.escape(overview)}</div>',
                unsafe_allow_html=True,
        )

    st.markdown("---")
    st.subheader(t(lang, "Схожий контент", "Similar content"))

    _, tfidf_matrix, cosine_sim = get_similarity(movies)
    recs = content_based.get_content_recommendations(
        row["title"],
        top_n=12,
        movies=movies,
        tfidf_matrix=tfidf_matrix,
        cosine_sim=cosine_sim,
    )
    recs = recs[has_display_poster_frame(recs)]
    cols = st.columns(6)
    for index, (_, rec_row) in enumerate(recs.iterrows()):
        with cols[index % 6]:
            render_card(rec_row, lang)


def render_pagination(page: int, total_pages: int) -> None:
    if total_pages <= 1:
        return

    neighbours = {1, 2, 3, total_pages, page - 1, page, page + 1}
    page_list = sorted({item for item in neighbours if 1 <= item <= total_pages})

    display_items: list[object] = ["prev"]
    last_added = None
    for item in page_list:
        if last_added is not None and item - last_added > 1:
            display_items.append("...")
        display_items.append(item)
        last_added = item
    display_items.append("next")

    def go_to_page(target_page: int) -> None:
        if "page" in st.query_params:
            del st.query_params["page"]
        st.session_state["page"] = min(max(target_page, 1), total_pages)
        st.rerun()

    cols = st.columns(len(display_items), gap="small")
    for col, item in zip(cols, display_items):
        with col:
            if item == "prev":
                if st.button("\\<", key="page_prev", disabled=page <= 1, use_container_width=True):
                    go_to_page(page - 1)
            elif item == "next":
                if st.button("\\>", key="page_next", disabled=page >= total_pages, use_container_width=True):
                    go_to_page(page + 1)
            elif item == "...":
                st.markdown('<span class="ms-page-ellipsis">...</span>', unsafe_allow_html=True)
            elif item == page:
                st.markdown(f'<span class="ms-page-pill">{item}</span>', unsafe_allow_html=True)
            elif st.button(str(item), key=f"page_{item}", use_container_width=True):
                go_to_page(int(item))


def find_movie_by_key(movies: pd.DataFrame, key: str) -> Optional[pd.Series]:
    if "|" not in key:
        return None
    title, year = key.split("|", 1)
    year_val = pd.to_numeric(year, errors="coerce") if year else np.nan
    if pd.isna(year_val):
        mask = movies["title"] == title
    else:
        mask = (movies["title"] == title) & (movies["year"] == year_val)
    hits = movies.index[mask].tolist()
    return movies.loc[hits[0]] if hits else None


def render_auth_page(lang: str) -> None:
    get_users_collection()
    with st.container():
        st.markdown(
            f"""
<span class="ms-auth-form-marker"></span>
<style>
div[data-testid="stMainBlockContainer"]:has(.ms-auth-form-marker),
section.main > div:has(.ms-auth-form-marker),
.block-container:has(.ms-auth-form-marker) {{
  margin-top: 0 !important;
  padding-top: 0 !important;
}}

div[data-testid="stVerticalBlock"]:has(.ms-auth-form-marker) {{
  margin-top: 60px !important;
}}

.st-key-login_username div[data-baseweb="base-input"],
.st-key-login_password div[data-baseweb="base-input"],
.st-key-register_username div[data-baseweb="base-input"],
.st-key-register_email div[data-baseweb="base-input"],
.st-key-register_password div[data-baseweb="base-input"],
.st-key-register_confirm div[data-baseweb="base-input"],
.st-key-login_username input,
.st-key-login_password input,
.st-key-register_username input,
.st-key-register_email input,
.st-key-register_password input,
.st-key-register_confirm input {{
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  outline: 0 !important;
}}

.st-key-auth_back_home {{
  width: min(760px, 100%) !important;
  margin: 0 auto 18px auto !important;
}}
</style>
<div class="ms-auth-compact-title">
  <strong>{html.escape(t(lang, "Вхід або реєстрація", "Login or registration"))}</strong>
  <span>{html.escape(t(lang, "Увійдіть у свій акаунт або створіть новий.", "Sign in or create a new account."))}</span>
</div>
            """,
            unsafe_allow_html=True,
        )
        login_tab, register_tab = st.tabs([t(lang, "Вхід", "Login"), t(lang, "Реєстрація", "Register")])
        with login_tab:
            username = st.text_input(t(lang, "Ім'я або електронна пошта", "Username or email"), key="login_username")
            password = st.text_input(t(lang, "Пароль", "Password"), type="password", key="login_password")
            if st.button(t(lang, "Увійти", "Login"), key="login_submit", use_container_width=True):
                ok, result = login_user(username, password)
                if ok:
                    set_current_user(result)
                    st.session_state["view"] = "home"
                    st.rerun()
                else:
                    st.error(result)

        with register_tab:
            username = st.text_input(t(lang, "Ім'я користувача", "Username"), key="register_username")
            email = st.text_input(t(lang, "Електронна пошта", "Email"), key="register_email")
            password = st.text_input(t(lang, "Пароль", "Password"), type="password", key="register_password")
            confirm_password = st.text_input(t(lang, "Підтвердження пароля", "Confirm password"), type="password", key="register_confirm")
            if st.button(t(lang, "Зареєструватися", "Register"), key="register_submit", use_container_width=True):
                ok, result = register_user(username, email, password, confirm_password)
                if ok:
                    set_current_user(result)
                    st.session_state["view"] = "home"
                    st.rerun()
                else:
                    st.error(result)

        st.markdown(
            f"""
<div class="ms-auth-info-bottom">
  <div class="ms-auth-info-title">{html.escape(t(lang, "AI-рекомендації", "AI recommendations"))}</div>
  <p>{html.escape(t(lang, "Увійдіть у профіль, щоб зберігати фільми, повертатися до списку й отримувати точніші рекомендації.", "Sign in to save movies, return to your list, and get better recommendations."))}</p>
  <div class="ms-auth-info-grid">
    <div class="ms-auth-info-item">{html.escape(t(lang, "Зберігайте фільми у список 'Подивитись потім'", "Save movies to Watch later"))}</div>
    <div class="ms-auth-info-item">{html.escape(t(lang, "Швидко повертайтесь до улюблених добірок", "Return to your favorite picks faster"))}</div>
    <div class="ms-auth-info-item">{html.escape(t(lang, "AI краще пам'ятає ваші запити", "AI keeps your preferences clearer"))}</div>
  </div>
</div>
            """,
            unsafe_allow_html=True,
        )

    if st.button(t(lang, "← Повернутися на головну", "← Back to home"), key="auth_back_home", type="tertiary"):
        st.session_state["view"] = "home"
        st.rerun()


def build_profile_movie_grid_html(movies: pd.DataFrame, keys: list[str], lang: str) -> str:
    if not keys:
        return f'<div class="ms-watch-empty">{html.escape(t(lang, "Список поки порожній.", "The list is empty for now."))}</div>'

    cards_html: list[str] = []
    visible = False
    for key in keys:
        row = find_movie_by_key(movies, key)
        if row is None:
            continue
        visible = True
        title = get_title_display(row, lang)
        movie_href = movie_details_href(key)
        poster = get_poster_display(row, lang)
        year = int(row["year"]) if not pd.isna(row.get("year")) else "N/A"
        genres = translate_genres(row.get("genres", ""), lang)
        poster_html = (
            f'<img src="{html.escape(poster)}" alt="{html.escape(title)}" />'
            if poster
            else '<div class="ms-mini-empty-poster"></div>'
        )
        cards_html.append(
            f"""
<a class="ms-mini-card" href="{html.escape(movie_href, quote=True)}" target="_self">
  {poster_html}
  <div class="ms-mini-card-title" title="{html.escape(title, quote=True)}">{html.escape(title)}</div>
  <div class="ms-mini-card-meta">{html.escape(str(year))} / {html.escape(genres)}</div>
</a>
            """
        )

    if not visible:
        return f'<div class="ms-watch-empty">{html.escape(t(lang, "Не вдалося знайти збережені фільми у каталозі.", "Saved movies were not found in the catalog."))}</div>'
    return f'<div class="ms-mini-grid">{"".join(cards_html)}</div>'


def render_profile_movie_grid(movies: pd.DataFrame, keys: list[str], lang: str) -> None:
    st.markdown(build_profile_movie_grid_html(movies, keys, lang), unsafe_allow_html=True)


def render_profile_page(movies: pd.DataFrame, lang: str) -> None:
    current_user = get_current_user()
    if not current_user:
        st.session_state["view"] = "auth"
        st.rerun()

    profile = get_user_profile(current_user)
    display_name = profile.get("display_name", current_user)
    email = profile.get("email", "")
    watch_later = get_watch_later(current_user)
    avatar_initial = (display_name or current_user or "U").strip()[:1].upper()
    profile_tab = first_query_value(st.query_params.get("profile_tab")) or "watch_later"
    if profile_tab not in {"watch_list", "watch_later"}:
        profile_tab = "watch_later"
    tab_items = [
        ("watch_list", t(lang, "Список перегляду", "Watch list")),
        ("watch_later", t(lang, "Подивитись потім", "Watch later")),
    ]
    tabs_html = "".join(
        f'<a class="ms-profile-tab{" ms-profile-tab-active" if tab_key == profile_tab else ""}" href="{html.escape(query_href_with_updates(app_view="profile", movie=None, profile_tab=tab_key), quote=True)}" target="_self">{html.escape(label)}</a>'
        for tab_key, label in tab_items
    )
    if profile_tab == "watch_list":
        section_title = t(lang, "Список перегляду", "Watch list")
        section_content = build_profile_movie_grid_html(movies, watch_later, lang)
    else:
        section_title = t(lang, "Подивитись потім", "Watch later")
        section_content = build_profile_movie_grid_html(movies, watch_later, lang)

    st.markdown('<div class="ms-profile-page">', unsafe_allow_html=True)
    home_href = query_href_with_updates(app_view=None, movie=None, profile_tab=None)
    logout_href = query_href_with_updates(app_view=None, movie=None, profile_tab=None, profile_logout="1")
    home_button_html = f'<a class="ms-detail-action ms-profile-home-action" href="{html.escape(home_href, quote=True)}" target="_self">{html.escape(t(lang, "Головна", "Home"))}</a>'
    logout_button_html = f'<a class="ms-detail-action ms-profile-logout-action" href="{html.escape(logout_href, quote=True)}" target="_self">{html.escape(t(lang, "Вийти", "Logout"))}</a>'

    st.markdown(
        f"""
  <div class="ms-profile-action-row">
    {home_button_html}
    <div></div>
    {logout_button_html}
  </div>
  <div class="ms-profile-layout">
    <div class="ms-profile-side">
      <div class="ms-profile-card">
        <div class="ms-avatar">{html.escape(avatar_initial)}</div>
        <div class="ms-profile-username">{html.escape(display_name)}</div>
        <div class="ms-profile-email">{html.escape(email or current_user)}</div>
        <div class="ms-stat-row">
          <div class="ms-stat"><strong>0</strong><span>{html.escape(t(lang, "Переглянуто", "Watched"))}</span></div>
          <div class="ms-stat"><strong>{len(watch_later)}</strong><span>{html.escape(t(lang, "У списку", "In list"))}</span></div>
        </div>
        <div class="ms-profile-note">
          <div class="ms-profile-note-title">{html.escape(t(lang, "Профіль", "Profile"))}</div>
          <div class="ms-profile-note-text">{html.escape(t(lang, "Ваші збережені фільми, список перегляду та персональні добірки.", "Your saved movies, watch list, and personal picks."))}</div>
        </div>
      </div>
    </div>
    <div class="ms-profile-content">
      <div class="ms-profile-tabs">{tabs_html}</div>
      <div class="ms-profile-section-title">{html.escape(section_title)}</div>
      {section_content}
    </div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


CHAT_SIGNAL_TERMS = [
    "бойовик", "екшн", "комеді", "фантаст", "трилер", "драма", "анім", "жах", "хорор", "романт",
    "детектив", "кримін", "фентез", "космос", "магі", "сімейн", "легк", "темн", "весел",
    "пригод", "документ", "біограф", "істор", "музич", "мюзикл", "спорт", "вестерн",
    "напруж", "пригод", "супергер", "марвел", "action", "comedy", "sci", "science",
    "thriller", "drama", "anime", "horror", "romance", "detective", "crime", "fantasy",
    "adventure", "documentary", "biography", "history", "music", "musical", "sport", "western",
    "space", "magic", "family", "dark", "light", "without", "no", "хочу", "подив",
    "новин", "нове", "нові", "свіж", "свіже", "популяр", "топ", "найкращ", "рейтинг", "latest", "new", "popular", "top", "best",
]


CHAT_GREETING_TERMS = {"привіт", "привет", "ку", "хай", "hello", "hi", "hey", "вітаю", "здоров", "доброго дня", "добрий день"}
CHAT_THANKS_TERMS = {"дякую", "спасибі", "спасибо", "thanks", "thank you", "ок", "окей", "добре", "супер"}
CHAT_HELP_TERMS = {"що ти вмієш", "що можеш", "допоможи", "help", "як працює", "як шукати"}
CHAT_LATEST_TERMS = {"новин", "новину", "новинк", "новинка", "новинку", "новинки", "нове", "нові", "новий", "новеньк", "свіж", "свіже", "свіжі", "свіжак", "найновіше", "latest", "new", "new release", "new movie"}
CHAT_LATEST_TERMS.update({
    "\u043d\u043e\u0432\u0438\u0445",
    "\u043d\u043e\u0432\u043e\u0433\u043e",
    "\u043d\u043e\u0432\u0438\u043c",
    "\u043d\u043e\u0432\u0438\u043c\u0438",
    "\u043d\u0430\u0439\u043d\u043e\u0432\u0456\u0448\u0456",
    "\u043d\u0430\u0439\u043d\u043e\u0432\u0456\u0448\u0438\u0445",
})
CHAT_POPULAR_TERMS = {"популярне", "популярні", "популярний", "тренд", "трендов", "popular", "trending"}
CHAT_TOP_TERMS = {"топ", "найкраще", "найкращі", "високий рейтинг", "рейтинг", "рейтингом", "оцінка", "оцінки", "best", "top rated", "high rated"}
CHAT_QUALITY_TERMS = {"норм", "нормальн", "хорош", "гарн", "сильн", "висок", "якісн", "крут", "не поган", "непоган", "рейтинг", "рейтингом", "оцінк", "good", "decent", "quality"}
CHAT_RESET_TERMS = {
    "скинь",
    "очисти",
    "очисть",
    "заново",
    "спочатку",
    "забудь",
    "все забудь",
    "забудь все",
    "забудь про все",
    "forget",
    "forget everything",
    "reset",
    "clear",
    "start over",
}
CHAT_RESET_COMMAND_PHRASES = sorted(CHAT_RESET_TERMS, key=len, reverse=True)
SIMILAR_MOVIE_PATTERNS = [
    r"(?:покажи|дай|порадь|знайди).{0,40}(?:схож\w*|похож\w*|подібн\w*).{0,12}(?:на|до|як)\s+(.+)",
    r"(?:схож\w*|похож\w*|подібн\w*)\s+(?:на|до|як)\s+(.+)",
    r"(?:\bяк\b|\bтипу\b|в\s+стилі)\s+(.+)",
    r"(?:схож\w*|похож\w*|подібн\w*)\s+(?:на|до)\s+(.+)",
    r"(?:як|типу|в стилі)\s+(.+)",
    r"similar\s+to\s+(.+)",
    r"like\s+(.+)",
]
MOVIE_TITLE_ALIASES = {
    "форсаж": "Fast X",
    "форсажу": "Fast X",
    "форсаж 10": "Fast X",
    "фаст форсаж": "Fast X",
    "fast furious": "Fast X",
    "fast and furious": "Fast X",
    "the fast and the furious": "The Fast and the Furious",
    "гран турізмо": "Gran Turismo",
    "гран турисмо": "Gran Turismo",
    "гран турізмо": "Gran Turismo",
    "гран турисмо": "Gran Turismo",
    "gran turismo": "Gran Turismo",
}

MOVIE_TITLE_ALIASES.update({
    "барбі": "Barbie",
    "барби": "Barbie",
    "форсаж": "Fast X",
    "форсажа": "Fast X",
    "форсажем": "Fast X",
    "форсажі": "Fast X",
    "форсажу": "Fast X",
    "гран турізмо": "Gran Turismo",
    "гран турисмо": "Gran Turismo",
    "трансформери": "Transformers: Rise of the Beasts",
    "трансформер": "Transformers",
    "бамблбі": "Bumblebee",
    "джон вік": "John Wick: Chapter 4",
    "гаррі поттер": "Harry Potter and the Philosopher's Stone",
    "гаррі потера": "Harry Potter and the Philosopher's Stone",
    "гарі потера": "Harry Potter and the Philosopher's Stone",
    "людина павук": "Spider-Man: No Way Home",
    "людина-павук": "Spider-Man: No Way Home",
    "месники": "Avengers: Infinity War",
    "аватар": "Avatar: The Way of Water",
    "зоряні війни": "Star Wars",
    "володар перснів": "The Lord of the Rings: The Fellowship of the Ring",
    "трансформери": "Transformers: Rise of the Beasts",
    "трансформер": "Transformers",
    "transformers": "Transformers: Rise of the Beasts",
    "бамблбі": "Bumblebee",
    "bumblebee": "Bumblebee",
    "джон вік": "John Wick: Chapter 4",
    "john wick": "John Wick: Chapter 4",
    "гаррі поттер": "Harry Potter and the Philosopher's Stone",
    "гаррі потера": "Harry Potter and the Philosopher's Stone",
    "гарі потера": "Harry Potter and the Philosopher's Stone",
    "harry potter": "Harry Potter and the Philosopher's Stone",
    "людина павук": "Spider-Man: No Way Home",
    "людина-павук": "Spider-Man: No Way Home",
    "spider man": "Spider-Man: No Way Home",
    "spider-man": "Spider-Man: No Way Home",
    "месники": "Avengers: Infinity War",
    "avengers": "Avengers: Infinity War",
    "аватар": "Avatar: The Way of Water",
    "avatar": "Avatar: The Way of Water",
    "зоряні війни": "Star Wars",
    "star wars": "Star Wars",
    "володар перснів": "The Lord of the Rings: The Fellowship of the Ring",
    "lord of the rings": "The Lord of the Rings: The Fellowship of the Ring",
})

SIMILARITY_PROFILE_QUERIES = {
    "Fast X": (
        "fast furious street racing cars car chase heist action crime thriller family "
        "drivers speed race drift turbo undercover transport transporter need for speed baby driver death race"
    ),
    "The Fast and the Furious": (
        "street racing cars car chase heist action crime thriller drivers speed race drift turbo undercover"
    ),
    "Gran Turismo": (
        "racing cars motorsport driver competition speed track sports drama race professional driver"
    ),
    "Transformers: Rise of the Beasts": (
        "transformers robots alien machines giant robots action science fiction adventure battle invasion "
        "bumblebee autobots decepticons mech technology world saving spectacle"
    ),
    "Transformers": (
        "transformers robots alien machines giant robots action science fiction adventure battle invasion "
        "bumblebee autobots decepticons mech technology world saving spectacle"
    ),
    "Harry Potter and the Philosopher's Stone": (
        "wizard magic school witchcraft fantasy adventure friendship young hero prophecy dark lord "
        "hogwarts spells magical creatures family mystery hobbit lord of the rings narnia fantastic beasts"
    ),
}

SIMILARITY_RELATED_TITLE_BOOSTS = {
    "Harry Potter and the Philosopher's Stone": {
        "harry potter": 4.0,
        "fantastic beasts": 3.8,
        "hobbit": 3.6,
        "lord of the rings": 3.6,
        "narnia": 3.2,
        "percy jackson": 2.9,
    },
}

SIMILARITY_PROFILE_BOOST_TERMS = {
    "Fast X": [
        "fast", "furious", "speed", "race", "racing", "driver", "drive", "transport", "transporter",
        "taxi", "car", "cars", "chase", "drift", "turbo", "heist", "crime", "action",
    ],
    "The Fast and the Furious": [
        "fast", "furious", "speed", "race", "racing", "driver", "drive", "car", "cars", "chase", "drift", "heist",
    ],
    "Gran Turismo": [
        "gran turismo", "race", "racing", "driver", "motorsport", "speed", "car", "cars", "track", "competition",
    ],
    "Transformers: Rise of the Beasts": [
        "transformers", "robot", "robots", "alien", "machine", "machines", "autobot", "autobots",
        "decepticon", "decepticons", "bumblebee", "mech", "action", "adventure", "science", "fiction",
        "godzilla", "kong", "pacific", "rim", "steel",
    ],
    "Transformers": [
        "transformers", "robot", "robots", "alien", "machine", "machines", "autobot", "autobots",
        "decepticon", "decepticons", "bumblebee", "mech", "action", "adventure", "science", "fiction",
        "godzilla", "kong", "pacific", "rim", "steel",
    ],
    "Harry Potter and the Philosopher's Stone": [
        "wizard", "magic", "magical", "spell", "spells", "witch", "witchcraft", "school", "hogwarts",
        "fantasy", "adventure", "young", "hero", "prophecy", "creatures", "mystery", "hobbit",
        "rings", "narnia", "beasts",
    ],
}

SIMILARITY_REQUIRED_TERMS = {
    "Fast X": [
        "fast", "furious", "race", "racing", "driver", "drive", "cars", "car", "chase",
        "drift", "speed", "heist", "transport", "transporter", "taxi", "turbo",
    ],
    "The Fast and the Furious": [
        "fast", "furious", "race", "racing", "driver", "drive", "cars", "car", "chase",
        "drift", "speed", "heist",
    ],
}

SIMILARITY_STOPWORDS = {
    "the", "and", "for", "with", "from", "into", "that", "this", "when", "where", "while", "after", "before",
    "movie", "film", "films", "part", "chapter", "vol", "story", "young", "must", "will", "their", "they",
    "його", "вона", "вони", "фільм", "кіно", "історія", "частина", "після", "коли", "щоб", "який", "яка",
}


def text_has_any(text: str, terms: set[str]) -> bool:
    return any(term in text for term in terms)


def is_reset_chat_request(message: str) -> bool:
    lowered = str(message or "").strip().lower()
    return bool(lowered) and text_has_any(lowered, CHAT_RESET_TERMS)


def split_reset_chat_request(message: str) -> tuple[bool, str]:
    text = str(message or "")
    lowered = text.lower()
    for phrase in CHAT_RESET_COMMAND_PHRASES:
        index = lowered.find(phrase)
        if index < 0:
            continue
        remainder = f"{text[:index]} {text[index + len(phrase):]}"
        return True, remainder.strip(" .,!?:;-—")
    return False, text.strip()


def extract_similar_movie_query(message: str) -> str:
    text = str(message or "").strip()
    lowered = text.lower()
    for pattern in SIMILAR_MOVIE_PATTERNS:
        match = re.search(pattern, lowered, flags=re.IGNORECASE)
        if not match:
            continue
        title = match.group(1)
        title = re.sub(r"\b(фільм|фільми|кіно|movie|movies)\b", " ", title, flags=re.IGNORECASE)
        title = title.strip(" .,!?:;-—\"'«»")
        return MOVIE_TITLE_ALIASES.get(title.lower(), title)
    return ""


def resolve_known_title_alias(query: str) -> str:
    clean_query = clean_display_text(query)
    query_norm = clean_query.lower()
    alias = MOVIE_TITLE_ALIASES.get(query_norm)
    if alias:
        return alias
    for title_en, title_ua in TITLE_UA_MAP.items():
        title_ua_norm = clean_display_text(title_ua).lower()
        title_en_norm = clean_display_text(title_en).lower()
        if query_norm in {title_ua_norm, title_en_norm}:
            return title_en
        if len(query_norm) >= 4 and title_ua_norm and query_norm in title_ua_norm:
            return title_en
    return clean_query


def normalize_title_match_text(value: object) -> str:
    text = clean_display_text(value).lower()
    text = re.sub(r"[^a-zа-яіїєґ0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def title_match_tokens(value: object) -> list[str]:
    return [
        token
        for token in normalize_title_match_text(value).split()
        if len(token) >= 3 and token not in SIMILARITY_STOPWORDS
    ]


def resolve_movie_title_query(movies: pd.DataFrame, query: str) -> str:
    query = resolve_known_title_alias(query)
    if not query:
        return ""
    query_norm = query.lower()
    for column in ["title", "title_ua", "tmdb_title_ua", "tmdb_title"]:
        if column not in movies.columns:
            continue
        values = movies[column].fillna("").astype(str)
        exact = movies.loc[values.str.lower().eq(query_norm)]
        if not exact.empty:
            return str(exact.iloc[0].get("title", ""))
        contains = movies.loc[values.str.lower().str.contains(re.escape(query_norm), na=False)]
        if not contains.empty:
            return str(contains.iloc[0].get("title", ""))
    query_match = normalize_title_match_text(query)
    query_tokens = title_match_tokens(query)
    if not query_match and not query_tokens:
        return query

    best_title = ""
    best_score = 0.0
    best_popularity = -1.0
    for _, row in movies.iterrows():
        title = clean_display_text(row.get("title", ""))
        if not title:
            continue
        candidates = [
            title,
            row.get("title_ua", ""),
            row.get("tmdb_title_ua", ""),
            TITLE_UA_MAP.get(title, ""),
        ]
        candidate_text = normalize_title_match_text(" ".join(clean_display_text(value) for value in candidates))
        if not candidate_text:
            continue
        score = 0.0
        if query_match and query_match in candidate_text:
            score += 4.0
        candidate_tokens = set(candidate_text.split())
        overlap = sum(1 for token in query_tokens if token in candidate_tokens)
        score += overlap * 1.4
        for token in query_tokens:
            if len(token) >= 5 and any(part.startswith(token) or token.startswith(part) for part in candidate_tokens):
                score += 0.45
        if score <= 0:
            continue
        popularity = clean_rating(row.get("tmdb_popularity")) or 0.0
        if score > best_score or (score == best_score and popularity > best_popularity):
            best_score = score
            best_popularity = popularity
            best_title = title
    if best_title and best_score >= 1.4:
        return best_title
    return query


def extract_similar_movie_query(message: str) -> str:
    text = str(message or "").strip()
    lowered = text.lower()
    for pattern in SIMILAR_MOVIE_PATTERNS:
        match = re.search(pattern, lowered, flags=re.IGNORECASE)
        if not match:
            continue
        title = match.group(1)
        title = re.sub(r"\b(фільм|фільми|кіно|movie|movies)\b", " ", title, flags=re.IGNORECASE)
        title = re.split(
            r"\b(?:але|без|з\s+хорош|з\s+норм|щоб|тільки|only|with|without|but|and)\b",
            title,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
        title = title.strip(" .,!?:;-—\"'«»")
        return MOVIE_TITLE_ALIASES.get(title.lower(), title)
    return ""


def find_movie_row_by_title(movies: pd.DataFrame, title: str) -> Optional[pd.Series]:
    resolved = resolve_movie_title_query(movies, title)
    if not resolved:
        return None
    resolved_norm = resolved.lower()
    values = movies["title"].fillna("").astype(str)
    exact = movies.loc[values.str.lower().eq(resolved_norm)]
    if not exact.empty:
        return exact.iloc[0]
    contains = movies.loc[values.str.lower().str.contains(re.escape(resolved_norm), na=False)]
    if not contains.empty:
        return contains.iloc[0]
    return None


def build_similar_movie_query(movies: pd.DataFrame, seed_title: str, requested_query: str) -> str:
    row = find_movie_row_by_title(movies, seed_title)
    parts = [seed_title, requested_query, SIMILARITY_PROFILE_QUERIES.get(seed_title, "")]
    if row is not None:
        parts.extend(
            [
                clean_display_text(row.get("genres", "")),
                clean_display_text(row.get("director", "")),
                clean_display_text(row.get("tmdb_overview", "")),
                clean_display_text(row.get("features_text", "")),
            ]
        )
    return expand_query_text(" ".join(part for part in parts if part).strip())


def tokenize_similarity_terms(text: object, limit: int = 40) -> list[str]:
    tokens = re.findall(r"[a-zа-яіїєґ0-9]{3,}", clean_display_text(text).lower())
    terms: list[str] = []
    for token in tokens:
        if token in SIMILARITY_STOPWORDS or token.isdigit():
            continue
        if token not in terms:
            terms.append(token)
        if len(terms) >= limit:
            break
    return terms


def build_seed_similarity_profile(movies: Optional[pd.DataFrame], seed_title: str) -> dict[str, list[str]]:
    row = find_movie_row_by_title(movies, seed_title) if movies is not None else None
    profile_terms = list(SIMILARITY_PROFILE_BOOST_TERMS.get(seed_title, []))
    title_terms = tokenize_similarity_terms(seed_title, limit=8)
    genres: list[str] = []
    overview_terms: list[str] = []
    if row is not None:
        genres = [
            part.strip().lower()
            for part in clean_display_text(row.get("genres", "")).split(",")
            if part.strip()
        ]
        title_terms = tokenize_similarity_terms(row.get("title", seed_title), limit=8) or title_terms
        overview_terms = tokenize_similarity_terms(
            f"{row.get('tmdb_overview', '')} {row.get('features_text', '')}",
            limit=34,
        )
    terms = list(dict.fromkeys(profile_terms + title_terms + genres + overview_terms))
    return {"terms": terms, "title_terms": title_terms, "genres": genres}


def add_related_title_candidates(results: pd.DataFrame, seed_title: str, movies: pd.DataFrame) -> pd.DataFrame:
    related_titles = SIMILARITY_RELATED_TITLE_BOOSTS.get(seed_title, {})
    if movies is None or movies.empty or not related_titles:
        return results
    title_text = movies["title"].fillna("").astype(str).str.lower()
    related_score = pd.Series(0.0, index=movies.index)
    for term, score in related_titles.items():
        related_score = related_score.where(
            ~title_text.str.contains(re.escape(term), regex=True, na=False),
            related_score.combine(pd.Series(score, index=movies.index), max),
        )
    related = movies.loc[related_score.gt(0)].copy()
    if related.empty:
        return results
    related["semantic_similarity"] = related_score.loc[related.index].astype(float)
    combined = pd.concat([results, related], ignore_index=True)
    combined["_similar_key"] = (
        combined["title"].fillna("").astype(str).str.lower()
        + "|"
        + combined["year"].fillna("").astype(str)
    )
    combined = combined.sort_values("semantic_similarity", ascending=False, na_position="last")
    return combined.drop_duplicates("_similar_key", keep="first").drop(columns=["_similar_key"])


def apply_similar_profile_boost(results: pd.DataFrame, seed_title: str, movies: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    if results.empty:
        return results
    profile = build_seed_similarity_profile(movies, seed_title)
    terms = profile["terms"]
    title_terms = profile["title_terms"]
    seed_genres = profile["genres"]
    if not terms and not seed_genres:
        return results
    boosted = results.copy()
    if "semantic_similarity" not in boosted.columns:
        boosted["semantic_similarity"] = 0.0
    searchable = (
        boosted["title"].fillna("").astype(str).str.lower()
        + " "
        + boosted["genres"].fillna("").astype(str).str.lower()
        + " "
        + boosted.get("tmdb_overview", pd.Series("", index=boosted.index)).fillna("").astype(str).str.lower()
        + " "
        + boosted.get("features_text", pd.Series("", index=boosted.index)).fillna("").astype(str).str.lower()
    )
    title_text = boosted["title"].fillna("").astype(str).str.lower()
    genre_text = boosted["genres"].fillna("").astype(str).str.lower()
    profile_score = searchable.apply(
        lambda value: sum(
            1
            for term in terms
            if re.search(rf"\b{re.escape(term)}\b", value)
        )
    )
    genre_score = genre_text.apply(
        lambda value: sum(
            1
            for genre in seed_genres
            if genre and genre in value
        )
    )
    title_score = title_text.apply(
        lambda value: sum(
            1
            for term in title_terms
            if re.search(rf"\b{re.escape(term)}\b", value)
        )
    )
    franchise_terms = ["fast", "furious"] if seed_title in {"Fast X", "The Fast and the Furious"} else []
    franchise_score = title_text.apply(
        lambda value: 4 if franchise_terms and any(re.search(rf"\b{term}\b", value) for term in franchise_terms) else 0
    )
    boosted["semantic_similarity"] = (
        pd.to_numeric(boosted["semantic_similarity"], errors="coerce").fillna(0)
        + profile_score.clip(upper=12).astype(float) * 0.035
        + genre_score.clip(upper=3).astype(float) * 0.11
        + title_score.clip(upper=4).astype(float) * 0.13
        + franchise_score.astype(float) * 0.08
    )
    return boosted


def apply_required_similarity_terms(results: pd.DataFrame, seed_title: str) -> pd.DataFrame:
    terms = SIMILARITY_REQUIRED_TERMS.get(seed_title, [])
    if results.empty or not terms:
        return results
    filtered = results.copy()
    searchable = (
        filtered["title"].fillna("").astype(str).str.lower()
        + " "
        + filtered.get("genres", pd.Series("", index=filtered.index)).fillna("").astype(str).str.lower()
        + " "
        + filtered.get("tmdb_overview", pd.Series("", index=filtered.index)).fillna("").astype(str).str.lower()
        + " "
        + filtered.get("features_text", pd.Series("", index=filtered.index)).fillna("").astype(str).str.lower()
    )
    title_text = filtered["title"].fillna("").astype(str).str.lower()
    genre_text = filtered.get("genres", pd.Series("", index=filtered.index)).fillna("").astype(str).str.lower()

    def exact_term_count(value: str) -> int:
        return sum(1 for term in terms if re.search(rf"\b{re.escape(term)}\b", value))

    term_score = searchable.apply(exact_term_count)
    if seed_title in {"Fast X", "The Fast and the Furious"}:
        franchise_mask = title_text.str.contains(r"\bfast\b|\bfurious\b|hobbs|shaw", regex=True, na=False)
        action_mask = genre_text.str.contains("action|crime|thriller", regex=True, na=False)
        keep_mask = franchise_mask | ((term_score >= 2) & action_mask) | (term_score >= 3)
        strict = filtered.loc[keep_mask].copy()
        if len(strict) >= 6:
            strict_term_score = term_score.loc[strict.index]
            strict_franchise = franchise_mask.loc[strict.index].astype(float)
            strict_action = action_mask.loc[strict.index].astype(float)
            strict["semantic_similarity"] = (
                pd.to_numeric(strict.get("semantic_similarity", 0), errors="coerce").fillna(0)
                + strict_franchise * 2.0
                + strict_term_score.astype(float) * 0.22
                + strict_action * 0.12
            )
            return strict.sort_values("semantic_similarity", ascending=False, na_position="last")
        return filtered

    mask = term_score >= 1
    strict = filtered.loc[mask].copy()
    return strict if len(strict) >= 6 else filtered


def get_ai_chat_context() -> dict[str, object]:
    context = st.session_state.setdefault(
        "ai_chat_context",
        {"latest": False, "popular": False, "top": False, "quality": False, "genres": []},
    )
    for key in ["latest", "popular", "top", "quality"]:
        context.setdefault(key, False)
    context.setdefault("genres", [])
    return context


def reset_ai_chat_context() -> None:
    st.session_state["ai_chat_context"] = {"latest": False, "popular": False, "top": False, "quality": False, "genres": []}
    st.session_state["ai_sort_bias"] = ""


def get_chat_history_text() -> str:
    messages = st.session_state.get("chat_messages", [])
    return " ".join(
        str(message.get("content", "")).lower()
        for message in messages
        if message.get("role") == "user"
    )


def get_last_similar_movie_query_from_history() -> str:
    messages = st.session_state.get("chat_messages", [])
    for message in reversed(messages):
        if message.get("role") != "user":
            continue
        similar_query = extract_similar_movie_query(str(message.get("content", "")))
        if similar_query:
            return similar_query
    return ""


def is_clear_movie_request(message: str) -> bool:
    normalized = message.strip().lower()
    return len(normalized) >= 12 and any(term in normalized for term in CHAT_SIGNAL_TERMS)


def build_chat_reply(message: str, lang: str) -> tuple[str, Optional[str], list[str]]:
  """Build a reply for the chat and return (assistant_text, ai_query, exclude_terms).

  - `ai_query` is an expanded description suitable for `search_by_description`.
  - `exclude_terms` is a list of tokens/terms to be used for excluding results.
  """
  normalized = message.strip()
  if not normalized:
    return t(lang, "Напишіть, який фільм хочете знайти.", "Tell me what kind of movie you want."), None, []

  lowered = normalized.lower()
  compact = lowered.strip(" .,!?:;-")
  context = get_ai_chat_context()
  previous_sort_bias = st.session_state.get("ai_sort_bias", "")
  history_text = get_chat_history_text()
  previous_similar_title_query = st.session_state.get("ai_similar_title_query") or get_last_similar_movie_query_from_history()
  history_has_latest = context.get("latest") or previous_sort_bias == "latest" or text_has_any(history_text, CHAT_LATEST_TERMS)
  history_has_quality = context.get("quality") or text_has_any(history_text, CHAT_TOP_TERMS) or text_has_any(history_text, CHAT_QUALITY_TERMS)
  history_intents, _, _, _, _, _ = extract_query_intents(history_text)
  matched_intents, negative_terms, matched_topics, matched_moods, strict_only_genres, excluded_genres = extract_query_intents(normalized)
  current_genres = [genre for genre in context.get("genres", []) if isinstance(genre, str)]
  if excluded_genres:
    current_genres = [genre for genre in current_genres if genre not in excluded_genres]
  if history_intents or matched_intents:
    current_genres = list(dict.fromkeys(current_genres + history_intents + matched_intents))
    if excluded_genres:
      current_genres = [genre for genre in current_genres if genre not in excluded_genres]
    context["genres"] = current_genres
  message_has_specific_intent = bool(matched_intents or matched_topics or matched_moods or strict_only_genres or excluded_genres or current_genres)

  if is_reset_chat_request(lowered):
    reset_ai_chat_context()
    st.session_state["ai_query"] = ""
    st.session_state["ai_similar_title_query"] = ""
    st.session_state["ai_exclude_terms"] = []
    return (
      t(lang, "Ок, починаємо заново. Напишіть, який фільм хочете знайти.", "Okay, starting fresh. Tell me what kind of movie you want to find."),
      None,
      [],
    )

  if history_has_latest:
    context["latest"] = True
    st.session_state["ai_sort_bias"] = "latest"
  if history_has_quality:
    context["quality"] = True

  similar_title_query = extract_similar_movie_query(normalized)
  if similar_title_query:
    reset_ai_chat_context()
    st.session_state["ai_sort_bias"] = "similar"
    st.session_state["ai_similar_title_query"] = similar_title_query
    ai_query = expand_query_text(f"similar to {similar_title_query}") or f"similar to {similar_title_query}"
    return (
      t(
        lang,
        f"Зрозумів, шукаю фільми, схожі на {similar_title_query}.",
        f"Got it, I am finding movies similar to {similar_title_query}.",
      ),
      ai_query,
      [],
    )
  if not previous_similar_title_query:
    st.session_state["ai_similar_title_query"] = ""

  if compact in CHAT_GREETING_TERMS or text_has_any(lowered, CHAT_HELP_TERMS):
    return (
      t(
        lang,
        "Привіт! Я можу підібрати фільм за жанром, настроєм, роком, новизною або тим, що треба прибрати. Наприклад: новинки, топ жахів, щось легке для вечора, бойовик без магії.",
        "Hi! I can find movies by genre, mood, year, freshness, or things to avoid. For example: new releases, top horror, something light for tonight, action without magic.",
      ),
      None,
      [],
    )

  if compact in CHAT_THANKS_TERMS:
    return (
      t(lang, "Будь ласка. Напишіть, який настрій або жанр хочете, і я підберу фільми.", "You are welcome. Tell me the mood or genre you want, and I will find movies."),
      None,
      [],
    )

  if text_has_any(lowered, CHAT_LATEST_TERMS):
    context["latest"] = True
    context["popular"] = False
    context["top"] = False
    st.session_state["ai_sort_bias"] = "similar_latest" if previous_similar_title_query else "latest"
    if previous_similar_title_query:
      st.session_state["ai_similar_title_query"] = previous_similar_title_query
      return (
        t(
          lang,
          f"Зрозумів, залишаю схожість на {previous_similar_title_query}, але піднімаю новіші фільми.",
          f"Got it, I am keeping similarity to {previous_similar_title_query}, but prioritizing newer movies.",
        ),
        st.session_state.get("ai_query") or (expand_query_text(f"similar to {previous_similar_title_query}") or f"similar to {previous_similar_title_query}"),
        [],
      )
    if not message_has_specific_intent:
      return (
        t(
          lang,
          "Зрозумів, шукаю новіші фільми і піднімаю вгору найсвіжіші роки. Якщо хочете, можна додати жанр: наприклад, новий хорор або свіжа комедія.",
          "Got it, I am looking for newer movies and prioritizing the latest years. You can add a genre too, for example new horror or fresh comedy.",
        ),
        expand_query_text("new recent release popular movie") or "new recent release popular movie",
        [],
      )

  if text_has_any(lowered, CHAT_POPULAR_TERMS):
    context["popular"] = True
    context["top"] = False
    st.session_state["ai_sort_bias"] = "popular"
    if not message_has_specific_intent:
      return (
        t(lang, "Ок, підбираю популярні фільми і сортую їх за популярністю.", "Okay, I am finding popular movies and sorting them by popularity."),
        expand_query_text("popular trending movie") or "popular trending movie",
        [],
      )

  if text_has_any(lowered, CHAT_TOP_TERMS) or text_has_any(lowered, CHAT_QUALITY_TERMS):
    context["quality"] = True
    if history_has_latest or context.get("latest") or previous_sort_bias == "latest":
      st.session_state["ai_sort_bias"] = "latest"
      if not message_has_specific_intent:
        return (
          t(
            lang,
            "Ок, залишаю запит на новинки, але тепер піднімаю серед найновіших фільмів ті, що мають кращі рейтинги.",
            "Okay, I am keeping the new-release request, but now prioritizing better-rated movies among the newest results.",
          ),
          st.session_state.get("ai_query") or (expand_query_text("new recent release popular movie") or "new recent release popular movie"),
          [],
        )
    else:
      st.session_state["ai_sort_bias"] = "top"
      context["top"] = True
      if not message_has_specific_intent:
        return (
          t(lang, "Ок, підбираю фільми з сильними оцінками та кращими рейтингами.", "Okay, I am finding movies with strong ratings and better scores."),
          expand_query_text("top rated best movie") or "top rated best movie",
          [],
        )

  # If message seems too short or unclear, ask for clarification but still try to extract hints
  if not is_clear_movie_request(normalized) and not message_has_specific_intent:
    # Try lightweight extraction to help user without forcing clarification
    _, negative_terms, _, _, _, excluded_genres = extract_query_intents(normalized)
    hard_neg = get_hard_negative_terms(normalized)
    excludes = list(dict.fromkeys(negative_terms + hard_neg + excluded_genres))
    if excludes:
      # if we found negations we can still produce a query
      ai_query = expand_query_text(normalized) or normalized
      return (
        t(
          lang,
          "Я трохи уточнив запит і застосував виключення. Можете додати деталі, якщо потрібно.",
          "I parsed a few exclusions and adapted the query. Add more details if needed.",
        ),
        ai_query,
        excludes,
      )

    return (
      t(
        lang,
        "Я ще не зовсім розумію тематику. Уточніть жанр, настрій або що точно не потрібно: наприклад, напружений бойовик без магії.",
        "I do not fully understand the theme yet. Add a genre, mood, or what to avoid: for example, tense action without magic.",
      ),
      None,
      [],
    )

  # Build an expanded query and extract negatives to improve ranking and exclusion
  genre_query = " ".join(current_genres)
  context_query_parts = []
  if context.get("latest") or history_has_latest or previous_sort_bias == "latest":
    context_query_parts.append("new recent release latest newest")
  if context.get("quality") or history_has_quality:
    context_query_parts.append("top rated good rating quality")
  if context.get("popular") or previous_sort_bias == "popular":
    context_query_parts.append("popular trending")
  combined_query = " ".join(part for part in [*context_query_parts, normalized, genre_query] if part)
  ai_query = expand_query_text(combined_query) or combined_query or normalized
  _, negative_terms, _, _, _, excluded_genres = extract_query_intents(combined_query)
  hard_neg = get_hard_negative_terms(normalized)
  excludes = list(dict.fromkeys(negative_terms + hard_neg + excluded_genres))

  if context.get("quality") and current_genres:
    reply_text = t(
      lang,
      "Ок, враховую жанр і рейтинг одночасно: спочатку фільтрую за жанром, потім піднімаю фільми з кращими оцінками.",
      "Okay, I am combining genre and rating: first filtering by genre, then prioritizing better-rated movies.",
    )
  elif context.get("latest") and current_genres:
    reply_text = t(
      lang,
      "Зрозумів, шукаю новіші фільми саме в цьому жанрі.",
      "Got it, I am looking for newer movies in this genre.",
    )
  else:
    reply_text = t(
      lang,
      "Зрозумів. Я застосував це як AI-запит і оновив рекомендації зліва. Якщо треба, напишіть, що прибрати або додати.",
      "Got it. I applied this as an AI query and updated the recommendations on the left. Tell me what to add or remove if needed.",
    )

  return (
    reply_text,
    ai_query,
    excludes,
  )


def get_chat_greeting(lang: str) -> str:
    return t(
        lang,
        "Привіт. Напишіть, що хочете подивитися, а я уточню деталі або одразу підберу фільми.",
        "Hi. Tell me what you want to watch, and I will ask for details or find movies right away.",
    )


def get_chat_messages(lang: str) -> list[dict[str, str]]:
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = [{"role": "assistant", "content": get_chat_greeting(lang)}]
    return st.session_state["chat_messages"]


def normalize_chat_messages(messages: object, lang: str) -> list[dict[str, str]]:
    clean_messages: list[dict[str, str]] = []
    if isinstance(messages, list):
        for message in messages:
            if not isinstance(message, dict):
                continue
            role = str(message.get("role", "")).strip()
            content = str(message.get("content", "")).strip()
            if role in {"assistant", "user"} and content:
                clean_messages.append({"role": role, "content": content[:900]})
    if not clean_messages:
        clean_messages = [{"role": "assistant", "content": get_chat_greeting(lang)}]
    return clean_messages[-30:]


def encode_chat_memory(messages: list[dict[str, str]]) -> str:
    payload = json.dumps(normalize_chat_messages(messages, st.session_state.get("lang", "UA")), ensure_ascii=False)
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")


def decode_chat_memory(value: object, lang: str) -> list[dict[str, str]]:
    if isinstance(value, list):
        value = value[0] if value else ""
    try:
        raw = base64.urlsafe_b64decode(str(value or "").encode("ascii")).decode("utf-8")
        return normalize_chat_messages(json.loads(raw), lang)
    except (ValueError, TypeError, json.JSONDecodeError):
        return []


def hydrate_chat_memory_from_query(lang: str) -> None:
    if is_reset_chat_request(st.query_params.get("ai_message")):
        return
    decoded = decode_chat_memory(st.query_params.get("chat_memory"), lang)
    if decoded and len(decoded) >= len(st.session_state.get("chat_messages", [])):
        st.session_state["chat_messages"] = decoded


def refresh_ai_exclusions_from_history() -> None:
    if is_reset_chat_request(st.query_params.get("ai_message")):
        return
    history_text = get_chat_history_text()
    if not history_text:
        return
    similar_title_query = get_last_similar_movie_query_from_history()
    if similar_title_query:
        st.session_state["ai_similar_title_query"] = similar_title_query
        st.session_state["ai_sort_bias"] = "similar"
        st.session_state["ai_query"] = expand_query_text(f"similar to {similar_title_query}") or f"similar to {similar_title_query}"
    matched_intents, negative_terms, _, _, _, excluded_genres = extract_query_intents(history_text)
    hard_neg = get_hard_negative_terms(history_text)
    current_excludes = st.session_state.get("ai_exclude_terms", []) or []
    st.session_state["ai_exclude_terms"] = list(dict.fromkeys(current_excludes + negative_terms + hard_neg + excluded_genres))

    context = get_ai_chat_context()
    current_genres = [genre for genre in context.get("genres", []) if isinstance(genre, str)]
    if matched_intents:
        current_genres = list(dict.fromkeys(current_genres + matched_intents))
    if excluded_genres:
        current_genres = [genre for genre in current_genres if genre not in excluded_genres]
    context["genres"] = current_genres
    if text_has_any(history_text, CHAT_LATEST_TERMS):
        context["latest"] = True
        st.session_state["ai_sort_bias"] = "similar_latest" if similar_title_query else "latest"
    if text_has_any(history_text, CHAT_QUALITY_TERMS) or text_has_any(history_text, CHAT_TOP_TERMS):
        context["quality"] = True
    if text_has_any(history_text, CHAT_POPULAR_TERMS) and not context.get("latest"):
        context["popular"] = True
        st.session_state["ai_sort_bias"] = "popular"


def submit_chat_message(chat_text: str, lang: str) -> None:
    text = chat_text.strip()
    if not text:
        return

    reset_requested, reset_remainder = split_reset_chat_request(text)
    if reset_requested:
        reset_ai_chat_context()
        st.session_state["ai_query"] = ""
        st.session_state["ai_similar_title_query"] = ""
        st.session_state["ai_exclude_terms"] = []
        st.session_state["title_query"] = ""
        st.session_state["page"] = 1
        st.session_state["chat_messages"] = []
        st.session_state["chat_open"] = True
        if not reset_remainder:
            st.session_state["chat_messages"] = [
                {"role": "user", "content": text},
                {
                    "role": "assistant",
                    "content": t(
                        lang,
                        "Ок, усе забув. Починаємо з чистого аркуша: напишіть, який фільм хочете знайти.",
                        "Okay, I forgot everything. Starting fresh: tell me what kind of movie you want to find.",
                    ),
                },
            ]
            return
        text = reset_remainder

    messages = get_chat_messages(lang)
    messages.append({"role": "user", "content": text})
    reply, query, excludes = build_chat_reply(text, lang)
    messages.append({"role": "assistant", "content": reply})
    st.session_state["chat_open"] = True

    if query:
        st.session_state["ai_query"] = query
        st.session_state["ai_exclude_terms"] = excludes or []
        st.session_state["page"] = 1
    else:
        st.session_state["ai_exclude_terms"] = []


def clear_ai_selection_state(lang: str) -> None:
    reset_ai_chat_context()
    st.session_state["ai_query"] = ""
    st.session_state["ai_similar_title_query"] = ""
    st.session_state["ai_exclude_terms"] = []
    st.session_state["ai_sort_bias"] = ""
    st.session_state["last_hero_ai_submit"] = ""
    st.session_state["chat_messages"] = [{"role": "assistant", "content": get_chat_greeting(lang)}]


def render_ai_chat_panel(lang: str) -> None:
    st.session_state.setdefault("chat_open", False)
    messages = get_chat_messages(lang)

    if not st.session_state["chat_open"]:
        return

    with st.container(key="floating_ai_chat_open"):
        title_col, close_col = st.columns([5, 1], vertical_alignment="top")
        with title_col:
            st.markdown(
                f"""
<div class="ms-chat-panel">
  <div class="ms-chat-title">{html.escape(t(lang, "AI-чат", "AI chat"))}</div>
  <div class="ms-chat-subtitle">{html.escape(t(lang, "Пишіть природно. Якщо запит розмитий, я поставлю уточнення.", "Write naturally. If the request is vague, I will ask a follow-up."))}</div>
</div>
                """,
                unsafe_allow_html=True,
            )
        with close_col:
            if st.button("×", key="close_ai_chat", use_container_width=True):
                st.session_state["chat_open"] = False
                st.rerun()

        message_slot = st.empty()
        # Quick suggestion prompts to help users craft good AI descriptions
        suggestions = [
          (t(lang, "Напружений бойовик без магії", "Tense action without magic"), "напружений бойовик без магії"),
          (t(lang, "Тепла сімейна комедія", "Warm family comedy"), "сімейна комедія для всієї родини"),
          (t(lang, "Темний психологічний трилер", "Dark psychological thriller"), "темний психологічний трилер з несподіваним фіналом"),
        ]
        sugg_cols = st.columns(min(len(suggestions), 3))
        for idx, (label, qtext) in enumerate(suggestions):
            col = sugg_cols[idx % len(sugg_cols)]
            if col.button(label, key=f"ai_sugg_{idx}"):
                ai_q = expand_query_text(qtext) or qtext
                _, negative_terms, _, _, _, excluded_genres = extract_query_intents(qtext)
                hard_neg = get_hard_negative_terms(qtext)
                excludes = list(dict.fromkeys(negative_terms + hard_neg + excluded_genres))
                st.session_state["ai_query"] = ai_q
                st.session_state["ai_exclude_terms"] = excludes
                st.session_state.setdefault("chat_messages", [])
                st.session_state["chat_messages"].append({"role": "assistant", "content": t(lang, "Застосував шаблонний запит для підбору фільмів.", "Applied a template query to find movies.")})
                st.session_state["page"] = 1
                st.rerun()
        with st.form("ai_chat_form", clear_on_submit=True):
            chat_text = st.text_area(
                t(lang, "Повідомлення", "Message"),
                placeholder=t(lang, "Наприклад: хочу щось напружене, але без магії", "For example: I want something tense, but without magic"),
                height=82,
            )
            sent = st.form_submit_button(t(lang, "Надіслати", "Send"), use_container_width=True)
            if sent and chat_text.strip():
                submit_chat_message(chat_text, lang)
                st.rerun()

        message_html = []
        for index, message in enumerate(messages[-8:]):
            role_class = "ms-chat-user" if message["role"] == "user" else "ms-chat-ai"
            typing_class = " ms-chat-typing" if index == 0 and len(messages) == 1 and message["role"] == "assistant" else ""
            content = html.escape(message["content"])
            if typing_class:
                content = f"<span>{content}</span><span class=\"ms-chat-cursor\"></span>"
            message_html.append(f'<div class="ms-chat-msg {role_class}{typing_class}">{content}</div>')
        message_slot.markdown(f'<div class="ms-chat-scroll">{"".join(message_html)}</div>', unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title="AI Multimedia Recommender", layout="wide")
    inject_css()

    st.session_state.setdefault("lang", "UA")
    st.session_state.setdefault("selected_movie", None)
    st.session_state.setdefault("show_movie_details", False)
    st.session_state.setdefault("page", 1)
    st.session_state.setdefault("ai_query", "")
    st.session_state.setdefault("ai_similar_title_query", "")
    st.session_state.setdefault("ai_exclude_terms", [])
    st.session_state.setdefault("ai_sort_bias", "")
    st.session_state.setdefault("ai_chat_context", {"latest": False, "popular": False, "top": False, "quality": False, "genres": []})
    st.session_state.setdefault("title_query", "")
    st.session_state.setdefault("current_user", None)
    st.session_state.setdefault("view", "home")
    st.session_state.setdefault("chat_open", False)
    hydrate_lang_from_query()
    hydrate_current_user_from_query()

    lang = st.session_state["lang"]
    if st.query_params.get("profile_logout"):
        clear_current_user()
        st.session_state["view"] = "home"
        st.session_state["selected_movie"] = None
        st.session_state["show_movie_details"] = False
        del st.query_params["profile_logout"]
        if "app_view" in st.query_params:
            del st.query_params["app_view"]
        st.rerun()

    if st.query_params.get("open_chat"):
        st.query_params["hero_panel"] = "ai"
        del st.query_params["open_chat"]

    requested_view = str(st.query_params.get("app_view") or "").strip()
    if requested_view in {"auth", "profile"}:
        st.session_state["view"] = requested_view
        st.session_state["selected_movie"] = None
        st.session_state["show_movie_details"] = False
        if "app_view" in st.query_params:
            del st.query_params["app_view"]

    if st.session_state.get("view") == "auth":
        render_auth_page(lang)
        return

    movies = get_movies(APP_MOVIE_CATALOG_CACHE_VERSION)

    if st.query_params.get("movie"):
        st.session_state["view"] = "home"

    if st.session_state.get("view") == "profile":
        render_profile_page(movies, lang)
        return

    movie_param = st.query_params.get("movie")
    add_watch_later_param = first_query_value(st.query_params.get("add_watch_later"))
    if add_watch_later_param and get_current_user():
        add_watch_later(get_current_user(), urllib.parse.unquote(add_watch_later_param))
        del st.query_params["add_watch_later"]
        st.rerun()

    if movie_param:
        if isinstance(movie_param, list):
            movie_param = movie_param[0] if movie_param else ""
        st.session_state["selected_movie"] = urllib.parse.unquote(str(movie_param))
        st.session_state["show_movie_details"] = True
        st.session_state["chat_open"] = False
        details_view(movies, lang)
        return
    if st.session_state.get("show_movie_details") and st.session_state.get("selected_movie"):
        st.session_state["chat_open"] = False
        details_view(movies, lang)
        return

    hero_row = movies.sample(1).iloc[0] if not movies.empty else None
    hero_bg = ""
    if hero_row is not None:
        hero_bg = get_backdrop(hero_row) or get_poster_display(hero_row, "EN") or ""

    movies_with_posters = movies[has_display_poster_frame(movies)].copy()
    all_genres = sorted({genre.strip() for genres in movies_with_posters["genres"].fillna("") for genre in str(genres).split(",") if genre.strip()})
    genre_option_map = {translate_genres(genre, lang): genre for genre in all_genres}
    y_min = int(np.nanmin(movies["year"])) if movies["year"].notna().any() else 1900
    y_max = int(np.nanmax(movies["year"])) if movies["year"].notna().any() else 2025
    hero_panel = str(st.query_params.get("hero_panel") or "").strip()
    if hero_panel != "title" and st.session_state.get("title_query"):
        st.session_state["title_query"] = ""
    if hero_panel != "ai" and (
        st.session_state.get("ai_query")
        or st.session_state.get("ai_similar_title_query")
        or st.session_state.get("ai_exclude_terms")
        or st.session_state.get("ai_sort_bias")
    ):
        clear_ai_selection_state(lang)
    active_ai_query = st.session_state.get("ai_query", "").strip()
    sort_options = [
        t(lang, "За популярністю", "By popularity"),
        t(lang, "За IMDb рейтингом", "By IMDb"),
        t(lang, "За TMDB рейтингом", "By TMDB"),
    ]
    if active_ai_query:
        sort_options.insert(1, t(lang, "За AI-релевантністю", "By AI relevance"))

    title_search = st.query_params.get("title_search")
    if title_search is not None:
        st.session_state["title_query"] = str(title_search).strip()
        st.session_state["page"] = 1

    hydrate_chat_memory_from_query(lang)
    ai_message = str(st.query_params.get("ai_message") or "").strip()
    if ai_message:
        submit_signature = f"{AI_CHAT_LOGIC_VERSION}|{ai_message}|{st.query_params.get('chat_memory') or ''}"
        if st.session_state.get("last_hero_ai_submit") != submit_signature:
            submit_chat_message(ai_message, lang)
            st.session_state["last_hero_ai_submit"] = submit_signature
    else:
        st.session_state["last_hero_ai_submit"] = ""
    refresh_ai_exclusions_from_history()

    selected_genre = str(st.query_params.get("genre") or "").strip()
    genres = [selected_genre] if selected_genre in all_genres else []
    if selected_genre:
        selected_intents, _, _, _, _, selected_excluded = extract_query_intents(selected_genre)
        ai_excludes_for_controls = st.session_state.get("ai_exclude_terms", []) or []
        if any(intent in ai_excludes_for_controls for intent in selected_intents) or selected_genre.lower() in {
            term for genre in ai_excludes_for_controls for term in content_based.STRICT_GENRE_TERMS.get(str(genre), [])
        }:
            genres = []

    def query_int(name: str, default: int) -> int:
        try:
            return int(float(str(st.query_params.get(name) or default)))
        except (TypeError, ValueError):
            return default

    year_from = max(y_min, min(query_int("year_min", y_min), y_max))
    year_to = max(y_min, min(query_int("year_max", y_max), y_max))
    year_range = (min(year_from, year_to), max(year_from, year_to))
    requested_sort = str(st.query_params.get("sort_by") or "").strip()
    sort_by = requested_sort if requested_sort in sort_options else sort_options[0]

    title_card_class = "ms-hero-card ms-hero-card-link" + (" ms-hero-card-active" if hero_panel == "title" else "")
    filter_card_class = "ms-hero-card ms-hero-card-link" + (" ms-hero-card-active" if hero_panel == "filters" else "")
    ai_card_class = "ms-hero-card ms-hero-card-link" + (" ms-hero-card-active" if hero_panel == "ai" else "")
    title_panel_href = panel_switch_href("title")
    filters_panel_href = panel_switch_href("filters")
    ai_panel_href = panel_switch_href("ai")
    auth_input_html = auth_hidden_input()
    lang_input_html = lang_hidden_input()

    hero_panel_html = ""
    if hero_panel == "title":
        hero_panel_html = f"""
      <div class="ms-hero-panel">
        <form class="ms-hero-form" method="get">
          <input type="hidden" name="hero_panel" value="title" />
          {auth_input_html}
          {lang_input_html}
          <label class="ms-hero-field">
            <span>{html.escape(t(lang, "Знайти фільм за назвою", "Find a movie by title"))}</span>
            <textarea class="ms-hero-input ms-hero-title-textarea" name="title_search" placeholder="{html.escape(t(lang, "Назва фільму...", "Movie title..."), quote=True)}">{html.escape(st.session_state.get("title_query", ""))}</textarea>
          </label>
          <button class="ms-hero-submit" type="submit">{html.escape(t(lang, "Шукати", "Search"))}</button>
        </form>
      </div>
        """
    elif hero_panel == "filters":
        genre_options = [
            f'<button class="ms-genre-option{" ms-genre-option-active" if not selected_genre else ""}" type="submit" name="genre" value="">{html.escape(t(lang, "Усі жанри", "All genres"))}</button>'
        ]
        for genre in all_genres:
            active_class = " ms-genre-option-active" if genre == selected_genre else ""
            genre_options.append(f'<button class="ms-genre-option{active_class}" type="submit" name="genre" value="{html.escape(genre, quote=True)}">{html.escape(translate_genres(genre, lang))}</button>')
        sort_options_html = []
        for option in sort_options:
            selected = " selected" if option == sort_by else ""
            sort_options_html.append(f'<option value="{html.escape(option, quote=True)}"{selected}>{html.escape(option)}</option>')
        year_min_options_html = []
        year_max_options_html = []
        for year in range(y_min, y_max + 1):
            min_selected = " selected" if year == year_range[0] else ""
            max_selected = " selected" if year == year_range[1] else ""
            year_min_options_html.append(f'<option value="{year}"{min_selected}>{year}</option>')
            year_max_options_html.append(f'<option value="{year}"{max_selected}>{year}</option>')
        hero_panel_html = f"""
      <div class="ms-hero-panel">
        <form class="ms-hero-form ms-hero-filter-form" method="get">
          <input type="hidden" name="hero_panel" value="filters" />
          {auth_input_html}
          {lang_input_html}
          <label class="ms-hero-field">
            <span>{html.escape(t(lang, "Жанр", "Genre"))}</span>
            <details class="ms-genre-dropdown">
              <summary class="ms-hero-select">{html.escape(translate_genres(selected_genre, lang) if selected_genre else t(lang, "Усі жанри", "All genres"))}</summary>
              <div class="ms-genre-menu">{"".join(genre_options)}</div>
            </details>
          </label>
          <label class="ms-hero-field">
            <span>{html.escape(t(lang, "Від року", "From year"))}</span>
            <select class="ms-hero-select" name="year_min">{"".join(year_min_options_html)}</select>
          </label>
          <label class="ms-hero-field">
            <span>{html.escape(t(lang, "До року", "To year"))}</span>
            <select class="ms-hero-select" name="year_max">{"".join(year_max_options_html)}</select>
          </label>
          <label class="ms-hero-field">
            <span>{html.escape(t(lang, "Сортування", "Sort"))}</span>
            <select class="ms-hero-select" name="sort_by">{"".join(sort_options_html)}</select>
          </label>
          <button class="ms-hero-submit" type="submit">{html.escape(t(lang, "Застосувати", "Apply"))}</button>
        </form>
      </div>
        """
    elif hero_panel == "ai":
        messages_html = []
        for message in reversed(get_chat_messages(lang)):
            role_class = "ms-chat-user" if message["role"] == "user" else "ms-chat-ai"
            messages_html.append(f'<div class="ms-chat-msg {role_class}">{html.escape(message["content"])}</div>')
        chat_memory = html.escape(encode_chat_memory(get_chat_messages(lang)), quote=True)
        hero_panel_html = f"""
      <div class="ms-hero-panel">
        <div class="ms-chat-scroll">{"".join(messages_html)}</div>
        <form class="ms-hero-form ms-hero-ai-form" method="get">
          <input type="hidden" name="hero_panel" value="ai" />
          {auth_input_html}
          {lang_input_html}
          <input type="hidden" name="chat_memory" value="{chat_memory}" />
          <label class="ms-hero-field">
            <span>{html.escape(t(lang, "AI-запит", "AI request"))}</span>
            <textarea class="ms-hero-input ms-hero-textarea" name="ai_message" placeholder="{html.escape(t(lang, "Опишіть, який фільм хочете знайти...", "Describe what kind of movie you want..."), quote=True)}"></textarea>
          </label>
          <button class="ms-hero-submit" type="submit">{html.escape(t(lang, "Надіслати", "Send"))}</button>
        </form>
      </div>
        """

    hero_panel_html = "\n".join(line.lstrip() for line in hero_panel_html.splitlines())

    title_col, account_col = st.columns([6, 1.2], vertical_alignment="top")
    with title_col:
        hero_html = f"""
<div class="ms-hero">
  <div class="ms-hero-content">
    <div class="ms-hero-text">
      <div class="ms-hero-copy-topline">{html.escape(t(lang, "AI-пошук + інтелектуальні фільтри для вибору ідеального фільму", "AI search + smart filters for choosing the ideal movie"))}</div>
    </div>
    <div class="ms-hero-center">
      <div class="ms-hero-copy-header">
        <h1>{html.escape(t(lang, "AI-рекомендації фільмів", "AI movie recommendations"))}</h1>
      </div>
      <p>{html.escape(t(lang, "Шукайте за назвою, жанром або власним описом настрою, а система підбере найближчі фільми з каталогу.", "Search by title, genre or your own mood description, and the system will find the closest movies in the catalog."))}</p>
      <div class="ms-hero-card-row" style="display: flex; flex-wrap: wrap; justify-content: center; gap: 16px; margin-top: 18px;">
        <a class="{title_card_class}" href="{html.escape(title_panel_href, quote=True)}" target="_self" style="flex: 1 1 180px; min-width: 180px;">
          <div class="ms-hero-card-value">{html.escape(t(lang, "Назва", "Title"))}</div>
          <div class="ms-hero-card-label">{html.escape(t(lang, "Знайди фільм по назві", "Find a movie by title"))}</div>
        </a>
        <a class="{filter_card_class}" href="{html.escape(filters_panel_href, quote=True)}" target="_self" style="flex: 1 1 180px; min-width: 180px;">
          <div class="ms-hero-card-value">{html.escape(t(lang, "Фільтри", "Filters"))}</div>
          <div class="ms-hero-card-label">{html.escape(t(lang, "Оберіть жанр, рік та AI-режим", "Choose genre, year, and AI mode"))}</div>
        </a>
        <a class="{ai_card_class}" href="{html.escape(ai_panel_href, quote=True)}" target="_self" style="flex: 1 1 180px; min-width: 180px;">
          <div class="ms-hero-card-value">AI</div>
          <div class="ms-hero-card-label">{html.escape(t(lang, "Опишіть настрій фільму", "Describe the movie mood"))}</div>
        </a>
      </div>
{hero_panel_html}
    </div>
  </div>
</div>
"""
        hero_html = "\n".join(line.lstrip() for line in hero_html.splitlines())
        st.markdown(hero_html, unsafe_allow_html=True)
    with account_col:
        current_user = get_current_user()
        account_label = t(lang, "Профіль", "Profile") if current_user else t(lang, "Увійти", "Login")
        account_href = app_view_href("profile" if current_user else "auth")
        st.markdown(
            f"""
<div class="ms-account-actions">
  {inline_language_switch_html(lang)}
  <a class="ms-account-login-link" href="{html.escape(account_href, quote=True)}" target="_self">{html.escape(account_label)}</a>
</div>
            """,
            unsafe_allow_html=True,
        )
    active_ai_query = st.session_state.get("ai_query", "").strip()
    movies_with_posters = movies[has_display_poster_frame(movies)].copy()
    all_genres = sorted({genre.strip() for genres in movies_with_posters["genres"].fillna("") for genre in str(genres).split(",") if genre.strip()})
    genre_option_map = {translate_genres(genre, lang): genre for genre in all_genres}
    y_min = int(np.nanmin(movies["year"])) if movies["year"].notna().any() else 1900
    y_max = int(np.nanmax(movies["year"])) if movies["year"].notna().any() else 2025
    sort_options = [
        t(lang, "За популярністю", "By popularity"),
        t(lang, "За IMDb рейтингом", "By IMDb"),
        t(lang, "За TMDB рейтингом", "By TMDB"),
    ]
    if active_ai_query:
        sort_options.insert(1, t(lang, "За AI-релевантністю", "By AI relevance"))

    if "genres" not in locals():
        genres = []
    if "year_range" not in locals():
        year_range = (y_min, y_max)
    if "sort_by" not in locals():
        sort_by = sort_options[0]

    ai_query = st.session_state.get("ai_query", "").strip()
    similar_title_query = st.session_state.get("ai_similar_title_query", "").strip()
    ai_sort_bias = st.session_state.get("ai_sort_bias", "")
    ai_context = get_ai_chat_context()
    ai_filter_text = " ".join(part for part in [ai_query, get_chat_history_text()] if part)
    if ai_query.strip() and not similar_title_query and text_has_any(ai_filter_text.lower(), CHAT_LATEST_TERMS):
        ai_context["latest"] = True
        ai_sort_bias = "latest"
        st.session_state["ai_sort_bias"] = "latest"
    if ai_query.strip() and (text_has_any(ai_filter_text.lower(), CHAT_QUALITY_TERMS) or text_has_any(ai_filter_text.lower(), CHAT_TOP_TERMS)):
        ai_context["quality"] = True
    _, ai_negative_terms, _, _, _, ai_excluded_from_text = extract_query_intents(ai_filter_text)
    ai_hard_negatives = get_hard_negative_terms(ai_filter_text)
    ai_excludes = list(dict.fromkeys((st.session_state.get("ai_exclude_terms", []) or []) + ai_negative_terms + ai_hard_negatives + ai_excluded_from_text))
    if ai_excludes != st.session_state.get("ai_exclude_terms", []):
        st.session_state["ai_exclude_terms"] = ai_excludes
    if ai_excluded_from_text:
        ai_context["genres"] = [
            genre for genre in ai_context.get("genres", [])
            if isinstance(genre, str) and genre not in ai_excluded_from_text
        ]
    if ai_excludes:
        ai_excluded_terms = {
            term
            for genre in ai_excludes
            for term in content_based.STRICT_GENRE_TERMS.get(str(genre), [])
        }
        selected_genre_key = selected_genre.lower()
        if selected_genre_key in ai_excluded_terms:
            genres = []

    if similar_title_query:
        seed_title = resolve_movie_title_query(movies, similar_title_query)
        _, tfidf_matrix, cosine_sim = get_similarity(movies)
        filtered = content_based.get_content_recommendations(
            seed_title,
            top_n=min(len(movies), 250),
            movies=movies,
            tfidf_matrix=tfidf_matrix,
            cosine_sim=cosine_sim,
        )
        if "similarity" in filtered.columns:
            filtered = filtered.rename(columns={"similarity": "semantic_similarity"})
        similar_description = build_similar_movie_query(movies, seed_title, similar_title_query)
        if similar_description:
            tfidf, tfidf_matrix, _ = get_similarity(movies)
            semantic_matches = content_based.search_by_description(
                similar_description,
                movies=movies,
                tfidf=tfidf,
                tfidf_matrix=tfidf_matrix,
                top_n=min(len(movies), 250),
            )
            if not semantic_matches.empty:
                filtered = pd.concat([filtered, semantic_matches], ignore_index=True)
                filtered["_similar_key"] = (
                    filtered["title"].fillna("").astype(str).str.lower()
                    + "|"
                    + filtered["year"].fillna("").astype(str)
                )
                filtered = filtered.sort_values("semantic_similarity", ascending=False, na_position="last")
                filtered = filtered.drop_duplicates("_similar_key", keep="first").drop(columns=["_similar_key"])
        filtered = add_related_title_candidates(filtered, seed_title, movies)
        filtered = apply_similar_profile_boost(filtered, seed_title, movies)
        filtered = apply_required_similarity_terms(filtered, seed_title)
        filtered = filtered[
            filtered["title"].fillna("").astype(str).str.lower() != str(seed_title).lower()
        ].copy()
        filtered = filtered[has_display_poster_frame(filtered)].copy()
        if filtered.empty and ai_query.strip():
            tfidf, tfidf_matrix, _ = get_similarity(movies)
            filtered = content_based.search_by_description(
                ai_query,
                movies=movies,
                tfidf=tfidf,
                tfidf_matrix=tfidf_matrix,
                top_n=min(len(movies), 250),
            )
            filtered = filtered[has_display_poster_frame(filtered)].copy()
    elif ai_query.strip() and ai_sort_bias in {"latest", "popular", "top"}:
        filtered = movies_with_posters.copy()
    elif ai_query.strip():
        tfidf, tfidf_matrix, _ = get_similarity(movies)
        filtered = content_based.search_by_description(
            ai_query,
            movies=movies,
            tfidf=tfidf,
            tfidf_matrix=tfidf_matrix,
            top_n=min(len(movies), 250),
        )
        filtered = filtered[has_display_poster_frame(filtered)].copy()
        # apply any exclude terms extracted from the AI chat
        if ai_excludes and not filtered.empty:
            searchable = (
                filtered["features_text"].fillna("").astype(str).str.lower()
                + " "
                + filtered["genres"].fillna("").astype(str).str.lower()
                + " "
                + filtered.get("tmdb_overview", pd.Series("", index=filtered.index)).fillna("").astype(str).str.lower()
            )
            exclude_mask = searchable.apply(lambda value: any(str(term).lower() in value for term in ai_excludes))
            filtered = filtered.loc[~exclude_mask].copy()
    else:
        filtered = movies_with_posters.copy()

    if ai_query.strip() and ai_excludes and not filtered.empty:
        searchable = (
            filtered["features_text"].fillna("").astype(str).str.lower()
            + " "
            + filtered["genres"].fillna("").astype(str).str.lower()
            + " "
            + filtered.get("tmdb_overview", pd.Series("", index=filtered.index)).fillna("").astype(str).str.lower()
        )
        exclude_mask = searchable.apply(lambda value: any(str(term).lower() in value for term in ai_excludes))
        filtered = filtered.loc[~exclude_mask].copy()

    query = st.session_state.get("title_query", "").strip()
    if query:
        filtered = filter_by_title_query(filtered, query)
    ai_excluded_genres = [
        genre for genre in ai_excludes
        if isinstance(genre, str) and genre in content_based.STRICT_GENRE_TERMS
    ]
    if ai_query.strip() and ai_excluded_genres and not filtered.empty:
        genre_text = filtered["genres"].fillna("").astype(str).str.lower()
        excluded_genre_mask = pd.Series(False, index=filtered.index)
        for genre_name in ai_excluded_genres:
            strict_terms = content_based.STRICT_GENRE_TERMS.get(genre_name, [])
            excluded_genre_mask = excluded_genre_mask | genre_text.apply(lambda value: any(term in value for term in strict_terms))
        filtered = filtered.loc[~excluded_genre_mask].copy()

    ai_genre_intents = [
        genre for genre in ai_context.get("genres", [])
        if isinstance(genre, str) and genre in content_based.GENRE_INTENTS
    ]
    if ai_query.strip() and ai_genre_intents and not filtered.empty:
        ai_genre_mask = pd.Series(False, index=filtered.index)
        genre_text = filtered["genres"].fillna("").astype(str).str.lower()
        for genre_name in ai_genre_intents:
            strict_terms = content_based.STRICT_GENRE_TERMS.get(genre_name, [])
            strict_mask = genre_text.apply(lambda value: any(term in value for term in strict_terms))
            if strict_mask.any():
                ai_genre_mask = ai_genre_mask | strict_mask
                continue
            genre_keywords = content_based.GENRE_INTENTS[genre_name]["genre_keywords"]
            ai_genre_mask = ai_genre_mask | genre_text.apply(lambda value: any(keyword in value for keyword in genre_keywords))
        filtered = filtered.loc[ai_genre_mask].copy()
    if genres:
        filtered = filtered[filtered["genres"].fillna("").apply(lambda value: any(genre in value for genre in genres))]
    if ai_query.strip() and ai_excluded_genres and not filtered.empty:
        genre_text = filtered["genres"].fillna("").astype(str).str.lower()
        excluded_genre_mask = pd.Series(False, index=filtered.index)
        for genre_name in ai_excluded_genres:
            strict_terms = content_based.STRICT_GENRE_TERMS.get(genre_name, [])
            excluded_genre_mask = excluded_genre_mask | genre_text.apply(lambda value: any(term in value for term in strict_terms))
        filtered = filtered.loc[~excluded_genre_mask].copy()
    filtered = filtered[filtered["year"].fillna(year_range[0]).between(year_range[0], year_range[1])]
    if not filtered.empty:
        imdb_score = pd.to_numeric(filtered["imdb_rating"], errors="coerce")
        tmdb_score = pd.to_numeric(filtered["tmdb_vote_average"], errors="coerce")
        imdb_score = imdb_score.where(imdb_score.gt(0))
        tmdb_score = tmdb_score.where(tmdb_score.gt(0))
        filtered = filtered.assign(_ms_rating_score=pd.concat([imdb_score, tmdb_score], axis=1).max(axis=1))

    ai_sort_bias = st.session_state.get("ai_sort_bias", "")
    if ai_query.strip() and ai_sort_bias == "latest" and not filtered.empty and filtered["year"].notna().any():
        max_year = int(filtered["year"].max())
        newest = filtered[filtered["year"] == max_year].copy()
        if len(newest) < 8:
            newest = filtered[filtered["year"] >= max_year - 1].copy()
        if ai_context.get("quality") and not newest.empty:
            rated_newest = newest.loc[newest["_ms_rating_score"].ge(6.5)].copy()
            if rated_newest.empty:
                rated_newest = filtered.loc[
                    filtered["year"].ge(max_year - 2) & filtered["_ms_rating_score"].ge(6.5)
                ].copy()
            if not rated_newest.empty:
                newest = rated_newest
        filtered = newest

    if similar_title_query and ai_sort_bias == "similar_latest":
        similarity_score = pd.to_numeric(filtered.get("semantic_similarity", 0), errors="coerce").fillna(0)
        year_score = pd.to_numeric(filtered["year"], errors="coerce")
        if year_score.notna().any():
            max_similar_year = int(year_score.max())
            recent_mask = year_score.ge(max_similar_year - 2)
            recent_filtered = filtered.loc[recent_mask].copy()
            if len(recent_filtered) >= 6:
                filtered = recent_filtered
                similarity_score = pd.to_numeric(filtered.get("semantic_similarity", 0), errors="coerce").fillna(0)
                year_score = pd.to_numeric(filtered["year"], errors="coerce")
        if year_score.notna().any() and year_score.max() != year_score.min():
            recency_score = (year_score - year_score.min()) / (year_score.max() - year_score.min())
        else:
            recency_score = pd.Series(0.0, index=filtered.index)
        rating_score = filtered.get("_ms_rating_score", pd.Series(0.0, index=filtered.index))
        rating_score = pd.to_numeric(rating_score, errors="coerce").fillna(0).clip(0, 10) / 10
        filtered = filtered.assign(_ms_similar_latest_score=similarity_score * 0.78 + recency_score.fillna(0) * 0.17 + rating_score * 0.05)
        filtered = filtered.sort_values(["_ms_similar_latest_score", "year", "semantic_similarity"], ascending=[False, False, False], na_position="last")
    elif similar_title_query and "semantic_similarity" in filtered.columns:
        filtered = filtered.sort_values("semantic_similarity", ascending=False, na_position="last")
    elif ai_query.strip() and ai_sort_bias == "latest" and ai_context.get("quality") and "_ms_rating_score" in filtered.columns:
        filtered = filtered.sort_values(["year", "_ms_rating_score", "tmdb_popularity"], ascending=[False, False, False], na_position="last")
    elif ai_query.strip() and ai_sort_bias == "latest":
        filtered = filtered.sort_values(["year", "imdb_rating", "tmdb_vote_average", "tmdb_popularity"], ascending=[False, False, False, False], na_position="last")
    elif ai_query.strip() and ai_sort_bias == "popular":
        filtered = filtered.sort_values(["tmdb_popularity", "tmdb_vote_average", "year"], ascending=[False, False, False], na_position="last")
    elif ai_query.strip() and ai_sort_bias == "top":
        filtered = filtered.sort_values(["imdb_rating", "tmdb_vote_average", "tmdb_popularity"], ascending=[False, False, False], na_position="last")
    elif ai_query.strip() and sort_by == t(lang, "За AI-релевантністю", "By AI relevance"):
        filtered = filtered.sort_values("semantic_similarity", ascending=False, na_position="last")
    elif sort_by == t(lang, "За популярністю", "By popularity"):
        filtered = filtered.sort_values("tmdb_popularity", ascending=False, na_position="last")
    elif sort_by == t(lang, "За IMDb рейтингом", "By IMDb"):
        filtered = filtered.sort_values("imdb_rating", ascending=False, na_position="last")
    else:
        filtered = filtered.sort_values("tmdb_vote_average", ascending=False, na_position="last")

    if filtered.empty:
        st.warning(t(lang, "Нічого не знайдено для таких фільтрів.", "No media found for these filters."))
        return

    page_size = 20
    total_items = len(filtered)
    total_pages = max((total_items - 1) // page_size + 1, 1)
    page_param = st.query_params.get("page")
    if page_param is not None:
        try:
            st.session_state["page"] = int(float(str(page_param)))
        except (TypeError, ValueError):
            st.session_state["page"] = 1
    page = min(max(st.session_state.get("page", 1), 1), total_pages)
    st.session_state["page"] = page

    start_idx = (page - 1) * page_size
    page_df = filtered.iloc[start_idx : start_idx + page_size]

    if ai_query.strip():
        st.markdown(
            f'<div class="ms-ai-pill">{html.escape(t(lang, "AI-режим: результати підібрані за змістом опису", "AI mode: results are ranked by your description"))}</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
<div class="ms-results-head">
  <h2>{html.escape(t(lang, "Результати", "Results"))}</h2>
  <div class="ms-results-count">{html.escape(t(lang, "Знайдено", "Found"))}: {total_items}</div>
</div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(5)
    for index, (_, row) in enumerate(page_df.iterrows()):
        with cols[index % 5]:
            render_card(row, lang)

    render_pagination(page, total_pages)

    st.markdown(
        """
<div class="ms-footer">
  <div class="ms-footer-content">
    <span class="ms-footer-brand">© 2026 AI Movie Recommender</span>
    <span class="ms-footer-text">Відкривай нові фільми швидко, з інтелектуальними фільтрами та персоналізованими рекомендаціями.</span>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
