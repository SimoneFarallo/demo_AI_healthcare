from pss_ai.api import app

# Allows: python -m pss_ai.run_api
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
