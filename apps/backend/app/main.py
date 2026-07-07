from fastapi import FastAPI

app = FastAPI(title="Security Monitoring Platform")

@app.get("/")
def health_check():
    return {"status": "ok", "mesage": "Backend is running"}