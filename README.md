# CineMatch

CineMatch is a Streamlit movie recommendation app. It uses a compact precomputed recommendation index and TMDB poster data to suggest five related movies.

## Run locally

1. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Optionally set a TMDB API key to show movie posters:

   ```bash
   export TMDB_API_KEY="your-key"
   ```

3. Start the app:

   ```bash
   streamlit run app.py
   ```

On Streamlit Community Cloud, add `TMDB_API_KEY` in the app's secrets settings to show movie posters. The app still works with placeholders when no key is configured.

