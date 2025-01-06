import pickle
import requests
import streamlit as st
import pandas as pd
import numpy as np

# FETCH MOVIE POSTERS FROM TMDB-API
def fetch_poster(movie_id):
    api_key = '7b995d3c6fd91a2284b4ad8cb390c7b8'
    url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}'
    
    # REQUEST
    response = requests.get(url)
    
    # FETCH-POSTER PATH.
    data = response.json()
    poster_path = data['poster_path']
    full_path = f"https://image.tmdb.org/t/p/w500{poster_path}"
    
    return full_path

# LOAD DATA-FRAME FROM pickle FILE.
with open('artifacts/genres_data.pkl', 'rb') as f:
    genres_df = pickle.load(f)

# PICK RANDOM 10 MOVIES FROM EVERY(GIVEN) GENRES.
# genres_list = ['Science Fiction', 'History', 'Action', 'Horror', 'Comedy', 'Romance']
genres_list = genres_df['genres'].unique()
genres_list = genres_list[(genres_list != None) & (genres_list != 'TV Movie') & (genres_list != 'Foreign')]

# SET PAGE CONFIGURATION FOR FULL-SCREEN.
st.set_page_config(
    page_title="Movie Recommendation Engine",
    layout="wide",  # Full-screen mode
    initial_sidebar_state="collapsed",  # Collapse the sidebar
)

# DISPLAY MOVIE POSTERS IN HOME-PAGE.
for genre in genres_list:
    st.subheader(f"{genre} Movies")
    
    # Filter movies by genre and pick 10 random movies (or all if less than 10)
    # genre_movies = genres_df[genres_df['genres'] == genre]['id'].drop_duplicates().head(10).tolist()
    genre_movies = genres_df[genres_df['genres'] == genre]['id'].drop_duplicates().sample(n=10).tolist()
    
    # Create columns for displaying posters
    cols = st.columns(10)
    
    for col, movie_id in zip(cols, genre_movies):
        with col: 
            if st.button('Watch', key = f'{movie_id}'):
                pass
            # Fetch and display the poster for each movie
            st.image(fetch_poster(movie_id), width=130)
            st.caption(f"{genres_df[genres_df['id'] == movie_id]['original_title'].drop_duplicates().iloc[0]}")
            
                

