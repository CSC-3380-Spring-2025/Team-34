| Date       | Version | Coder       | Descriptions                                   |
|------------|---------|-------------|------------------------------------------------|
| 2025/04/22 | 1.0.0   | Baron Davis | Initial setup of team-34 project structure. Created version history and version number files. |
| 2025/04/22 | 1.0.1   | Baron Davis | Fixed hidden buttons on sidebar on main page. |
| 2025/04/23 | 1.0.2   | Christian Gamble | Added Cpu ussage and performance. |
| 2025/04/23 | 1.0.3   | Christian Gamble | csv and parquet download option. |
| 2025/04/23 | 1.0.4   | Christian Gamble | added daily live feed logs. |
| 2025/04/23 | 1.0.5   | Christian Gamble | changed gitlink to team 34 on side bar. |
| 2025/04/23 | 1.0.6   | Christian Gamble | added new requirements in text file. |
| 2025/04/23 | 1.0.7   | Christian Gamble | updated README.md for data fetching. |
| 2025/04/23 | 1.0.8   | Christian Gamble | added data related to topics for today using fetch_store.py in data folder. |
| 2025/04/23 | 1.0.9   | Jason Gonzales | Updated requirements.txt by adding schedule dependency. |
| 2025/04/23 | 1.1.0   | Jason Gonzales | Fixed hidden Send Data button on pre-login status. |
| 2025/04/23 | 1.1.1   | Felix Schafer | fixed lsu data collect not collecting some additonal notes. |
| 2025/04/23 | 1.1.2   | Baron Davis | added secret key for login features b/c our login info use to be hardcoded in our test.py. |
| 2025/04/23 | 1.1.3   | Baron Davis | added new demo verison number to the live test.py so that website verison is up to date with our verison number of chef-master-v2. |
| 2025/04/28 | 1.1.4   | Baron Davis | added correct format template to README.md |
| 2025/05/01 | 1.1.5   | Felix Schafer | Added EE and IE LSU data. |
| 2025/05/01 | 1.2.5   | Felix Schafer | added API collection of course and job data. |
| 2025/05/01 | 1.2.6   | Felix Schafer | refactored lsu data collection to avoid collecting and storing unneeded repeat data. |
| 2025/05/01 | 1.2.7   | Jason Gonzales | Fixed logo size. |
| 2025/05/01 | 1.2.8   | Baron Davis | updated ci.yml pipeline to ensure code quality and app functionality before merging into dev. |
| 2025/05/01 | 1.2.9   | Baron Davis | Fix Sendgrid bug because cant send emails of the data to @lsu.edu emails all other emails work. |
| 2025/05/01 | 1.3.0   | Jason Gonzales | Added Blank Page to see all files in database. |
| 2025/05/01 | 1.3.1   | Jason Gonzales | Change side bar feature on pre login page to not include software based links, instead navigation link. |
| 2025/05/01 | 1.3.2   | Felix Schafer | Added cybersecurity to majors. |
| 2025/05/01 | 1.3.3   | Felix Schafer | Fixed page styling. |
| 2025/05/01 | 1.3.4   | Felix Schafer | Changed graph axes to show different data |
| 2025/05/04 | 1.3.5   | Baron Davis | Add Search Data, Visualize Data, Share data, to the sidebar navigate to dropdown menu. |
| 2025/05/04 | 1.3.6   | Baron Davis | add back the edit data feature on login status page. |
| 2025/05/06 | 1.3.7   | Baron Davis | branched off of dev 1.3.6 v branch to create this current master (default) for fianl main branch and also cleaned scripts to follow Coding Standards.  |
| 2025/05/06 | 1.3.8   | Baron Davis | added Sendgrid api key hardcoded in .env so that you can send emails of data if cloned locally or if you are on streamlit app and add .env to .gitignore . |
| 2025/05/06 | 1.3.9   | Baron Davis | Change blank page name to 'Data Page'. |
| 2025/05/06 | 1.4.0   | Felix Schafer | Added 'Download Data' Page |
| 2025/05/06 | 1.4.1   | Jason Gonzales | Renamed test.py to app.py and changed README file accordingly. |
| 2025/05/06 | 1.4.2   | Felix Schafer | Added type hinting to test functions. |
| 2025/05/06 | 1.4.3   | Jason Gonzales | Refactor app.py into five modular scripts in src/scripts. |
| 2025/05/06 | 1.4.4   | Felix Schafer | Added JSON and Excel downloads to download page. |