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

def add_calculated_fields(df):
    df = set_column_types(df)
    df = format_time_columns(df, 'date_start', 'date_end')
    df['diff_v50'] = ( df['v50'] - df['zone']) 
    df['diff_v85'] = ( df['v85'] - df['zone']) 
    df['diff_v50_perc'] = df['diff_v50'] / 100
    df['diff_v85_perc'] = df['diff_v85'] / df['zone'] * 100
    return df