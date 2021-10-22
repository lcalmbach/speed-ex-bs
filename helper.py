import pandas as pd
import const as cn
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode

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
    df = format_time_columns(df, ('start_date', 'end_date'), cn.FORMAT_DMY)
    df['diff_v50'] = ( df['v50'] - df['zone']) 
    df['diff_v85'] = ( df['v85'] - df['zone']) 
    df['diff_v50_perc'] = df['diff_v50'] / 100
    df['diff_v85_perc'] = df['diff_v85'] / df['zone'] * 100
    return df

def show_table(data, formatted_columns):
        """
        displays the selected columns in a table
        """

        def get_format():
            gb = GridOptionsBuilder.from_dataframe(data)
            gb.configure_default_column(groupable=False, value=True, enableRowGroup=False, aggFunc='sum', editable=False)
            gb.configure_grid_options(domLayout='normal')
            for row in formatted_columns:
                if row['column_format'] != {}:
                    x = row['column_format']
                    gb.configure_column(row['label'], type=x['type'], precision=x['precision'])
            return gb.build()

        if len(data)>0:
            gridOptions = get_format()
            AgGrid(data,gridOptions=gridOptions)
        else:
            pass

def replace_day_ids(df, col):
    week_dic = {0: 'Sonntag', 1: 'Montag', 2: 'Dienstag', 3: 'Mittwoch', 4: 'Donnerstag', 5: 'Freitag', 6: 'Samstag'}
    return df.replace({col: week_dic})

def add_leading_zeros(df, col,len):
        """convert the month column

        Args:
            df ([type]): [description]

        Returns:
            [type]: [description]
        """
        df[col] = df[col].astype(int)
        df[col] = df[col].astype(str)
        df[col]  = df[col].astype(str).str.zfill(len)
        return df