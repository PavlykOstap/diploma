from lib.imports import *
from models.content_based import get_content_recommendations
from utils.preprocessing import load_movies


def hybrid_recommendation(
    title: str,
    top_n: int = 5,
    alpha: float = 0.7,
) -> pd.DataFrame:
    """
    Hybrid recommendation: combines content similarity and normalized IMDb rating.

    score = alpha * similarity + (1 - alpha) * normalized_imdb_rating
    """
    movies = load_movies()
    content_recs = get_content_recommendations(title, top_n=100, movies=movies)
    if content_recs.empty:
        return content_recs

    max_rating = movies["imdb_rating"].max()
    min_rating = movies["imdb_rating"].min()

    def _norm_rating(value: float) -> float:
        if pd.isna(value) or pd.isna(max_rating) or pd.isna(min_rating) or max_rating == min_rating:
            return 0.0
        return (value - min_rating) / (max_rating - min_rating)

    content_recs["imdb_rating_norm"] = content_recs["imdb_rating"].apply(_norm_rating)
    content_recs["hybrid_score"] = (
        alpha * content_recs["similarity"] + (1 - alpha) * content_recs["imdb_rating_norm"]
    )

    return content_recs.sort_values("hybrid_score", ascending=False).head(top_n).reset_index(drop=True)
