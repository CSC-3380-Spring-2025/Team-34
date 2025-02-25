# Airflow Setup with PostgreSQL - Local & Linux Guide

## **1. Overview**
This document details the steps to configure and run Apache Airflow locally using Docker and PostgreSQL. It includes required improvements, setup configurations, and Linux command execution.

---

## **2. Requirements & Improvements Made**
### **2.1 System Requirements**
- Docker & Docker Compose installed
- PostgreSQL 17
- Python 3.x (if running outside Docker)
- Airflow 2.7.2

### **2.2 Improvements Made**
- Migrated from SQLite to PostgreSQL for production readiness
- Ensured DAG scripts can access external scripts inside Docker
- Corrected DAG scheduling and execution paths
- Set proper volume mounts in `docker-compose.yml`
- Enabled Airflow Scheduler to run reliably
- Updated workflow documentation to align with LSU CS DS Project 34

---

## **3. Project Team Roles (LSU CS DS: 34)**
### **3.1 Members**
- **Project Manager:** Felix ([fschaf2])
- **Git Master:** Baron ([bdogdavis])
- **Design Lead:** Jason ([JasonGonzo123])
- **Communications Lead:** TBD ([GitHub Name])
- **Quality Assurance Tester:** TBD ([GitHub Name])

---

## **4. Setting Up PostgreSQL & Airflow in Docker**

### **4.1 Docker Compose Configuration (`docker-compose.yml`)**
Ensure the following configurations are set:
```yaml
services:
  postgres:
    image: postgres:17
    restart: always
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U airflow"]
      interval: 10s
      retries: 5
      timeout: 5s
    volumes:
      - postgres_data:/var/lib/postgresql/data

  airflow-init:
    image: apache/airflow:2.7.2
    restart: on-failure
    entrypoint: /bin/bash
    command: ["-c", "airflow db migrate && airflow db upgrade"]
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ./plugins:/opt/airflow/plugins
      - ./scripts/research:/opt/research

  airflow-webserver:
    image: apache/airflow:2.7.2
    restart: always
    depends_on:
      airflow-init:
        condition: service_completed_successfully
    ports:
      - "8080:8080"
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__CORE__FERNET_KEY=your_secret_key
      - AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=False
      - AIRFLOW__WEBSERVER__RBAC=True
      - AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow
    command: airflow webserver
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ./plugins:/opt/airflow/plugins
      - ./scripts/research:/opt/research

  airflow-scheduler:
    image: apache/airflow:2.7.2
    restart: always
    depends_on:
      airflow-webserver:
        condition: service_healthy
    command: airflow scheduler
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ./plugins:/opt/airflow/plugins
      - ./scripts/research:/opt/research

volumes:
  postgres_data:
```

---

## **5. Running Airflow & PostgreSQL on Linux**

### **5.1 Initialize and Start Containers**
```bash
docker-compose down --remove-orphans  # Stop existing containers
docker-compose up -d  # Start PostgreSQL and Airflow services
```

### **5.2 Verify Running Containers**
```bash
docker ps  # Check if airflow-webserver, scheduler, and PostgreSQL are running
```

### **5.3 Manually Trigger DAG Execution**
```bash
docker-compose exec airflow-webserver airflow dags trigger fetch_research_dag
```

### **5.4 Check DAG Logs for Execution Details**
```bash
docker-compose logs airflow-scheduler --tail=50
```

### **5.5 Verify PostgreSQL Connection**
```bash
docker-compose exec postgres psql -U airflow -d airflow -c "\dt"
```

---

## **6. Ensuring DAG Executes External Python Script**

### **6.1 Update DAG to Reference Correct Path**
Modify `fetch_research_dag.py`:
```python
fetch_research_task = BashOperator(
    task_id='fetch_research_task',
    bash_command='cd /opt/research && python3 run_research_fetching.py',
    dag=dag
)
```

### **6.2 Test Script Execution Inside Docker**
```bash
docker-compose exec airflow-webserver bash -c "cd /opt/research && python3 run_research_fetching.py"
```

---

## **7. Troubleshooting Steps**

### **7.1 If Airflow Scheduler Is Not Running**
```bash
docker-compose restart airflow-scheduler
```

### **7.2 If DAG Execution Fails**
1. Check if the script exists inside Docker:
   ```bash
   docker-compose exec airflow-webserver ls /opt/research/run_research_fetching.py
   ```
2. Verify DAG logs:
   ```bash
   docker-compose logs airflow-scheduler --tail=50
   ```

### **7.3 If Airflow UI Login Fails**
Create a new user:
```bash
docker-compose exec airflow-webserver airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password airflow
```

### **7.4 Restarting Everything if Issues Persist**
```bash
docker-compose down --remove-orphans
docker-compose up -d
```

---

## **8. Summary of Improvements & Fixes**
✅ PostgreSQL setup replacing SQLite for persistence.
✅ Ensured DAG correctly references `run_research_fetching.py`.
✅ Set correct file paths and working directory for Airflow execution.
✅ Mounted `scripts/research` to ensure all dependencies load.
✅ Added troubleshooting steps for common issues.
✅ Included LSU CS DS Project 34 documentation roles and structure.

Now, **Airflow should run properly with PostgreSQL**, and DAGs should execute external scripts seamlessly! 🚀

