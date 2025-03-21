import parse_courses as pc

def collect_multi_department_data(links):
    full_data=list[dict[str, str]]
    for link in links:
        full_data.extend(pc.parse_page(link))
    pc.create_csv(full_data,'lsu_data')

links=['https://appl101.lsu.edu/booklet2.nsf/All/67FD57ECBF3676C486258BAC002C42AB?OpenDocument', 'https://appl101.lsu.edu/booklet2.nsf/All/2719C3AEB8F7AE3986258BAC002C42D6?OpenDocument']