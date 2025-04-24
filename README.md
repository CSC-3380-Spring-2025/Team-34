Update datastore.db and Push to chef-master-v2 Step-by-Step Instructions Navigate to the folder where fetch_store.py is located: cd Team-34/src/data
Install the required Python package: pip install schedule
Run your data fetching script to update datastore.db: python fetch_store.py
Commit and force push the updated database file to chef-master-v2: git add ../datastore/datastore.db git commit -m "Update datastore.db with new data" git push origin chef-master-v2 --force
⚠️ Warning: Force pushing will overwrite remote history; use with caution
