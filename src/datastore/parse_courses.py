from typing import Any
import requests
import pandas as pd


def add_list_string(list_str:str, added_str:str):
    if list_str == '':
        return added_str
    else:
        return list_str + ' + ' + added_str




def parse_data(course_page):
    lines = course_page.split('\n')
    course_data: list[dict[str, str]] = []
    session="Normal"
    i : int=0
    while not(lines[i].startswith('------------')):
        i+=1
    i+=1
    for line in lines[i:]:
        line=line.replace('&amp;','&')
        if line=='':
            break
        if line[5:7]=='**':
            course_data[-1]['additional_notes']=add_list_string(course_data[-1]['additional_notes'],line[7:].strip())
            continue
        if line[13:23]=='SESSION  B':
            session='B'
            continue
        elif line[13:23]=='SESSION  C':
            session='C'
            continue
        current_course: dict[str, str]={
            "available_spots": line[0:5].strip(),
            "capacity": line[5:11].strip(),
            "prefix": line[11:16].strip(),
            "course_number": line[16:21].strip(),
            "type": line[21:27].strip(),
            "section": line[27:32].strip(),
            "title": line[32:55].strip(),
            "credits": line[55:60].strip(),
            "time": line[60:72].strip(),
            "days": line[72:79].strip(),
            "room": line[79:84].strip(),
            "building": line[84:100].strip(),
            "spec": line[100:117].strip(),
            "instructor": line[117:].strip(),
            "session": session,
            "additional_meet_times":'',
            "additional_meet_days":'',
            "additional_notes":''
        }
        if current_course['course_number']=='':
            if current_course['type']=='LAB':
                course_data[-1]['type']=='LECLAB'
                course_data[-1]['additional_meet_times']=add_list_string(course_data[-1]['additional_meet_times'],current_course['time'])
                course_data[-1]['additional_meet_days']=add_list_string(course_data[-1]['additional_meet_days'],current_course['days'])
            elif current_course['spec']!='':
                course_data[-1]['spec'] = add_list_string(course_data[-1]['spec'],current_course['spec'])
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