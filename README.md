# LSU Datastore Dashboard : Team-34

## Members
- **Project Manager:** Felix Schafer (bdogdavis)  
- **Communications Lead:** Christian Gamble (cgamble)  
- **Git Master:** Baron K. Davis (bdogdavis)  
- **Design Lead:** _Not specified_  
- **Quality Assurance Tester:** _Not specified_  

## About Our Software
A Streamlit-based dashboard for uploading, previewing, and managing CSV datasets (courses, research, live logs) in a unified SQLite datastore.

## Platforms Tested on
- MacOS  
- Linux (Ubuntu)  
- Windows  

## Important Links
- **Kanban Board:** https://github.com/CSC-3380-Spring-2025/Team-34/projects  
- **Designs:** _N/A_  
- **Styles Guide(s):** _N/A_  

## How to Run Dev and Test Environment

### Dependencies
- `streamlit~=1.43.0`  
- `plotly==5.20.0`  
- `python-dotenv==1.0.1`  
- `xlsxwriter==3.2.0`  
- `sendgrid==6.11.0`  
- `pandas==2.2.3`  
- `requests==2.32.3`  
- `bs4==0.0.2`  
- `psutil==6.1.0`  
- `pyarrow==17.0.0`  
- `schedule==1.2.2`  

### Downloading Dependencies

pip install -r requirements.txt


### Commands
Start the app locally:

streamlit run src/test.py \
  --server.enableCORS false \
  --server.enableXsrfProtection false

Run tests:
pytest tests/


### Update datastore.db and Push to chef-master-v2 Step-by-Step Instructions
1. Navigate to the folder where fetch_store.py is located:
cd Team-34/src/data
2. Install the required package:
pip install schedule
3. Run the data-fetching script to update datastore.db:
python fetch_store.py
4. Commit & force-push the updated database file:
git add ../datastore/datastore.db
git commit -m "Update datastore.db with new data"
git push origin chef-master-v2 --force

⚠️ Warning: Force pushing will overwrite remote history; use with caution.
