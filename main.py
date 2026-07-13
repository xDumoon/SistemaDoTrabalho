import os
from dotenv import load_dotenv
load_dotenv()
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "app.app:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("RELOAD", "false").lower() == "true",
    )
