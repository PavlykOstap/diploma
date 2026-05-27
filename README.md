## Вебсистема для пошуку та підбору фільмів

Проєкт демонструє просту рекомендаційну систему фільмів на основі IMDb-датасетів, TMDB-метаданих та контентного/гібридного підходів.

### Стек

- **Python**
- **pandas, numpy, scikit-learn**
- **Streamlit** - вебінтерфейс

### Структура

- `utils/preprocessing.py` - завантаження та уніфікація IMDb CSV, збагачення TMDB-даними, побудова `features_text`.
- `models/content_based.py` - TF-IDF + cosine similarity, пошук за назвою та описом.
- `models/hybrid.py` - гібридний скоринг: similarity + IMDb рейтинг.
- `app/streamlit_app.py` - вебдодаток Streamlit.
- `main.py` - консольний приклад використання `hybrid_recommendation`.

### Запуск

1. Створити віртуальне середовище, якщо потрібно:

```bash
python -m venv .venv
```

2. Активувати середовище та встановити залежності:

```bash
pip install -r requirements.txt
```

3. Запустити вебдодаток:

```bash
streamlit run app/streamlit_app.py
```

4. Для тесту з консолі:

```bash
python main.py
```

> Якщо поточне `.venv` не запускається, видаліть його та створіть заново командою з першого кроку.
