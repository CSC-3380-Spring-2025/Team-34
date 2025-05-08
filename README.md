# LSU Datastore Dashboard : Team-34

## Members
- **Project Manager:** Felix Schafer (fschaf2)  
- **Communications Lead:** Christian Gamble (Christianfft)  
- **Git Master:** Baron Davis (bdogdavis)  
- **Design Lead:** Jason Gonzales (JasonGonzo123)  
- **Quality Assurance Tester:** _Not specified_  

## About Our Software
The LSU Datastore Dashboard is a Streamlit-based web application for managing, visualizing, and sharing academic and professional datasets at LSU. It allows users to upload and preview CSV datasets (e.g., jobs, courses, research papers, LSU courses), visualize data with interactive plots, share datasets via email using SendGrid, and schedule daily data fetching. Key features include:

- User authentication with SQLite-backed credentials.
- Data upload, preview, editing, and deletion.
- Search across all datasets.
- Data visualization using Plotly scatter plots.
- Email sharing of datasets.
- Live logging and system performance metrics (CPU/memory usage).
- Scheduled data fetching for jobs, courses, research, and LSU data.

## Platforms Tested on
- MacOS (Python 3.11)
- Linux (Ubuntu, Python 3.10 via CI/CD, Python 3.11 in Codespaces)
- Windows (Python 3.11)
- Streamlit Cloud (Python 3.11)

## Important Links
- **Kanban Board:** [https://github.com/CSC-3380-Spring-2025/Team-34/projects](https://github.com/orgs/CSC-3380-Spring-2025/projects/5)  
- **Designs/Website Here:** (https://team34-lsu-csc-dashboard-v2.streamlit.app/)
- **Styles Guide(s):**
  - [PEP 8](https://peps.python.org/pep-0008/) for Python style.
  - [PEP 257](https://peps.python.org/pep-0257/) for docstrings.
  - [pylint](https://pylint.pycqa.org/en/latest/) for linting (enforced via CI/CD pipeline).

## How to Run Dev and Test Environment

### Prerequisites
- **Python**: Version 3.10 (for CI/CD) or 3.11 (for local dev and Streamlit Cloud). Download from [python.org](https://www.python.org/downloads/).
- **IDE**: Visual Studio Code (free/community edition) recommended.
  - Required VS Code Extensions:
    - Python (`ms-python.python`)
    - Pylance (`ms-python.vscode-pylance`)
- **Streamlit Cloud**: Free tier account for deployment (optional).

### Dependencies
- `streamlit==1.31.0`  
- `plotly==5.22.0`  
- `python-dotenv==1.0.0`  
- `xlsxwriter==3.2.0`  
- `sendgrid==6.10.0`  
- `pandas==2.2.2`  
- `requests==2.31.0`  
- `psutil==5.9.5`  
- `pyarrow==14.0.1`  
- `schedule==1.2.0`

### Downloading Dependencies
1. Clone the repository:
   ```bash
   git clone https://github.com/CSC-3380-Spring-2025/Team-34.git
   cd Team-34
2. Ensure Python 3.10 or 3.11 is installed:
   python3 --version
3. Install dependencies from requirements.txt (located in the project root):
   pip install -r requirements.txt
4. (Optional) Set up PYTHONPATH for imports:
   export PYTHONPATH=$PWD:$PYTHONPATH
   echo $PYTHONPATH
### Commands
1. Start the app locally from the project root:
  streamlit run src/app.py \
  --server.enableCORS false \
  --server.enableXsrfProtection false
2. Run tests (ensure tests/ directory exists with test files):
   pytest tests/
### Update datastore.db and Push to master Step-by-Step Instructions
1. Navigate to the folder where fetch_store.py is located:
   cd Team-34/src/data
2. Ensure the schedule package is installed:
  pip install schedule
3. Run the data-fetching script to update datastore.db:
   python fetch_store.py
     - This script fetches job listings, courses, research papers, and LSU course data, storing them in datastore.db using save_csv_to_database.
4. Commit and force-push the updated database file:
     git add ../datastore/datastore.db
     git commit -m "Update datastore.db with new data"
     git push origin main --force

⚠️ Warning: Force pushing will overwrite remote history; use with caution. Consider --force-with-lease to avoid overwriting others' changes:

git push origin master --force-with-lease

### Streamlit Cloud Deployment (Optional)
1. Fork or push the repository to your GitHub account.
2. Sign up for a free Streamlit Cloud account at streamlit.io.
3. Create a new app, linking to your repository’s master branch.
4. Set the app entry point to src/app.py.
5. Add secrets in Streamlit Cloud under “Secrets”:
     [general]
     SENDGRID_API_KEY = "your-sendgrid-api-key"
     USERNAME = "admin"
     PASSWORD = "NewSecurePassword123"

6.  Deploy the app and monitor logs for errors.
