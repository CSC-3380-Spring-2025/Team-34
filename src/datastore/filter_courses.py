import pandas as pd

def filter_courses_level(df : pd.DataFrame,level : int):
    df['course_number'] = pd.to_numeric(df['course_number'],errors='coerce')
    df_filtered=df[(df['course_number'] >= level*1000) & (df['course_number'] < (level+1)*1000)]
    return df_filtered
def filter_courses_instructor(df : pd.DataFrame,inst:string):
    df_filtered=df[df['instructor']==inst]
    return df_filtered
