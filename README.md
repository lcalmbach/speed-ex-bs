# speed-ex-bas (under construction, 2021-10-10)

This app is written in Python and uses the frameworks [streamlit](https://streamlit.io) and [altair](https://altair-viz.github.io/). It downloads traffic speed data from [opendata.bs](https://https://data.bs.ch/pages/home/) and provides several options to analyse the data.  

The app is published [here](https://github.com/lcalmbach/speed-ex-bss). To run the code on your local machine follow these steps to install the required environment:
1. git clone https://https://github.com/lcalmbach/speed-ex-bs
2. create and activate a virtual environment and install the libraries, for example in Windows:
    ```
    > Python -m venv env
    > env\scripts\activate
    > (env) pip install -r requirements.txt
    > (env) pip install -r requirements.txt
    ```
1. run streamlit server locally by typing:
    ```
    > (env) streamlit run app.py
    ```
1. Open App in Browser on http://localhost:8501