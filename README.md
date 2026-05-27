# AI Movie Recommender

Вебсистема для пошуку, фільтрації та AI-рекомендацій фільмів. Проєкт поєднує IMDb-датасети, TMDB-метадані, контентний пошук, схожість фільмів, профіль користувача та список "Подивитись потім".

## Можливості

- пошук фільмів за назвою;
- фільтри за жанром, роком і рейтингом;
- AI-чат із пам'яттю запитів;
- рекомендації схожих фільмів;
- сторінка деталей фільму;
- реєстрація, вхід і профіль через MongoDB;
- список "Подивитись потім";
- перемикач мови UA / EN;
- українські назви й описи, якщо вони є в локальній базі перекладів.

## Технології

- Python
- Streamlit
- pandas, numpy, scikit-learn
- MongoDB
- IMDb / TMDB metadata

## Структура

- `app/streamlit_app.py` - основний Streamlit-додаток.
- `utils/preprocessing.py` - підготовка IMDb/TMDB даних і каталогу фільмів.
- `models/content_based.py` - TF-IDF, пошук за описом і схожі фільми.
- `models/hybrid.py` - гібридне ранжування.
- `models/collaborative.py` - заготовка для collaborative filtering.
- `scripts/start_mongo_27018.ps1` - запуск MongoDB на порту 27018.

## Запуск

1. Встановити залежності:

```bash
pip install -r requirements.txt
```

2. Запустити MongoDB на порту 27018:

```powershell
.\scripts\start_mongo_27018.ps1
```

3. Запустити сайт:

```bash
streamlit run app/streamlit_app.py
```

## Дані

У проєкті використовується підготовлений каталог:

```text
data/movie_catalog_12000_fresh-rated-v1.csv
```

Великі сирі датасети не додаються в репозиторій, щоб не перевищувати обмеження GitHub.

Data courtesy of IMDb.
