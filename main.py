from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "Backend is healthy!"}

@app.get("/")
def root():
    return {"message": "Welcome to the FastAPI app"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
