import os
import pickle
from pathlib import Path

import pandas as pd
import requests
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
PLACEHOLDER_POSTER = "https://placehold.co/500x750/161b22/ffffff?text=No+Poster"


st.set_page_config(
    page_title="CineMatch",
    layout="wide",
)


def get_setting(name: str) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    try:
        return st.secrets.get(name)
    except FileNotFoundError:
        return None


TMDB_API_KEY = get_setting("TMDB_API_KEY")


def ensure_data_file(filename: str, url_env_name: str) -> Path:
    path = BASE_DIR / filename
    if path.exists():
        return path

    url = get_setting(url_env_name)
    if not url:
        raise FileNotFoundError(
            f"{filename} is missing. Add it locally or set {url_env_name} "
            "to a direct download URL."
        )

    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()

    with path.open("wb") as file:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                file.write(chunk)

    return path


@st.cache_resource(show_spinner="Loading the recommendation model...")
def load_data():
    movie_dict_path = ensure_data_file("movie_dict.pkl", "MOVIE_DICT_URL")
    similarity_path = ensure_data_file("similarity.pkl", "SIMILARITY_URL")

    with movie_dict_path.open("rb") as file:
        movies_data = pickle.load(file)

    if callable(movies_data):
        movies_data = movies_data()

    if isinstance(movies_data, pd.DataFrame):
        movies = movies_data
    elif isinstance(movies_data, dict):
        movies = pd.DataFrame(movies_data)
    else:
        raise TypeError("movie_dict.pkl does not contain a DataFrame or dictionary.")

    required_columns = {"title", "movie_id"}
    missing_columns = required_columns.difference(movies.columns)
    if missing_columns:
        raise ValueError(
            "Movie data is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    with similarity_path.open("rb") as file:
        similarity = pickle.load(file)

    if len(similarity) != len(movies):
        raise ValueError("The movie data and similarity matrix have different sizes.")

    return movies.reset_index(drop=True), similarity


@st.cache_data(ttl=24 * 60 * 60, show_spinner=False)
def fetch_poster(movie_id: int) -> str:
    if not TMDB_API_KEY:
        return PLACEHOLDER_POSTER

    try:
        response = requests.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}",
            params={"api_key": TMDB_API_KEY, "language": "en-US"},
            timeout=5,
        )
        response.raise_for_status()
        poster_path = response.json().get("poster_path")
        if poster_path:
            return f"https://image.tmdb.org/t/p/w500{poster_path}"
    except requests.RequestException:
        pass

    return PLACEHOLDER_POSTER


def recommend(movie_title: str, movies: pd.DataFrame, similarity, count: int = 5):
    matches = movies.index[movies["title"] == movie_title].tolist()
    if not matches:
        return []

    movie_index = matches[0]
    ranked_movies = sorted(
        enumerate(similarity[movie_index]),
        key=lambda item: item[1],
        reverse=True,
    )

    recommendations = []
    for index, _score in ranked_movies:
        if index == movie_index:
            continue

        row = movies.iloc[index]
        movie_id = int(row["movie_id"])
        recommendations.append(
            {
                "title": str(row["title"]),
                "movie_id": movie_id,
                "poster": fetch_poster(movie_id),
            }
        )
        if len(recommendations) == count:
            break

    return recommendations


st.title("CineMatch")
st.caption("Choose a movie and discover five similar films.")

try:
    movies, similarity = load_data()
except Exception as error:
    st.error(f"Could not load the recommendation data: {error}")
    st.stop()

movie_titles = sorted(movies["title"].dropna().astype(str).unique())
selected_movie = st.selectbox(
    "Select a movie",
    movie_titles,
    index=None,
    placeholder="Start typing a movie title...",
)

if st.button("Recommend", type="primary", disabled=selected_movie is None):
    with st.spinner("Finding movies you may like..."):
        recommendations = recommend(selected_movie, movies, similarity)

    if not recommendations:
        st.warning("No recommendations were found for that movie.")
    else:
        st.subheader(f"Because you liked {selected_movie}")
        columns = st.columns(len(recommendations))
        for column, movie in zip(columns, recommendations):
            with column:
                st.image(movie["poster"], use_container_width=True)
                st.markdown(f"**{movie['title']}**")

