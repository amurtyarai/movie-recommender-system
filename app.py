import os
import pickle
import requests
import base64
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Movie Recommender System",
    page_icon="🎬",
    layout="wide"
)

# Custom Glassmorphism Theme & UI CSS
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    h1 {
        color: #f8fafc;
        font-family: 'Inter', system-ui, sans-serif;
        text-align: center;
        margin-bottom: 0.2rem;
        background: linear-gradient(135deg, #e0e7ff 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.5rem;
    }
    .subtitle {
        text-align: center;
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .movie-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 10px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .movie-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 12px 28px rgba(99, 102, 241, 0.35);
        border-color: rgba(99, 102, 241, 0.5);
    }
    .movie-title {
        color: #f8fafc;
        font-weight: 600;
        font-size: 0.95rem;
        margin-top: 10px;
        min-height: 44px;
        text-align: center;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        line-height: 1.3;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        color: white;
        border: none;
        padding: 0.65rem 1.5rem;
        font-weight: 600;
        font-size: 1.05rem;
        border-radius: 10px;
        box-shadow: 0 4px 14px 0 rgba(99, 102, 241, 0.4);
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #4f46e5 0%, #9333ea 100%);
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.65);
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

def get_placeholder_poster(title):
    encoded_title = title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    words = encoded_title.split()
    line1 = " ".join(words[:3]) if len(words) > 0 else ""
    line2 = " ".join(words[3:6]) if len(words) > 3 else ""
    line3 = " ".join(words[6:]) if len(words) > 6 else ""
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="300" height="450" viewBox="0 0 300 450">
      <defs>
        <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#1e1b4b;stop-opacity:1" />
          <stop offset="50%" style="stop-color:#0f172a;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#31104b;stop-opacity:1" />
        </linearGradient>
      </defs>
      <rect width="300" height="450" fill="url(#grad)" rx="16" />
      <rect x="12" y="12" width="276" height="426" fill="none" stroke="#475569" stroke-width="1.5" stroke-dasharray="6,6" rx="12" />
      <circle cx="150" cy="160" r="48" fill="#1e293b" stroke="#818cf8" stroke-width="3"/>
      <text x="150" y="172" font-family="Segoe UI, sans-serif" font-size="40" text-anchor="middle">🎬</text>
      <text x="150" y="270" font-family="Segoe UI, sans-serif" font-size="20" font-weight="bold" fill="#f8fafc" text-anchor="middle">
        <tspan x="150" dy="0">{line1}</tspan>
        {"<tspan x='150' dy='26'>" + line2 + "</tspan>" if line2 else ""}
        {"<tspan x='150' dy='26'>" + line3 + "</tspan>" if line3 else ""}
      </text>
      <rect x="75" y="385" width="150" height="28" fill="#312e81" rx="14" />
      <text x="150" y="403" font-family="Segoe UI, sans-serif" font-size="11" font-weight="600" fill="#a5b4fc" text-anchor="middle">MOVIE RECOMMENDER</text>
    </svg>'''
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode('utf-8')).decode('utf-8')

@st.cache_data(show_spinner=False, ttl=86400)
def fetch_poster(movie_id, title):
    # 1. Primary Source: OMDb API (Fetches real IMDb high-res movie posters)
    for api_key in ['trilogy', '727299d4', 'b7027c4']:
        try:
            url = f"http://www.omdbapi.com/?t={requests.utils.quote(title)}&apikey={api_key}"
            response = requests.get(url, timeout=2.5)
            if response.status_code == 200:
                data = response.json()
                poster_url = data.get('Poster')
                if poster_url and poster_url != 'N/A' and poster_url.startswith('http'):
                    return poster_url
        except Exception:
            pass

    # 2. Secondary Source: Wikipedia Thumbnail API
    try:
        wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(title)}"
        headers = {'User-Agent': 'MovieRecommenderApp/1.0'}
        response = requests.get(wiki_url, headers=headers, timeout=2.0)
        if response.status_code == 200:
            thumb = response.json().get('thumbnail', {}).get('source')
            if thumb and thumb.startswith('http'):
                return thumb
    except Exception:
        pass

    # 3. Tertiary Source: TMDB API (if accessible)
    try:
        tmdb_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US"
        response = requests.get(tmdb_url, timeout=2.0)
        if response.status_code == 200:
            data = response.json()
            poster_path = data.get('poster_path')
            if poster_path:
                return "https://image.tmdb.org/t/p/w500/" + poster_path
    except Exception:
        pass

    # 4. Fallback: Styled SVG Poster Card
    return get_placeholder_poster(title)

def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_movie_names = []
    recommended_movie_posters = []
    for i in distances[1:6]:
        movie_id = movies.iloc[i[0]].movie_id
        title = movies.iloc[i[0]].title
        recommended_movie_names.append(title)
        recommended_movie_posters.append(fetch_poster(movie_id, title))

    return recommended_movie_names, recommended_movie_posters

st.markdown("<h1>🍿 Content-Based Movie Recommender</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Discover movies similar to your favorites powered by TMDB Dataset & Cosine Similarity</p>", unsafe_allow_html=True)

# Load pickled models
@st.cache_resource
def load_data():
    movie_dict_path = 'model/movie_list.pkl'
    similarity_path = 'model/similarity.pkl'
    
    if not os.path.exists(movie_dict_path) or not os.path.exists(similarity_path):
        st.error("Model files not found! Please run generate_model.py first.")
        st.stop()
        
    movies = pickle.load(open(movie_dict_path, 'rb'))
    similarity = pickle.load(open(similarity_path, 'rb'))
    return movies, similarity

movies, similarity = load_data()
movie_list = movies['title'].values

selected_movie = st.selectbox(
    "Type or select a movie from the dropdown:",
    movie_list,
    index=0
)

if st.button('✨ Show Recommendation'):
    with st.spinner('Fetching real movie posters & recommendations...'):
        recommended_movie_names, recommended_movie_posters = recommend(selected_movie)
        
        st.markdown("<br>### 🎬 Recommended Movies", unsafe_allow_html=True)
        cols = st.columns(5)
        for idx, col in enumerate(cols):
            with col:
                st.image(recommended_movie_posters[idx], use_container_width=True)
                st.markdown(f"<div class='movie-title'>{recommended_movie_names[idx]}</div>", unsafe_allow_html=True)
