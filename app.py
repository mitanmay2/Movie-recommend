import json
import os
from pathlib import Path

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


@st.cache_resource(show_spinner="Loading the recommendation model...")
def load_data():
    data_path = BASE_DIR / "recommendations.json"
    with data_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    movies = data.get("movies", [])
    recommendations = data.get("recommendations", [])
    if not movies or len(movies) != len(recommendations):
        raise ValueError("recommendations.json is missing or invalid.")

    title_to_index = {}
    for index, movie in enumerate(movies):
        title_to_index.setdefault(movie[0], index)

    return movies, recommendations, title_to_index


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


def recommend(movie_title, movies, recommendation_indices, title_to_index, count=5):
    movie_index = title_to_index.get(movie_title)
    if movie_index is None:
        return []

    recommendations = []
    for index in recommendation_indices[movie_index][:count]:
        title, movie_id = movies[index]
        recommendations.append(
            {
                "title": title,
                "movie_id": int(movie_id),
                "poster": fetch_poster(movie_id),
            }
        )

    return recommendations


st.title("CineMatch")
st.caption("Choose a movie and discover five similar films.")

try:
    movies, recommendation_indices, title_to_index = load_data()
except Exception as error:
    st.error(f"Could not load the recommendation data: {error}")
    st.stop()

movie_titles = sorted(title_to_index)
selected_movie = st.selectbox(
    "Select a movie",
    movie_titles,
    index=None,
    placeholder="Start typing a movie title...",
)

if st.button("Recommend", type="primary", disabled=selected_movie is None):
    with st.spinner("Finding movies you may like..."):
        recommendations = recommend(
            selected_movie,
            movies,
            recommendation_indices,
            title_to_index,
        )

    if not recommendations:
        st.warning("No recommendations were found for that movie.")
    else:
        st.subheader(f"Because you liked {selected_movie}")
        columns = st.columns(len(recommendations))
        for column, movie in zip(columns, recommendations):
            with column:
                st.image(movie["poster"], use_container_width=True)
                st.markdown(f"**{movie['title']}**")

