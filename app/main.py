from fastapi import FastAPI

app = FastAPI(
    title="Viridi SFA API",
    version="0.1.0",
)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Welcome to Viridi SFA API! Database and migrations are ready."
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}