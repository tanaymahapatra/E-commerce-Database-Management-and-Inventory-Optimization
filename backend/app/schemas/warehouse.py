from pydantic import BaseModel, ConfigDict


class WarehouseResponse(BaseModel):
    warehouse_id: int
    warehouse_location: str

    # Illustrative Swagger example; not actual database data.
    model_config = ConfigDict(json_schema_extra={
        "example": {"warehouse_id": 1, "warehouse_location": "Guwahati"}
    })


class WarehouseListResponse(BaseModel):
    page: int
    limit: int
    total_warehouses: int
    warehouses: list[WarehouseResponse]

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "page": 1,
            "limit": 10,
            "total_warehouses": 50,
            "warehouses": [{"warehouse_id": 1, "warehouse_location": "Guwahati"}]
        }
    })


class WarehouseLocationsResponse(BaseModel):
    locations: list[str]

    model_config = ConfigDict(json_schema_extra={
        "example": {"locations": ["Guwahati", "Mumbai"]}
    })
