# AI-Powered Transaction Processing Pipeline

This project is a Backend API that processes a CSV file of transactions, uses an LLM to categorize and analyze them, and generates a structured summary report.

**Author:** [defaultname-ayan](https://deafultayan.dev)
**Technical Review Video:** [Watch on YouTube](https://youtu.be/Gjlm1WWrAHg)


**youtube link** : https://youtu.be/Gjlm1WWrAHg
**portfolio** : https://deafultayan.dev

## Architecture & Tech Stack

*   **API Framework:** FastAPI
*   **Database:** PostgreSQL (with async SQLAlchemy)
*   **Job Queue:** Celery + Redis
*   **LLM:** Google Gemini 1.5 Flash
*   **Containerization:** Docker & Docker Compose

## Requirements

*   Docker and Docker Compose installed.
*   A Gemini API Key. (You can get one for free from Google AI Studio).

## Setup Instructions

1. Clone the repository.
2. The project uses a management script (`start.sh`) for setup and running. Make sure it is executable:
```bash
chmod +x start.sh
```

### 1. Setup Environment
Run the setup flag. This will copy the `env.example` file and interactively prompt you for your `GEMINI_API_KEY`, Postgres User, and Postgres Password.
```bash
./start.sh --setup
```

### 2. Start the Application
Once the `.env` is configured, start the containers in detached mode:
```bash
./start.sh --start
```
The API will be available at `http://localhost:8000`. You can view live logs by running `docker compose logs -f`.

### 3. Stop the Application
To spin down the containers and clean up the network:
```bash
./start.sh --stop
```

## Running Tests

To run the unit tests for the core business logic (Data Cleaning, Anomaly Detection, and LLM formatting):

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest tests/
```

## Example cURL Requests

### 1. Upload a CSV file
```bash
curl -X POST "http://localhost:8000/jobs/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@transactions.csv"
```
*Expected Response:*
```json
{
  "job_id": "bf04a96f-73c7-4d2e-927a-80197de1fd0f",
  "status": "pending"
}
```

### 2. Get Job Status
```bash
curl -X GET "http://localhost:8000/jobs/bf04a96f-73c7-4d2e-927a-80197de1fd0f/status"
```
*Expected Response:*
```json
{
  "job_id": "bf04a96f-73c7-4d2e-927a-80197de1fd0f",
  "status": "completed",
  "summary": {
    "total_spend_inr": 120500.0,
    "total_spend_usd": 450.0,
    "anomaly_count": 2,
    "risk_level": "low"
  },
  "error_message": null
}
```

### 3. Get Job Results
```bash
curl -X GET "http://localhost:8000/jobs/bf04a96f-73c7-4d2e-927a-80197de1fd0f/results"
```
*Expected Response:*
```json
{
  "job_id": "bf04a96f-73c7-4d2e-927a-80197de1fd0f",
  "status": "completed",
  "cleaned_transactions": [...],
  "flagged_anomalies": [...],
  "category_breakdown": {
    "Food": 1500.0,
    "Shopping": 300.0
  },
  "narrative_summary": {
    "total_spend_inr": 120500.0,
    "total_spend_usd": 450.0,
    "top_merchants": [
      {"merchant": "Amazon", "count": 10}
    ],
    "anomaly_count": 2,
    "narrative": "Processed 90 transactions. Found 2 anomalies.",
    "risk_level": "low"
  }
}
```

### 4. List All Jobs
```bash
curl -X GET "http://localhost:8000/jobs?status=completed"
```
*Expected Response:*
```json
[
  {
    "id": "bf04a96f-73c7-4d2e-927a-80197de1fd0f",
    "filename": "transactions.csv",
    "status": "completed",
    "row_count_raw": 90,
    "row_count_clean": 88,
    "created_at": "2024-05-15T12:00:00Z"
  }
]
```
