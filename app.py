import streamlit as st
import pandas as pd
import pickle
import requests
import time

# Set page configuration
st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

# Title and description
st.title('🎬 Movie Recommender System')
st.markdown("""
Discover movies similar to your favorites! Select a movie below and get personalized recommendations.
""")

# Load data
@st.cache_data
def load_data():
    try:
        movies_names = pickle.load(open('model_dict.pkl', 'rb'))
        df = pd.DataFrame(movies_names)
        similarity = pickle.load(open('similarity.pkl', 'rb'))
        return df, similarity
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.stop()

df, similarity = load_data()

# Improved poster fetching function with retries
def fetch_poster(movie_id, retries=2):
    api_key = "a32c5741a3cff043c961972c1083495b"
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
    headers = {"User-Agent": "Mozilla/5.0"}

    for attempt in range(retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            poster_path = data.get('poster_path')
            if poster_path:
                return f"https://image.tmdb.org/t/p/w500/{poster_path}"
            return None
        except requests.exceptions.RequestException as e:
            if attempt < retries:
                time.sleep(1)  # wait before retry
            else:
                st.warning(f"⚠️ Failed to fetch poster for movie ID {movie_id}")
                return None

# Recommendation function with error handling
def recommend(movie):
    try:
        movie_ind = df[df['title'] == movie].index[0]
        distances = similarity[movie_ind]
        movie_list = sorted(enumerate(distances), reverse=True, key=lambda x: x[1])[1:6]

        names = []
        posters = []

        for i in movie_list:
            movie_id = df.iloc[i[0]].id
            names.append(df.iloc[i[0]].title)
            posters.append(fetch_poster(movie_id))

        return names, posters
    except IndexError:
        st.error("❌ Selected movie not found in our database")
    except Exception as e:
        st.error(f"❌ Recommendation error: {str(e)}")
    return [], []

# UI Section
with st.form("movie_recommender_form"):
    movie_title = st.selectbox(
        "Select a movie:",
        df['title'].values,
        index=min(100, len(df) - 1),
        help="Choose a movie to get similar recommendations"
    )
    submitted = st.form_submit_button("🚀 Get Recommendations")

if submitted:
    with st.spinner('🔍 Finding similar movies...'):
        names, posters = recommend(movie_title)
        time.sleep(0.5)  # Show spinner for minimum time

    if not names:
        st.warning("No recommendations found. Please try another movie.")
    else:
        st.success(f"🎉 Recommended movies similar to **{movie_title}**:")
        cols = st.columns(5)
        placeholder = "https://via.placeholder.com/500x750?text=No+Poster"

        for i, col in enumerate(cols):
            with col:
                st.markdown(
                    f"<p style='text-align:center; height:60px;' title='{names[i]}'>"
                    f"<b>{names[i]}</b></p>",
                    unsafe_allow_html=True
                )

                poster_url = posters[i] if posters[i] else placeholder
                st.image(
                    poster_url,
                    caption=names[i] if posters[i] else "Poster not available"
                )

                if posters[i]:
                    st.caption("[Source: The Movie Database](https://www.themoviedb.org/)")

# Footer
st.markdown("---")
st.caption("Built with Streamlit • Movie data from [The Movie Database](https://www.themoviedb.org/)")
