from lib.imports import *
from models.hybrid import hybrid_recommendation
from utils.preprocessing import load_movies


if __name__ == "__main__":
    movies = load_movies()

    movie_title = "Inception"
    recs = hybrid_recommendation(movie_title, top_n=5)

    print("\nTop 5 movie recommendations for:", movie_title)
    for _, row in recs.iterrows():
        print(
            f"- {row['title']} "
            f"({int(row['year']) if not pd.isna(row['year']) else 'N/A'}) | "
            f"IMDb: {row['imdb_rating'] if not pd.isna(row['imdb_rating']) else 'N/A'}"
        )
