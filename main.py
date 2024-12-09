from fastapi import FastAPI
from routers.products import router as products_router
from routers.prices import router as prices_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products_router)
app.include_router(prices_router)


@app.get("/")
def read_root():
    return "Server is running."
