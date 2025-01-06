import pickle
import requests
import pandas as pd
import streamlit as st

# LOAD THE PROCESSED-DATA(AS DATAFRAME) AND CONSINE-SIMILARITY MATRIX.
with open('movie_data.pkl', 'rb') as f:
    df, cosine_sim = pickle.load(f)
    
# FUNCTION TO GET MOVIE-RECOMENDATION.
def get_recommendations(title, cosine_sim = cosine_sim):
    
    idx = df[df['original_title'].str.lower() == title.lower()].index[0] # GET INDEX(ROW-NUMBER) OF THE MOVIE.
    sim_scores = list(enumerate(cosine_sim[idx])) # GET ALL THE SIMILARITY-SCORES OF A GIVEN MOVIE WITH OTHER MOVIES.
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse = True) # SORT SIMILARITY SCORES. 
    sim_scores = sim_scores[1:11]  # GET TOP 10 MOVIES
    movie_indices = [i[0] for i in sim_scores]
    
    return df['original_title'].iloc[movie_indices] # RETRIVES TITLES OF MOVIES FROM THE DATA-FRAME USING PROVIDED INDEICES OF MOVIES.

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

    
# SETUP USER-INTERFACE USING STREAMLIT.
st.title('Movie Recommendation Engine')

selected_movie = st.selectbox("Select a movie:", df['original_title'].values)        
        
if st.button('Recommend'):
    # GET RECOMMENDED MOVIES BASED ON SELECTED-MOVIES.
    recommendations = get_recommendations(selected_movie)
    print(recommendations)
    st.write("Top 10 recommended movies:")

    for i in range(0, 10, 5): # LOOP TO ITERATE 2 ROWS(BECAUSE IT INCREMENTS BY 5).
        # CREATE 5 COLUMNS FOR EACH ROW.
        cols = st.columns(5)
        
        for col, idx in zip(cols, range(i, i + 5)): # LOOP TO ITERATE COLUMNS IN A ROW.
            # IDX ---> REPRESENTS INDEX OF RECOMMENDED MOVIES IN 'recommendations'
            if idx < len(recommendations):
                movie_index = recommendations.index[idx]
                movie_title = recommendations.iloc[idx]
                movie_id = df.loc[movie_index, 'id']
                
                poster_url = fetch_poster(movie_id)
                
                with col:
                    st.image(poster_url, width=130)
                    st.write(movie_title)
                
                
        