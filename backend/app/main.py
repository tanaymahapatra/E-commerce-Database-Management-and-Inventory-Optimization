from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .database import get_db

# Create FastAPI application
app = FastAPI(title="E-Commerce Inventory Optimization API")
from .routers import products, warehouse, inventory, orders, analytics

app.include_router(products.router)
app.include_router(warehouse.router)
app.include_router(inventory.router)
app.include_router(orders.router)
app.include_router(analytics.router)


@app.get("/")
def home():
    return {"message": "E-Commerce Inventory API is running"}


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        database = db.execute(text("SELECT DATABASE()")).scalar_one()

        return {"status": "connected", "database": database}

    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Database connection failed")
