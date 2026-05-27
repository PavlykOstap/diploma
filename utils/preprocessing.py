from lib.imports import *

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
TMDB_IMG_BASE_W500 = "https://image.tmdb.org/t/p/w500"
TMDB_IMG_BASE_ORIGINAL = "https://image.tmdb.org/t/p/original"
MOVIE_CATALOG_LIMIT = 12000
PROTECTED_CATALOG_YEARS = {2024, 2025}
MOVIE_CATALOG_CACHE_VERSION = "fresh-rated-v1"

SEARCH_SYNONYMS = {
    "fantasy": "fantasy magic magical wizard medieval mythical dragon kingdom quest",
    "sci-fi": "science fiction sci-fi futuristic future space alien robot technology cyberpunk",
    "science fiction": "science fiction sci-fi futuristic future space alien robot technology cyberpunk",
    "superhero": "superhero superheroes marvel dc comic comics vigilante superpower action adventure",
    "horror": "horror scary creepy supernatural haunted ghost monster fear thriller",
    "romance": "romance romantic love relationship couple drama",
    "comedy": "comedy funny humor humour lighthearted family",
    "animation": "animation animated cartoon pixar disney anime family",
    "anime": "anime animation animated cartoon fantasy action",
    "thriller": "thriller suspense tense mystery crime investigation psychological",
    "drama": "drama emotional character relationship life",
    "adventure": "adventure journey exploration quest travel action",
}

GENRE_ALIASES = {
    "fantasy": "фентезі фентезі магія магічний чарівний міфічний казковий dragons magic",
    "science fiction": "фантастика наукова фантастика sci fi sci-fi космос майбутнє роботи aliens",
    "sci-fi": "фантастика наукова фантастика космос sci fi space future aliens robots",
    "superhero": "супергерой супергерої супергеройський марвел dc комікси heroes comic",
    "action": "бойовик екшн битви бійки fight combat",
    "adventure": "пригоди пригодницький квест journey exploration",
    "comedy": "комедія смішний веселий гумор comedy funny",
    "romance": "романтика романтичний кохання love relationship",
    "drama": "драма драматичний емоційний emotional",
    "thriller": "трилер напружений suspense mystery crime",
    "horror": "жахи страшний моторошний horror scary ghost monster",
    "animation": "мультфільм мультфільми анімація аніме cartoon animated family",
    "anime": "аніме animation animated cartoon",
    "family": "сімейний для сім'ї family kids children",
    "mystery": "детектив загадка розслідування mystery investigation",
    "crime": "кримінал злочин crime mafia gangster",
}


def _safe_read_csv(path: str, **kwargs) -> pd.DataFrame:
    try:
        return pd.read_csv(path, encoding="utf-8", **kwargs)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="latin-1", **kwargs)


def _normalize_text(s: object) -> str:
    if s is None or (isinstance(s, float) and np.isnan(s)):
        return ""
    s = str(s).replace("\u00a0", " ")
    return re.sub(r"\s+", " ", s).strip()


def _expand_search_text(text: object) -> str:
    normalized = _normalize_text(text).lower()
    if not normalized:
        return ""

    expanded_parts = [normalized]
    for key, extra in SEARCH_SYNONYMS.items():
        if key in normalized:
            expanded_parts.append(extra)
    return " ".join(expanded_parts)


def _genre_alias_text(genres: object) -> str:
    normalized = _normalize_text(genres).lower()
    if not normalized:
        return ""

    extras: List[str] = []
    for key, alias in GENRE_ALIASES.items():
        if key in normalized:
            extras.append(alias)
    return " ".join(extras)


def load_movies() -> pd.DataFrame:
    """
    Load and unify IMDb datasets into a single movies table.

    Stable output columns:
    - title, year, certificate, genres, director, cast, imdb_rating, metascore, duration_min, poster_src
    - TMDB fields when available
    - features_text for TF-IDF search
    """
    cache_path = os.path.join(DATA_DIR, f"movie_catalog_{MOVIE_CATALOG_LIMIT}_{MOVIE_CATALOG_CACHE_VERSION}.csv")
    if os.path.exists(cache_path):
        return _safe_read_csv(cache_path)

    paths = [
        os.path.join(DATA_DIR, "IMDb_Dataset.csv"),
        os.path.join(DATA_DIR, "IMDb_Dataset_2.csv"),
        os.path.join(DATA_DIR, "IMDb_Dataset_3.csv"),
    ]

    frames: List[pd.DataFrame] = []
    for path in paths:
        if os.path.exists(path):
            frames.append(_safe_read_csv(path))

    if not frames:
        raise FileNotFoundError("Не знайдено IMDb CSV у папці `data/`. Очікуються файли IMDb_Dataset*.csv")

    df = pd.concat(frames, ignore_index=True)

    col_map = {
        "Title": "title",
        "Year": "year",
        "Certificates": "certificate",
        "Genre": "genre_1",
        "Second_Genre": "genre_2",
        "Third_Genre": "genre_3",
        "Director": "director",
        "Star Cast": "cast",
        "IMDb Rating": "imdb_rating",
        "MetaScore": "metascore",
        "Duration (minutes)": "duration_min",
        "Poster-src": "poster_src",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    for column in ["title", "director", "cast", "certificate", "poster_src"]:
        if column not in df.columns:
            df[column] = ""
        df[column] = df[column].apply(_normalize_text)

    for column in ["genre_1", "genre_2", "genre_3"]:
        if column not in df.columns:
            df[column] = ""
        df[column] = df[column].apply(_normalize_text)

    for column in ["year", "imdb_rating", "metascore", "duration_min"]:
        if column not in df.columns:
            df[column] = np.nan
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["genres"] = (
        df[["genre_1", "genre_2", "genre_3"]]
        .fillna("")
        .agg(lambda row: ", ".join([value for value in row.tolist() if value]), axis=1)
    )

    df["_has_rating"] = df["imdb_rating"].notna().astype(int)
    df = df.sort_values(by=["_has_rating", "imdb_rating"], ascending=False)
    df = df.drop_duplicates(subset=["title", "year"], keep="first").drop(columns=["_has_rating"])

    tmdb_path = os.path.join(DATA_DIR, "TMDB_movie_dataset_v11.csv")
    if os.path.exists(tmdb_path):
        tmdb_cols = [
            "title",
            "genres",
            "vote_average",
            "vote_count",
            "overview",
            "poster_path",
            "backdrop_path",
            "popularity",
            "release_date",
        ]
        tmdb = _safe_read_csv(tmdb_path, usecols=lambda col: col in tmdb_cols)
        tmdb = tmdb.rename(
            columns={
                "title": "tmdb_title",
                "genres": "tmdb_genres",
                "vote_average": "tmdb_vote_average",
                "vote_count": "tmdb_vote_count",
                "overview": "tmdb_overview",
                "poster_path": "tmdb_poster_path",
                "backdrop_path": "tmdb_backdrop_path",
                "popularity": "tmdb_popularity",
                "release_date": "tmdb_release_date",
            }
        )

        tmdb["tmdb_title"] = tmdb["tmdb_title"].apply(_normalize_text)
        tmdb["tmdb_genres"] = tmdb.get("tmdb_genres", "").apply(_normalize_text)
        for column in ["tmdb_vote_average", "tmdb_vote_count", "tmdb_popularity"]:
            tmdb[column] = pd.to_numeric(tmdb[column], errors="coerce")
        tmdb["tmdb_year"] = pd.to_datetime(tmdb["tmdb_release_date"], errors="coerce").dt.year
        tmdb["tmdb_poster_url"] = tmdb["tmdb_poster_path"].apply(
            lambda value: f"{TMDB_IMG_BASE_W500}{value}" if isinstance(value, str) and value.strip() else ""
        )
        tmdb["tmdb_backdrop_url"] = tmdb["tmdb_backdrop_path"].apply(
            lambda value: f"{TMDB_IMG_BASE_ORIGINAL}{value}" if isinstance(value, str) and value.strip() else ""
        )
        tmdb["_has_poster"] = tmdb["tmdb_poster_url"].ne("").astype(int)

        left = df.drop(
            columns=[
                "tmdb_vote_average",
                "tmdb_vote_count",
                "tmdb_popularity",
                "tmdb_overview",
                "tmdb_poster_url",
                "tmdb_backdrop_url",
            ],
            errors="ignore",
        ).copy()
        left["_t"] = left["title"].str.lower()
        left["_y"] = left["year"]

        right = tmdb[
            [
                "tmdb_title",
                "tmdb_year",
                "tmdb_vote_average",
                "tmdb_vote_count",
                "tmdb_popularity",
                "tmdb_overview",
                "tmdb_poster_url",
                "tmdb_backdrop_url",
                "_has_poster",
            ]
        ].copy()
        right["_t"] = right["tmdb_title"].str.lower()
        right["_y"] = right["tmdb_year"]
        right = right.sort_values(["_has_poster", "tmdb_vote_count", "tmdb_popularity"], ascending=False, na_position="last")
        right = right.drop_duplicates(subset=["_t", "_y"], keep="first")

        df = left.merge(right.drop(columns=["tmdb_title", "tmdb_year", "_has_poster"]), on=["_t", "_y"], how="left")
        df = df.drop(columns=["_t", "_y"])

        tmdb_extra = tmdb.copy()
        tmdb_extra["_t"] = tmdb_extra["tmdb_title"].str.lower()
        tmdb_extra["_y"] = tmdb_extra["tmdb_year"]
        tmdb_extra = tmdb_extra[
            tmdb_extra["tmdb_title"].ne("")
            & tmdb_extra["tmdb_year"].notna()
            & tmdb_extra["tmdb_poster_url"].ne("")
        ].copy()
        tmdb_extra = tmdb_extra.sort_values(["_has_poster", "tmdb_vote_count", "tmdb_popularity"], ascending=False, na_position="last")
        tmdb_extra = tmdb_extra.drop_duplicates(subset=["_t", "_y"], keep="first")
        existing_keys = set(zip(left["_t"], left["_y"]))
        tmdb_extra = tmdb_extra[~tmdb_extra[["_t", "_y"]].apply(tuple, axis=1).isin(existing_keys)]

        needed = max(0, MOVIE_CATALOG_LIMIT - int(df["tmdb_poster_url"].fillna("").astype(str).str.strip().ne("").sum()))
        protected_extra = tmdb_extra[
            tmdb_extra["tmdb_year"].isin(PROTECTED_CATALOG_YEARS)
            & pd.to_numeric(tmdb_extra["tmdb_vote_average"], errors="coerce").gt(0)
        ].copy()
        if needed or not protected_extra.empty:
            other_extra = tmdb_extra[~tmdb_extra.index.isin(protected_extra.index)].copy()
            other_needed = max(0, needed - len(protected_extra))
            tmdb_extra = pd.concat([protected_extra, other_extra.head(other_needed)], ignore_index=True)
            extra_df = pd.DataFrame(
                {
                    "title": tmdb_extra["tmdb_title"],
                    "year": tmdb_extra["tmdb_year"],
                    "certificate": "",
                    "genres": tmdb_extra["tmdb_genres"],
                    "director": "",
                    "cast": "",
                    "imdb_rating": np.nan,
                    "metascore": np.nan,
                    "duration_min": np.nan,
                    "poster_src": "",
                    "tmdb_vote_average": tmdb_extra["tmdb_vote_average"],
                    "tmdb_vote_count": tmdb_extra["tmdb_vote_count"],
                    "tmdb_popularity": tmdb_extra["tmdb_popularity"],
                    "tmdb_overview": tmdb_extra["tmdb_overview"].fillna("").apply(_normalize_text),
                    "tmdb_poster_url": tmdb_extra["tmdb_poster_url"],
                    "tmdb_backdrop_url": tmdb_extra["tmdb_backdrop_url"],
                }
            )
            df = pd.concat([df, extra_df], ignore_index=True)

    overview = df.get("tmdb_overview", pd.Series("", index=df.index)).fillna("")
    df["features_text"] = (
        (df["title"].fillna("") + " ")
        + (df["genres"].fillna("") + " ")
        + (df["director"].fillna("") + " ")
        + (df["cast"].fillna("") + " ")
        + (df["certificate"].fillna("") + " ")
        + (overview + " ")
        + df["genres"].fillna("").apply(_genre_alias_text)
    ).apply(_expand_search_text)

    keep = [
        "title",
        "title_ua",
        "tmdb_title_ua",
        "year",
        "certificate",
        "genres",
        "director",
        "cast",
        "imdb_rating",
        "metascore",
        "duration_min",
        "poster_src",
        "tmdb_vote_average",
        "tmdb_vote_count",
        "tmdb_popularity",
        "tmdb_overview",
        "overview_ua",
        "tmdb_overview_ua",
        "tmdb_poster_url",
        "poster_src_ua",
        "tmdb_poster_url_ua",
        "tmdb_backdrop_url",
        "features_text",
    ]
    text_columns = {
        "title",
        "title_ua",
        "tmdb_title_ua",
        "certificate",
        "genres",
        "director",
        "cast",
        "poster_src",
        "overview_ua",
        "tmdb_overview_ua",
        "tmdb_overview",
        "tmdb_poster_url",
        "poster_src_ua",
        "tmdb_poster_url_ua",
        "tmdb_backdrop_url",
        "features_text",
    }
    for column in keep:
        if column not in df.columns:
            df[column] = "" if column in text_columns else np.nan

    fresh_year = pd.to_numeric(df["year"], errors="coerce").isin(PROTECTED_CATALOG_YEARS)
    has_any_rating = pd.to_numeric(df["imdb_rating"], errors="coerce").gt(0) | pd.to_numeric(
        df["tmdb_vote_average"], errors="coerce"
    ).gt(0)
    df = df[~fresh_year | has_any_rating].copy()

    if MOVIE_CATALOG_LIMIT and len(df) > MOVIE_CATALOG_LIMIT:
        has_poster = df["tmdb_poster_url"].fillna("").astype(str).str.strip().ne("")
        df["_has_poster"] = has_poster.astype(int)
        df["_sort_votes"] = pd.to_numeric(df["tmdb_vote_count"], errors="coerce").fillna(0)
        df["_sort_popularity"] = pd.to_numeric(df["tmdb_popularity"], errors="coerce").fillna(0)
        df["_sort_rating"] = pd.concat(
            [
                pd.to_numeric(df["imdb_rating"], errors="coerce"),
                pd.to_numeric(df["tmdb_vote_average"], errors="coerce"),
            ],
            axis=1,
        ).max(axis=1).fillna(0)
        sorted_df = df.sort_values(
            ["_has_poster", "_sort_votes", "_sort_popularity", "_sort_rating"],
            ascending=False,
        )
        protected_mask = pd.to_numeric(sorted_df["year"], errors="coerce").isin(PROTECTED_CATALOG_YEARS) & sorted_df["_has_poster"].eq(1)
        protected_df = sorted_df[protected_mask]
        regular_df = sorted_df[~protected_mask].head(max(0, MOVIE_CATALOG_LIMIT - len(protected_df)))
        df = pd.concat([protected_df, regular_df], ignore_index=True).drop(
            columns=["_has_poster", "_sort_votes", "_sort_popularity", "_sort_rating"]
        )
        if int(df["tmdb_poster_url"].fillna("").astype(str).str.strip().ne("").sum()) < MOVIE_CATALOG_LIMIT and os.path.exists(tmdb_path):
            poster_keys = set(
                zip(
                    df["title"].fillna("").astype(str).str.lower(),
                    pd.to_numeric(df["year"], errors="coerce"),
                )
            )
            tmdb_fill = tmdb[
                tmdb["tmdb_title"].ne("")
                & tmdb["tmdb_year"].notna()
                & tmdb["tmdb_poster_url"].ne("")
            ].copy()
            tmdb_fill["_key"] = list(zip(tmdb_fill["tmdb_title"].str.lower(), tmdb_fill["tmdb_year"]))
            tmdb_fill = tmdb_fill[~tmdb_fill["_key"].isin(poster_keys)]
            tmdb_fill = tmdb_fill.sort_values(["_has_poster", "tmdb_vote_count", "tmdb_popularity"], ascending=False, na_position="last")
            missing = MOVIE_CATALOG_LIMIT - int(df["tmdb_poster_url"].fillna("").astype(str).str.strip().ne("").sum())
            tmdb_fill = tmdb_fill.head(max(0, missing))
            if not tmdb_fill.empty:
                fill_df = pd.DataFrame(
                    {
                        "title": tmdb_fill["tmdb_title"],
                        "year": tmdb_fill["tmdb_year"],
                        "certificate": "",
                        "genres": tmdb_fill["tmdb_genres"],
                        "director": "",
                        "cast": "",
                        "imdb_rating": np.nan,
                        "metascore": np.nan,
                        "duration_min": np.nan,
                        "poster_src": "",
                        "tmdb_vote_average": tmdb_fill["tmdb_vote_average"],
                        "tmdb_vote_count": tmdb_fill["tmdb_vote_count"],
                        "tmdb_popularity": tmdb_fill["tmdb_popularity"],
                        "tmdb_overview": tmdb_fill["tmdb_overview"].fillna("").apply(_normalize_text),
                        "tmdb_poster_url": tmdb_fill["tmdb_poster_url"],
                        "tmdb_backdrop_url": tmdb_fill["tmdb_backdrop_url"],
                    }
                )
                df = pd.concat(
                    [df[df["tmdb_poster_url"].fillna("").astype(str).str.strip().ne("")], fill_df],
                    ignore_index=True,
                ).head(MOVIE_CATALOG_LIMIT)

    df = df[keep].reset_index(drop=True)
    try:
        df.to_csv(cache_path, index=False, encoding="utf-8")
    except OSError:
        pass
    return df
