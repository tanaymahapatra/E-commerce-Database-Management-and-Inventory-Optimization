from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import Depends
from .security import require_admin
from .routers import auth
from .database import get_db
from contextlib import asynccontextmanager


# Create FastAPI application
@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()


app = FastAPI(title="E-Commerce Inventory Optimization API", lifespan=lifespan)

from .routers import (
    products,
    warehouse,
    inventory,
    orders,
    analytics,
    recommendations,
    stock_demand,
    scheduler,
)
from .services.scheduler_service import (
    start_scheduler,
    stop_scheduler,
)

# Authentication endpoints
app.include_router(auth.router)

# Warehouse-level permission checks inside recommendations.py
app.include_router(recommendations.router)

# Other APIs temporarily restricted to admin
app.include_router(products.router, dependencies=[Depends(require_admin)])

app.include_router(warehouse.router, dependencies=[Depends(require_admin)])

app.include_router(inventory.router, dependencies=[Depends(require_admin)])

app.include_router(orders.router, dependencies=[Depends(require_admin)])

app.include_router(analytics.router, dependencies=[Depends(require_admin)])
app.include_router(stock_demand.router)
app.include_router(scheduler.router, dependencies=[Depends(require_admin)])


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
