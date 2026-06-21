# CineMatch

CineMatch is a Streamlit movie recommendation app. It uses a precomputed similarity matrix and TMDB poster data to suggest five related movies.

## Run locally

1. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Keep `movie_dict.pkl` and `similarity.pkl` beside `app.py`, or configure direct download URLs with `MOVIE_DICT_URL` and `SIMILARITY_URL`.

3. Set a TMDB API key:

   ```bash
   export TMDB_API_KEY="your-key"
   ```

4. Start the app:

   ```bash
   streamlit run app.py
   ```

On Streamlit Community Cloud, add `TMDB_API_KEY`, `MOVIE_DICT_URL`, and `SIMILARITY_URL` in the app's secrets settings. The data files are intentionally excluded from Git because `similarity.pkl` exceeds GitHub's file-size limit.
