# Gridle residential clients

This repository now includes two web clients for the Gridle residential public API.

## 1) React UI + Python API server (latest values)

### What it does

- Python FastAPI server exposes `/latest` on localhost.
- React UI fetches from `http://localhost:8000/latest`.
- Dashboard auto-refreshes every 60 seconds and shows latest measurement values.

### Run it

1. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables (recommended in a local `.env` file):

   ```bash
   cp env.example .env
   ```

   Then set `GRIDLE_API_KEY` in `.env`.

3. Start the Python API server:

   ```bash
   uvicorn api_server:app --host 127.0.0.1 --port 8000
   ```

4. In a new terminal, install frontend dependencies:

   ```bash
   npm --prefix frontend install
   ```

5. Start the React UI:

   ```bash
   npm --prefix frontend run dev -- --host 127.0.0.1 --port 5173
   ```

6. Open `http://127.0.0.1:5173`.

## 2) Streamlit client (time series explorer)

The original Streamlit app is still available in `app.py`.

Run it with:

```bash
streamlit run app.py
```

## Notes

- The API key is no longer stored in source code.
- Set `GRIDLE_API_KEY` in your environment (or local `.env`) before running the apps.
- Gridle API rate limit is 1 request per second with burst 2.
- Maximum supported range is 31 days.