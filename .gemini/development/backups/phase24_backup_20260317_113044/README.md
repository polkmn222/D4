# AI Ready CRM - Running Instructions

## Development Server
To run the CRM web application locally, use the following command from the project root directory:

```bash
uvicorn app.main:app --reload
```

- **URL**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **FastAPI Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Environment Setup
Ensure you have installed the dependencies and configured the `.env` file:

1. `pip install -r requirements.txt`
2. Check `.env` for `CELEBRACE_API_KEY` and `GROQ_API_KEY`.

## Database
The application uses SQLite (`crm.db`). Tables are automatically initialized on startup.
