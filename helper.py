import pandas as pd

def set_column_types(df:pd.DataFrame)->pd.DataFrame:
    if 'latitude' in df.columns:
        df['latitude']=df['latitude'].astype('float')
        df['longitude']=df['longitude'].astype('float')
    if 'start_date' in df.columns:
        df['start_date'] = pd.to_datetime(df['start_date'])
        df['end_date'] = pd.to_datetime(df['end_date'])
    return df

def format_time_columns(df:pd.DataFrame, cols: tuple, fmt):
    for col in cols:
        df[col].apply(lambda x: x.strftime(fmt))
    return df