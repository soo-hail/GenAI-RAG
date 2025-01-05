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

# LOAD DATA-FRAME FROM pickle FILE
with open('artifacts/rating_data.pkl', 'rb') as f:
    df = pickle.load(f)

# RANDOMLY PICK 30 MOVIES (tmdbId) TO ADD MOVIES TO THE HOME PAGE.
genres_unique_list = ['Sci-Fi', 'Adventure', 'Comedy', 'Action', 'Horror', 'Romance'] 
home_df = np.random.choice(df['tmdbId'].unique(), size= 40, replace = False)  # Randomly select 30 unique tmdbIds

# SET PAGE CONFIGURATION FOR FULL-SCREEN.
st.set_page_config(
    page_title="Movie Recommendation Engine",
    layout="wide",  # Full-screen mode
    initial_sidebar_state="collapsed",  # Collapse the sidebar
)


# DISPLAY MOVIE POSTERS IN GRID WITH 5 COLUMNS
for i in range(0, len(home_df), 10):  # Increment by 5 columns
    cols = st.columns(10)  # Adjust to 5 columns per row
    
    for idx, col in enumerate(cols):  # Loop to iterate columns in a row
        if i + idx < len(home_df):  # Ensure we don't go out of bounds
            movie_id = home_df[i + idx]  # Get tmdbId for movie
            movie = df[df['tmdbId'] == movie_id].iloc[0]  # Get movie data from df
            
            with col:
                image_url = fetch_poster(movie_id)
                
                if st.button(f"Watch", key=f"movie_{movie['movieId']}"):
                    pass
                
                # Embed image with fixed height and width using HTML                    
                st.markdown(
                    f"""
                    <img src="{image_url}" style="width:140px; height:200px;">
                    """,
                    unsafe_allow_html=True,
                )
                st.write(movie["title"])  # Display movie title
                

