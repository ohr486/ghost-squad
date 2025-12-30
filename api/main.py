"""Ghost Squad API - Main application."""
from config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import inquiry

app = FastAPI(
    title="Ghost Squad API",
    description="AI-Driven Task Management Platform",
    version="0.1.0",
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(inquiry.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Ghost Squad API is running"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
