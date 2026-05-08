import uvicorn
import os

if __name__ == "__main__":
    # Ensure uploads directory exists
    os.makedirs("../uploads", exist_ok=True)
    os.makedirs("../data", exist_ok=True)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
