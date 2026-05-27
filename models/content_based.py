from lib.imports import *

from utils.preprocessing import load_movies

QUERY_SYNONYMS = {
    "супергер": "superhero superheroes marvel dc comic comics superpower action adventure",
    "марвел": "marvel superhero avengers iron man captain america comic",
    "dc": "dc superhero superheroes comic vigilante dark knight batman",
    "фентез": "fantasy magic magical wizard mythical dragon kingdom quest adventure",
    "фантаст": "science fiction sci-fi futuristic space alien technology",
    "космос": "space sci-fi science fiction galaxy astronaut interstellar universe",
    "магі": "magic magical fantasy wizard sorcery mythical",
    "жах": "horror scary creepy supernatural ghost haunted monster thriller",
    "хорор": "horror scary creepy supernatural ghost haunted monster thriller",
    "комед": "comedy funny humor family lighthearted",
    "сміш": "comedy funny humor lighthearted",
    "романт": "romance romantic love relationship couple",
    "кохан": "romance romantic love relationship couple",
    "бойов": "action combat fight superhero adventure thriller",
    "екшн": "action combat fight mission explosion adventure",
    "пригод": "adventure journey quest exploration travel",
    "драма": "drama emotional relationship character life",
    "мульт": "animation animated cartoon anime family pixar disney",
    "анім": "animation animated anime cartoon family",
    "детектив": "detective mystery investigation crime thriller",
    "кримін": "crime detective mafia gangster thriller",
    "сімейн": "family friendly kids children heartwarming",
    "документ": "documentary real story factual informative",
    "біограф": "biography biographical real person true story",
    "істор": "history historical period war past",
    "музич": "music musical song concert musician",
    "мюзикл": "musical song dance music stage",
    "спорт": "sport sports athlete competition football boxing",
    "вестерн": "western cowboy frontier desert sheriff",
    "трилер": "thriller suspense tense mystery crime",
    "темний": "dark thriller psychological crime mystery",
    "розумн": "smart intelligent psychological twist thought-provoking",
}

GENRE_INTENTS = {
    "action": {
        "include": ["бойовик", "бойовики", "екшн", "action", "бойове", "бойов"],
        "genre_keywords": ["action", "thriller", "crime"],
        "content_keywords": ["fight", "combat", "war", "mission", "explosion", "hero", "assassin", "weapon", "gun"],
    },
    "fantasy": {
        "include": ["фентезі", "фентези", "fantasy", "магія", "магічне", "чари"],
        "genre_keywords": ["fantasy", "adventure"],
        "content_keywords": ["magic", "wizard", "dragon", "kingdom", "mythical"],
    },
    "science fiction": {
        "include": ["фантастика", "sci-fi", "science fiction", "космос", "майбутнє"],
        "genre_keywords": ["science fiction", "sci-fi"],
        "content_keywords": ["space", "future", "alien", "robot", "galaxy", "technology"],
    },
    "horror": {
        "include": ["жахи", "жах", "хорор", "хоррор", "страшне", "страшний", "horror"],
        "genre_keywords": ["horror", "thriller"],
        "content_keywords": ["ghost", "haunted", "monster", "fear", "supernatural"],
    },
    "comedy": {
        "include": ["комедія", "смішне", "веселе", "comedy"],
        "genre_keywords": ["comedy"],
        "content_keywords": ["funny", "humor", "family", "lighthearted"],
    },
    "romance": {
        "include": ["романтика", "кохання", "романтичне", "romance"],
        "genre_keywords": ["romance", "drama"],
        "content_keywords": ["love", "relationship", "couple"],
    },
    "animation": {
        "include": ["мультфільм", "мультфільми", "аніме", "анімація", "cartoon", "animated"],
        "genre_keywords": ["animation", "anime", "family"],
        "content_keywords": ["animated", "cartoon", "family", "kids"],
    },
    "crime": {
        "include": ["кримінал", "детектив", "mafia", "crime"],
        "genre_keywords": ["crime", "thriller", "mystery"],
        "content_keywords": ["investigation", "detective", "mafia", "gangster", "murder"],
    },
    "adventure": {
        "include": ["пригоди", "пригодницький", "пригод", "adventure"],
        "genre_keywords": ["adventure"],
        "content_keywords": ["journey", "quest", "exploration", "travel", "expedition"],
    },
    "drama": {
        "include": ["драма", "драму", "драматичне", "drama"],
        "genre_keywords": ["drama"],
        "content_keywords": ["emotional", "life", "relationship", "character", "family"],
    },
    "thriller": {
        "include": ["трилер", "трилери", "напружене", "thriller"],
        "genre_keywords": ["thriller"],
        "content_keywords": ["suspense", "tense", "danger", "mystery", "crime"],
    },
    "family": {
        "include": ["сімейний", "сімейне", "для сім'ї", "family"],
        "genre_keywords": ["family"],
        "content_keywords": ["kids", "children", "friendly", "heartwarming", "animated"],
    },
    "documentary": {
        "include": ["документальний", "документалка", "документальне", "documentary"],
        "genre_keywords": ["documentary"],
        "content_keywords": ["real", "factual", "true story", "interview", "history"],
    },
    "biography": {
        "include": ["біографія", "біографічний", "про життя", "biography", "biographical"],
        "genre_keywords": ["biography"],
        "content_keywords": ["true story", "life", "person", "career", "historical"],
    },
    "history": {
        "include": ["історичний", "історія", "історичне", "history", "historical"],
        "genre_keywords": ["history"],
        "content_keywords": ["historical", "period", "war", "past", "king"],
    },
    "music": {
        "include": ["музика", "музичний", "про музику", "music"],
        "genre_keywords": ["music"],
        "content_keywords": ["song", "concert", "musician", "band", "singer"],
    },
    "musical": {
        "include": ["мюзикл", "мюзикли", "musical"],
        "genre_keywords": ["musical", "music"],
        "content_keywords": ["song", "dance", "stage", "music", "performance"],
    },
    "sport": {
        "include": ["спорт", "спортивний", "про спорт", "sport", "sports"],
        "genre_keywords": ["sport"],
        "content_keywords": ["athlete", "competition", "football", "boxing", "team"],
    },
    "western": {
        "include": ["вестерн", "western", "ковбой"],
        "genre_keywords": ["western"],
        "content_keywords": ["cowboy", "frontier", "sheriff", "desert", "outlaw"],
    },
}

STRICT_GENRE_TERMS = {
    "action": ["action"],
    "fantasy": ["fantasy"],
    "science fiction": ["science fiction", "sci-fi"],
    "horror": ["horror"],
    "comedy": ["comedy"],
    "romance": ["romance"],
    "animation": ["animation", "anime"],
    "crime": ["crime"],
    "adventure": ["adventure"],
    "drama": ["drama"],
    "thriller": ["thriller"],
    "family": ["family"],
    "documentary": ["documentary"],
    "biography": ["biography"],
    "history": ["history"],
    "music": ["music"],
    "musical": ["musical"],
    "sport": ["sport"],
    "western": ["western"],
}

NEGATIVE_HINTS = {
    "не спорт": ["sport", "sports", "football", "soccer", "basketball", "boxing", "wrestling", "athlete"],
    "без спорту": ["sport", "sports", "football", "soccer", "basketball", "boxing", "wrestling", "athlete"],
    "не романтика": ["romance", "love", "relationship", "couple"],
    "без романтики": ["romance", "love", "relationship", "couple"],
    "не комедія": ["comedy", "funny", "humor", "lighthearted"],
    "без комедії": ["comedy", "funny", "humor", "lighthearted"],
    "без жорстокості": ["violence", "gore", "brutal", "bloody", "war"],
    "без насильства": ["violence", "gore", "brutal", "bloody", "war"],
    "без магії": ["magic", "wizard", "sorcery", "spell", "mythical", "dragon", "kingdom", "fantasy"],
    "без чарів": ["magic", "wizard", "sorcery", "spell", "mythical", "dragon", "fantasy"],
    "без чаклунів": ["magic", "wizard", "sorcery", "spell", "fantasy"],
    "без драконів": ["dragon", "mythical", "fantasy"],
    "не магія": ["magic", "wizard", "sorcery", "spell", "fantasy"],
    "without sport": ["sport", "sports", "football", "soccer", "basketball", "boxing", "wrestling", "athlete"],
    "no sport": ["sport", "sports", "football", "soccer", "basketball", "boxing", "wrestling", "athlete"],
    "without romance": ["romance", "love", "relationship", "couple"],
    "no romance": ["romance", "love", "relationship", "couple"],
    "without comedy": ["comedy", "funny", "humor", "lighthearted"],
    "no comedy": ["comedy", "funny", "humor", "lighthearted"],
    "without magic": ["magic", "wizard", "sorcery", "spell", "mythical", "dragon", "kingdom", "fantasy"],
    "no magic": ["magic", "wizard", "sorcery", "spell", "mythical", "dragon", "kingdom", "fantasy"],
}

QUERY_FILLER_WORDS = {
    "покажи",
    "дай",
    "дайте",
    "мені",
    "якісь",
    "якийсь",
    "щось",
    "хочу",
    "хочеться",
    "будь",
    "ласка",
    "будь-ласка",
    "фільми",
    "фільм",
    "кіно",
    "подивитись",
    "подивитися",
    "дивитись",
    "для",
    "про",
    "with",
    "show",
    "give",
    "some",
    "movies",
}

TOPIC_INTENTS = {
    "space": {
        "include": ["космос", "космічний", "space", "galaxy", "astronaut"],
        "keywords": ["space", "galaxy", "astronaut", "planet", "universe", "interstellar", "rocket"],
    },
    "war": {
        "include": ["війна", "воєнний", "war", "battle"],
        "keywords": ["war", "battle", "soldier", "army", "military", "invasion"],
    },
    "magic": {
        "include": ["магія", "чари", "чаклун", "wizard", "magic"],
        "keywords": ["magic", "wizard", "sorcery", "spell", "mythical", "dragon"],
    },
    "superhero": {
        "include": ["марвел", "dc", "супергерої", "superhero"],
        "keywords": ["superhero", "marvel", "dc", "comic", "avengers", "batman", "spider"],
    },
    "crime": {
        "include": ["мафія", "кримінал", "гангстер", "crime"],
        "keywords": ["crime", "gangster", "mafia", "detective", "murder", "heist"],
    },
}

MOOD_INTENTS = {
    "dark": {
        "include": ["темний", "похмурий", "dark", "grim"],
        "keywords": ["dark", "grim", "psychological", "crime", "mystery"],
    },
    "epic": {
        "include": ["епічний", "масштабний", "epic", "grand"],
        "keywords": ["epic", "legendary", "kingdom", "war", "grand", "saga"],
    },
    "family": {
        "include": ["сімейний", "для дітей", "family", "kids"],
        "keywords": ["family", "kids", "children", "heartwarming", "friendly"],
    },
    "smart": {
        "include": ["розумний", "розумне", "інтелектуальний", "smart", "mind-bending"],
        "keywords": ["smart", "mind", "intelligent", "psychological", "twist", "thought-provoking"],
    },
    "light": {
        "include": ["легке", "легкий", "easy", "lighthearted"],
        "keywords": ["lighthearted", "funny", "family", "feel-good"],
    },
}

STRICT_ONLY_PATTERNS = {
    "action": ["лише бойовик", "тільки бойовик", "only action", "just action"],
    "fantasy": ["лише фентезі", "тільки фентезі", "only fantasy"],
    "science fiction": ["лише фантастика", "тільки фантастика", "only sci-fi", "only science fiction"],
    "horror": ["лише жахи", "тільки жахи", "only horror"],
    "comedy": ["лише комедія", "тільки комедія", "only comedy"],
    "animation": ["лише мультфільм", "тільки мультфільм", "лише анімація", "тільки анімація", "only animation"],
    "crime": ["лише кримінал", "тільки кримінал", "only crime"],
}

EXCLUDED_GENRE_PATTERNS = {
    "action": [
        "без бойовика",
        "без бойовиків",
        "без екшну",
        "не бойовик",
        "не бойовики",
        "не екшн",
        "without action",
        "no action",
    ],
    "fantasy": [
        "без фентезі",
        "не фентезі",
        "без магії",
        "без чарів",
        "без чаклунів",
        "без драконів",
        "не магія",
        "without fantasy",
        "no fantasy",
        "without magic",
        "no magic",
    ],
    "animation": ["без мультиків", "без мультфільмів", "без анімації", "не мультфільм", "without animation", "no animation"],
    "comedy": ["без комедії", "не комедія", "without comedy", "no comedy"],
    "romance": ["без романтики", "не романтика", "without romance", "no romance"],
    "science fiction": ["без фантастики", "не фантастика", "without sci-fi", "no sci-fi"],
    "horror": ["без жахів", "не жахи", "without horror", "no horror"],
    "family": ["без сімейного", "не сімейне", "without family"],
    "adventure": ["без пригод", "не пригоди", "without adventure", "no adventure"],
    "drama": ["без драми", "не драма", "without drama", "no drama"],
    "thriller": ["без трилера", "без трилерів", "не трилер", "without thriller", "no thriller"],
    "documentary": ["без документального", "не документальний", "without documentary", "no documentary"],
    "biography": ["без біографії", "не біографія", "without biography", "no biography"],
    "history": ["без історичного", "не історичний", "without history", "no history"],
    "music": ["без музики", "не музичний", "without music", "no music"],
    "musical": ["без мюзиклу", "не мюзикл", "without musical", "no musical"],
    "sport": ["без спорту", "не спорт", "without sport", "no sport"],
    "western": ["без вестерну", "не вестерн", "without western", "no western"],
}

HARD_NEGATIVE_PATTERNS = {
    "magic": {
        "patterns": ["без магії", "без чарів", "без чаклунів", "без драконів", "не магія", "without magic", "no magic"],
        "terms": [
            "fantasy",
            "magic",
            "wizard",
            "sorcery",
            "spell",
            "mythical",
            "dragon",
            "hobbit",
            "lord of the rings",
            "middle-earth",
            "middle earth",
            "rings",
            "elves",
            "elf",
            "orc",
            "dwarf",
        ],
    }
}


def normalize_query_text(text: str) -> str:
    text = text.strip().lower().replace("’", "'")
    text = re.sub(r"[^\w\s'-]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def strip_filler_words(text: str) -> str:
    tokens = [token for token in normalize_query_text(text).split() if token not in QUERY_FILLER_WORDS]
    return " ".join(tokens)


def get_negated_tokens(text: str) -> set[str]:
    tokens = normalize_query_text(text).split()
    negated: set[str] = set()
    negation_words = {"без", "не", "without", "no"}

    for index, token in enumerate(tokens[:-1]):
        if token in negation_words:
            negated.add(tokens[index + 1])
            if index + 2 < len(tokens):
                negated.add(f"{tokens[index + 1]} {tokens[index + 2]}")
    return negated


def expand_query_text(description: str) -> str:
    text = normalize_query_text(description)
    core_text = strip_filler_words(description)
    negated_tokens = get_negated_tokens(description)
    if not text:
        return ""

    expanded_parts = [text]
    if core_text and core_text != text:
        expanded_parts.append(core_text)

    tokens = core_text.split() if core_text else text.split()
    for token in tokens:
        if token in negated_tokens:
            continue
        for stem, extra in QUERY_SYNONYMS.items():
            if stem in token:
                expanded_parts.append(extra)

    return " ".join(dict.fromkeys(part for part in expanded_parts if part))


def extract_query_intents(description: str) -> tuple[list[str], list[str], list[str], list[str], list[str], list[str]]:
    text = normalize_query_text(description)
    negated_tokens = get_negated_tokens(description)
    matched_intents: list[str] = []
    negative_terms: list[str] = []
    matched_topics: list[str] = []
    matched_moods: list[str] = []
    strict_only_genres: list[str] = []
    excluded_genres: list[str] = []

    for genre_name, patterns in STRICT_ONLY_PATTERNS.items():
        if any(pattern in text for pattern in patterns):
            strict_only_genres.append(genre_name)

    for genre_name, patterns in EXCLUDED_GENRE_PATTERNS.items():
        if any(pattern in text for pattern in patterns):
            excluded_genres.append(genre_name)

    for genre_name, config in GENRE_INTENTS.items():
        include_terms = [term for term in config["include"] if term not in negated_tokens]
        if any(term in text for term in include_terms) and genre_name not in excluded_genres:
            matched_intents.append(genre_name)

    for topic_name, config in TOPIC_INTENTS.items():
        include_terms = [term for term in config["include"] if term not in negated_tokens]
        if any(term in text for term in include_terms):
            matched_topics.append(topic_name)

    for mood_name, config in MOOD_INTENTS.items():
        include_terms = [term for term in config["include"] if term not in negated_tokens]
        if any(term in text for term in include_terms):
            matched_moods.append(mood_name)

    for phrase, terms in NEGATIVE_HINTS.items():
        if phrase in text:
            negative_terms.extend(terms)

    return matched_intents, negative_terms, matched_topics, matched_moods, strict_only_genres, excluded_genres


def get_hard_negative_terms(description: str) -> list[str]:
    text = normalize_query_text(description)
    terms: list[str] = []
    for config in HARD_NEGATIVE_PATTERNS.values():
        if any(pattern in text for pattern in config["patterns"]):
            terms.extend(config["terms"])
    return list(dict.fromkeys(terms))


def _normalize_series(values: pd.Series) -> pd.Series:
    series = pd.to_numeric(values, errors="coerce").fillna(0.0).astype(float)
    max_val = series.max()
    min_val = series.min()
    if pd.isna(max_val) or pd.isna(min_val) or max_val == min_val:
        return pd.Series(np.zeros(len(series)), index=series.index, dtype=float)
    return (series - min_val) / (max_val - min_val)


def _has_strict_genre(genres_value: object, genre_name: str) -> bool:
    text = str(genres_value).lower() if pd.notna(genres_value) else ""
    return any(term in text for term in STRICT_GENRE_TERMS.get(genre_name, []))


def build_content_index(movies: pd.DataFrame) -> tuple[TfidfVectorizer, object, Optional[np.ndarray]]:
    max_features = 5000 if len(movies) <= 12000 else 2500
    tfidf = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=2, max_features=max_features)
    tfidf_matrix = tfidf.fit_transform(movies["features_text"].fillna(""))
    return tfidf, tfidf_matrix, None


def build_similarity(movies: pd.DataFrame) -> tuple[TfidfVectorizer, Optional[np.ndarray]]:
    tfidf, _, sim = build_content_index(movies)
    return tfidf, sim


def find_title_index(movies: pd.DataFrame, title: str) -> Optional[int]:
    title_norm = title.strip().lower()
    hits = movies.index[movies["title"].str.lower() == title_norm].tolist()
    if hits:
        return hits[0]

    hits = movies.index[movies["title"].str.lower().str.contains(re.escape(title_norm), na=False)].tolist()
    return hits[0] if hits else None


def get_content_recommendations(
    title: str,
    top_n: int = 10,
    movies: Optional[pd.DataFrame] = None,
    tfidf_matrix: Optional[object] = None,
    cosine_sim: Optional[np.ndarray] = None,
) -> pd.DataFrame:
    if movies is None:
        movies = load_movies()
    if cosine_sim is None and tfidf_matrix is None:
        _, tfidf_matrix, cosine_sim = build_content_index(movies)

    idx = find_title_index(movies, title)
    if idx is None:
        return movies.head(0)

    if cosine_sim is not None:
        scores = cosine_sim[idx]
    else:
        query_matrix = tfidf_matrix[idx : idx + 1]
        scores = cosine_similarity(query_matrix, tfidf_matrix).flatten()
    sim_scores = list(enumerate(scores))
    sim_scores = sorted(sim_scores, key=lambda item: item[1], reverse=True)
    sim_scores = [item for item in sim_scores if item[0] != idx][:top_n]

    rec_idx = [index for index, _ in sim_scores]
    out = movies.iloc[rec_idx].copy()
    out["similarity"] = [score for _, score in sim_scores]
    return out


def search_by_description(
    description: str,
    movies: Optional[pd.DataFrame] = None,
    tfidf: Optional[TfidfVectorizer] = None,
    tfidf_matrix: Optional[object] = None,
    top_n: int = 50,
) -> pd.DataFrame:
    description = description.strip()
    if not description:
        return load_movies().head(0) if movies is None else movies.head(0)

    if movies is None:
        movies = load_movies()
    if tfidf is None or tfidf_matrix is None:
        tfidf, tfidf_matrix, _ = build_content_index(movies)

    expanded_description = expand_query_text(description)
    query_vec = tfidf.transform([expanded_description])
    scores = cosine_similarity(query_vec, tfidf_matrix).flatten()

    out = movies.copy()
    out["semantic_similarity"] = scores
    out["semantic_score"] = out["semantic_similarity"].astype(float)
    out["genre_match_score"] = 0.0

    matched_intents, negative_terms, matched_topics, matched_moods, strict_only_genres, excluded_genres = extract_query_intents(description)
    hard_negative_terms = get_hard_negative_terms(description)
    searchable_text = (
        out["features_text"].fillna("").astype(str).str.lower()
        + " "
        + out["genres"].fillna("").astype(str).str.lower()
        + " "
        + out.get("tmdb_overview", pd.Series("", index=out.index)).fillna("").astype(str).str.lower()
    )

    if hard_negative_terms:
        hard_negative_mask = searchable_text.apply(lambda value: any(term in value for term in hard_negative_terms))
        out = out[~hard_negative_mask].copy()
        searchable_text = searchable_text.loc[out.index]
        if out.empty:
            return out

    requested_genre_mask = pd.Series(False, index=out.index)

    if matched_intents:
        for genre_name in matched_intents:
            config = GENRE_INTENTS[genre_name]
            genre_mask = out["genres"].fillna("").str.lower().apply(
                lambda value: any(keyword in value for keyword in config["genre_keywords"])
            )
            requested_genre_mask = requested_genre_mask | genre_mask
            keyword_mask = searchable_text.apply(
                lambda value: any(keyword in value for keyword in config["content_keywords"])
            )
            out.loc[genre_mask, "genre_match_score"] += 1.0
            out.loc[keyword_mask, "genre_match_score"] += 0.35
            out.loc[genre_mask, "semantic_score"] += 0.45
            out.loc[keyword_mask, "semantic_score"] += 0.15

    if strict_only_genres:
        strict_mask = pd.Series(False, index=out.index)
        for genre_name in strict_only_genres:
            strict_mask = strict_mask | out["genres"].apply(lambda value: _has_strict_genre(value, genre_name))
        out = out[strict_mask].copy()
        searchable_text = searchable_text.loc[out.index]
        if out.empty:
            return out

    topic_match_score = pd.Series(np.zeros(len(out)), index=out.index, dtype=float)
    for topic_name in matched_topics:
        config = TOPIC_INTENTS[topic_name]
        topic_mask = searchable_text.loc[out.index].apply(lambda value: any(keyword in value for keyword in config["keywords"]))
        topic_match_score.loc[topic_mask] += 1.0
        out.loc[topic_mask, "semantic_score"] += 0.22

    mood_match_score = pd.Series(np.zeros(len(out)), index=out.index, dtype=float)
    for mood_name in matched_moods:
        config = MOOD_INTENTS[mood_name]
        mood_mask = searchable_text.loc[out.index].apply(lambda value: any(keyword in value for keyword in config["keywords"]))
        mood_match_score.loc[mood_mask] += 1.0
        out.loc[mood_mask, "semantic_score"] += 0.14

    if negative_terms:
        negative_mask = searchable_text.loc[out.index].apply(lambda value: any(term in value for term in negative_terms))
        out.loc[negative_mask, "semantic_score"] -= 0.35

    if excluded_genres:
        excluded_mask = pd.Series(False, index=out.index)
        for genre_name in excluded_genres:
            excluded_mask = excluded_mask | out["genres"].apply(lambda value: _has_strict_genre(value, genre_name))
        out = out[~excluded_mask].copy()
        if out.empty:
            return out
        topic_match_score = topic_match_score.loc[out.index]
        mood_match_score = mood_match_score.loc[out.index]

    if matched_intents:
        direct_genre_mask = requested_genre_mask.loc[out.index]
        if direct_genre_mask.any():
            out = out[direct_genre_mask].copy()
        else:
            out = out[out["genre_match_score"] > 0].copy()
        if out.empty:
            return out
        topic_match_score = topic_match_score.loc[out.index]
        mood_match_score = mood_match_score.loc[out.index]
    elif matched_topics:
        topical_mask = topic_match_score.loc[out.index] > 0
        if topical_mask.any():
            out = out[topical_mask].copy()
            topic_match_score = topic_match_score.loc[out.index]
            mood_match_score = mood_match_score.loc[out.index]

    imdb_norm = _normalize_series(out.get("imdb_rating", pd.Series(0, index=out.index)))
    tmdb_norm = _normalize_series(out.get("tmdb_vote_average", pd.Series(0, index=out.index)))
    popularity_norm = _normalize_series(out.get("tmdb_popularity", pd.Series(0, index=out.index)))

    out["quality_score"] = 0.55 * imdb_norm + 0.30 * tmdb_norm + 0.15 * popularity_norm
    out["intent_boost"] = out["genre_match_score"].fillna(0.0) * 0.35
    out["topic_boost"] = topic_match_score.loc[out.index].fillna(0.0) * 0.18
    out["mood_boost"] = mood_match_score.loc[out.index].fillna(0.0) * 0.10
    out["final_rank_score"] = (
        0.50 * out["semantic_score"].fillna(0.0)
        + 0.25 * out["quality_score"].fillna(0.0)
        + 0.20 * out["intent_boost"].fillna(0.0)
        + 0.10 * out["topic_boost"].fillna(0.0)
        + 0.05 * out["mood_boost"].fillna(0.0)
    )

    low_quality_mask = (
        out.get("imdb_rating", pd.Series(np.nan, index=out.index)).fillna(0) < 5.5
    ) & (
        out.get("tmdb_vote_average", pd.Series(np.nan, index=out.index)).fillna(0) < 5.5
    )
    out.loc[low_quality_mask, "final_rank_score"] -= 0.25

    ranked_idx = np.argsort(out["final_rank_score"].to_numpy())[::-1][:top_n]
    out = out.iloc[ranked_idx].copy()
    out["semantic_similarity"] = out["final_rank_score"]
    return out[out["semantic_similarity"] > 0].reset_index(drop=True)
