from typing import Any
import requests
import pandas as pd


def add_list_string(list_str:str, added_str:str, adder:str):
    if list_str == '':
        return added_str
    else:
        return list_str + adder + added_str




def parse_data(course_page):
    lines = course_page.split('\n')
    course_data: list[dict[str, str]] = []
    session="Normal"
    queued_notes: dict[str, str] = {}
    i : int=0
    while not(lines[i].startswith('------------')):
        i+=1
    i+=1
    for line in lines[i:]:
        line=line.replace('&amp;','&')
        season_check=line[0:6].strip()
        if (line=='' or season_check=='Fall' or season_check.strip()=='Spring' or line[0:5].strip()=='</PRE'):
            continue
        if line[5:7]=='**':
            course_data[-1]['Additional Notes']=add_list_string(course_data[-1]['Additional Notes'],line[7:].strip(), ' + ')
            continue
        if line[6:9]=='***':
            course_name=line[11:22].strip()
            if course_name in queued_notes:
                queued_notes[course_name]=add_list_string(queued_notes[course_name], line[32:].strip(),' ')
            else :
                queued_notes[course_name]=line[32:].strip()
            continue
        if 'SESSION  B' in line:
            session='B'
            continue
        elif 'SESSION  C' in line:
            session='C'
            continue
        current_course: dict[str, str]={
            "Available Spots": line[0:5].strip(),
            "Capacity": line[5:11].strip(),
            "Prefix": line[11:16].strip(),
            "Course Number": line[16:21].strip(),
            "Type": line[21:27].strip(),
            "Section": line[27:32].strip(),
            "Title": line[32:55].strip(),
            "Credits": line[55:60].strip(),
            "Time": line[60:72].strip(),
            "Days": line[72:79].strip(),
            "Room": line[79:84].strip(),
            "Building": line[84:100].strip(),
            "Special Info": line[100:117].strip(),
            "Instructor": line[117:].strip(),
            "Session": session,
            "Additional Meet Times":'',
            "Additional Meet Days":'',
            "Additional Notes":''
        }
        course_string=current_course['Prefix'] + ' ' + current_course['Title']
        if course_string in queued_notes:
            current_course['Additional Notes']=add_list_string(current_course['Additional Notes'],queued_notes[course_string],' + ')
            queued_notes.remove(course_string)
        if current_course['Course Number']=='':
            if current_course['Type']=='LAB':
                course_data[-1]['Type']=='LECLAB'
                course_data[-1]['Additional Meet Times']=add_list_string(course_data[-1]['Additional Meet Times'],current_course['Time'], ' + ')
                course_data[-1]['Additional Meet Days']=add_list_string(course_data[-1]['Additional Meet Days'],current_course['Days'], ' + ')
            elif current_course['Special Info']!='':
                course_data[-1]['Special Info'] = add_list_string(course_data[-1]['Special Info'],current_course['Special Info'], ' + ')
        else:
            course_data.append(current_course)
    return course_data

def parse_page(url):
    page = requests.get(url,verify=False)
    return parse_data(page.text)
def create_parquet(data,name):
    df:pd.DataFrame=pd.DataFrame(data)
    df.to_parquet("{}.parquet".format(name), engine="pyarrow")
def create_csv(data,name):
    df:pd.DataFrame=pd.DataFrame(data)
    df.to_csv("{}.csv".format(name),index=False)

if __name__ == '__main__':
    create_parquet(parse_page('https://appl101.lsu.edu/booklet2.nsf/All/67FD57ECBF3676C486258BAC002C42AB?OpenDocument'), 'csc_courses')