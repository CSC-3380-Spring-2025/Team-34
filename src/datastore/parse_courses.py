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
            course_data[-1]['additional_notes']=add_list_string(course_data[-1]['additional_notes'],line[7:].strip(), ' + ')
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
            "special_info": line[100:117].strip(),
            "instructor": line[117:].strip(),
            "session": session,
            "additional_meet_times":'',
            "additional_meet_days":'',
            "additional_notes":''
        }
        if current_course['available_spots']=="(F)":
            current_course['available_spots']=0
        course_string=current_course['prefix'] + ' ' + current_course['title']
        if course_string in queued_notes:
            current_course['additional_notes']=add_list_string(current_course['additional_notes'],queued_notes[course_string],' + ')
            queued_notes.remove(course_string)
        if current_course['course_number']=='':
            if current_course['type']=='LAB':
                course_data[-1]['type']=='LECLAB'
                course_data[-1]['additional_meet_times']=add_list_string(course_data[-1]['additional_meet_times'],current_course['time'], ' + ')
                course_data[-1]['additional_meet_days']=add_list_string(course_data[-1]['additional_meet_days'],current_course['days'], ' + ')
            elif current_course['special_info']!='':
                course_data[-1]['special_info'] = add_list_string(course_data[-1]['special_info'],current_course['special_info'], ' + ')
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
    create_csv(parse_page('https://appl101.lsu.edu/booklet2.nsf/All/67FD57ECBF3676C486258BAC002C42AB?OpenDocument'), 'csc_courses')