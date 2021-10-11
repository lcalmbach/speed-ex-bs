import streamlit as st
import pandas as pd



def dummy():
    # df = pd.read_parquet('./violations.parquet')
    # st.write(df.head(100))
    st.info("noch nicht implementiert, kommt bald!")

def show_menu(texts, conn):    
    dic_menu = {'1': 'Statistik nach Zone', '2': 'Statistik nach Messtation', '3': 'Statistik nach Wochentag', '4': 'Statistik nach Tageszeit'}
    menu_item = st.sidebar.selectbox('Optionen', list(dic_menu.keys()),
        format_func=lambda x: dic_menu[x])   
    if menu_item == '1':
        dummy()
    elif menu_item ==  '2':
        dummy()
    elif menu_item ==  '3':
        dummy()
    elif menu_item ==  '4':
        dummy()
                