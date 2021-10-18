import streamlit as st 
from streamlit_lottie import st_lottie
import app_info
import app_map
import app_stats
import requests
import const as cn
import json
import sqlite3
from queries import qry
import database as db

__version__ = '0.0.9'
__author__ = 'Lukas Calmbach'
__author_email__ = 'lcalmbach@gmail.com'
VERSION_DATE = '2021-10-18'
my_name = 'Geschwindigkeits-Übertretungen in Basel-Stadt'

LOTTIE_URL = 'https://assets8.lottiefiles.com/private_files/lf30_zcwz0fha.json'
SOURCE_URL = 'https://data.bs.ch/explore/dataset/100097'
GIT_REPO = 'https://github.com/lcalmbach/speed-ex-bs'
APP_INFO = f"""<div style="background-color:powderblue; padding: 10px;border-radius: 15px;">
    <small>App created by <a href="mailto:{__author_email__}">{__author__}</a><br>
    version: {__version__} ({VERSION_DATE})<br>
    source: <a href="{SOURCE_URL}">data.bs</a>
    <br><a href="{GIT_REPO}">git-repo</a>
    """
DB_FILE_PATH = "velocity.sqlite3"


def get_connection():
    conn = sqlite3.connect(DB_FILE_PATH)
    return conn

@st.experimental_memo()
def get_lottie():
    ok=True
    r=''
    try:
        r = requests.get(LOTTIE_URL).json()
    except:
        st.write(r.status)
        ok = False
    return r,ok

#@st.experimental_memo()
def get_texts():
    t = json.loads(open(cn.TEXTS, encoding='utf-8').read())
    return t
    
def main():
    st.set_page_config(
        page_title=my_name,
        layout="wide")

    lottie_search_names, ok = get_lottie()
    if ok:
        with st.sidebar:
            st_lottie(lottie_search_names, height=80, loop=False)

    texts = get_texts()
    conn = db.get_pg_connection()
    menu_action = st.sidebar.selectbox('Menu',['Info','Karte','Statistik'])
    if menu_action == 'Info':
        app_info.show_menu(texts['app_info'], conn)
    elif menu_action == 'Karte':
        app_map.show_menu(texts['app_map'], conn)
    elif menu_action == 'Statistik':
        app_stats.show_menu(texts['app_stats'], conn)
    st.sidebar.markdown(APP_INFO, unsafe_allow_html=True)

if __name__ == '__main__':
    main()
