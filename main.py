from fastapi import FastAPI
from routers.products import router as products_router


app = FastAPI()

app.include_router(products_router)


@app.get("/")
def read_root():
    return "Server is running."
