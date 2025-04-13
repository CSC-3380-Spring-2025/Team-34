import parse_courses as pc


def collect_multi_department_data(links):
    full_data: list[dict[str, str]] = []
    for link in links:
        full_data.extend(pc.parse_page(link))
    return full_data

def make_multi_csv(links):
    pc.create_csv(collect_multi_department_data(links), 'multi_department_data')

def make_multi_parquet(links):
    pc.create_parquet(collect_multi_department_data(links), 'multi_department_data')

def collect_default_data():
    links = ['https://appl101.lsu.edu/booklet2.nsf/All/67FD57ECBF3676C486258BAC002C42AB?OpenDocument',
             'https://appl101.lsu.edu/booklet2.nsf/All/2719C3AEB8F7AE3986258BAC002C42D6?OpenDocument']
    return collect_multi_department_data(links)
