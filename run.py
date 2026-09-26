"""Start the app: python run.py  (then open http://127.0.0.1:8000)"""

import logging

import uvicorn

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uvicorn.run("app.main:create_app", factory=True, host="127.0.0.1", port=8000)
