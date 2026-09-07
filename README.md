# E-commerce Database Management and Inventory Optimization

DBMS Course Project

**Team:** Himanshu Mandal • Subhadeep Sarkar • Swarnava Kundu • Tanay Mahapatra

## Overview

Retail and e-commerce businesses struggle to keep inventory at the right level — understocking causes lost sales, overstocking wastes money on storage and risks obsolescence. Most existing systems rely on flat averages that break down when sales fluctuate or deliveries are delayed.

This project connects a **MySQL** relational database with **Python** statistical forecasting to automatically calculate safe inventory levels and write recommendations back to the database.

## Objectives

- Build a normalized MySQL schema for orders, customers, products, warehouses, sales, and inventory.
- Categorize products as **fast-moving** (high daily sales) or **slow-moving** (irregular, many zero-sales days).
- Forecast future demand per product/warehouse using time-series methods.
- Calculate safety stock from delivery delays and forecast uncertainty.
- Automate writeback of order quantities and status flags to MySQL.

**Scope:** DB design, SQL aggregation, time-series forecasting, safety-stock calculation, automated SQL writeback.

## Users and Major Operations

**Users:** Warehouse manager (location-wise), Head manager (country-wise), Chief Sales Officer, Business analyst (sales trends), Procurement team (reorder planning).

**Pipeline:**
Data ingestion of raw sales → SQL aggregation by product/warehouse/date → Python demand forecasting → safety-stock & reorder-threshold calculation → writeback of quantities and status flags (`OK`, `REORDER_NOW`, `CRITICAL`).

## Data

**Primary source:** [Kaggle — Global E-Commerce Dataset (+1M Records, 2024–2026)](https://www.kaggle.com/datasets/akrambelha/global-e-commerce-dataset-1m-records-20242026)

The flat transactional dataset is normalized into the following entities:

| Entity | Key Fields |
|---|---|
| **Customer** | customer_id, customer_name, gender, age, customer_segment, country, city, customer_loyalty_score, total_orders_by_customer, account_creation_date |
| **Product** | product_id, product_name, category, sub_category, brand, product_rating_avg, product_reviews_count, unit_price_usd |
| **Warehouse** | warehouse_id (derived), warehouse_location |
| **Inventory** | inventory_id, product_id, warehouse_id, stock_quantity |
| **Order** | order_id, order_date, is_weekend, order_status, payment_method, payment_status, installment_plan, device_type, customer_id |
| **Order_Item** | order_id, product_id, warehouse_id, quantity, discount_percent, total_price_usd, cost_usd, profit_usd, tax_usd |
| **Shipment** | order_id, shipping_method, shipping_cost_usd, delivery_days, shipping_country, delivery_status |
| **Forecast/Recommendation** | product, warehouse, predicted_demand, safety_stock, reorder_qty, status *(system-generated)* |

### ER Diagram (preliminary)

```
Customer --places--> Order --has--> Shipment
Order --has--> Order_Item --refers--> Product
Order_Item --fulfils--> Warehouse --holds--> Inventory --stocked--> Product
Inventory --gen.--> Reorder_Rec.
```
*(Not finalized )*

## Business Rules and Integrity Constraints

- Order must reference an existing Customer (FK).
- Order_Item must reference valid Order, Product, and Warehouse.
- Price/cost fields must be > 0 (CHECK).
- Stock on hand must always be ≥ 0.
- Order_Item quantity must be > 0.
- `(product_id, warehouse_id)` must be unique in Inventory.
- Product deletion is restricted if referenced by an Order_Item.
- `order_date` cannot be a future date.

