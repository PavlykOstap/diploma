"""
Placeholder for collaborative filtering.

The current datasets do not contain user-item ratings such as userId/movieId,
so a real collaborative model cannot be trained yet. If such data is added
later, this module is the place for an SVD, KNN, or matrix-factorization model.
"""

from lib.imports import *


def predict_rating(user_id: int, movie_title: str) -> float:
    """
    Return a neutral fallback rating until user-item data is available.
    """
    return 0.0
