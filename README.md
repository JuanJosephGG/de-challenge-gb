# 🚀 Data Engineering Challenge - Ingestion & Analytics Platform

A robust, stateless, and cloud-native REST API designed for the ingestion, validation, backup, and analysis of corporate Human Resources data.

## 🏗️ Project Architecture

This project implements **Clean Architecture** and **Shift-Left Data Validation** principles, ensuring that corrupted or malformed data is rejected and properly logged before it ever reaches the main database.

The platform utilizes a hybrid Transactional/Analytical approach:
* **Bronze Layer / Data Lake (Amazon S3):** Stores raw historical CSV files, manages the Dead Letter Queue (DLQ) logs, and persists binary backups (AVRO).
* **Silver / Gold Layer (PostgreSQL RDS):** Stores clean, validated data. Analytical metrics are delegated directly to the database engine via SQL Views to maximize performance and reduce memory overhead.

## 🛠️ Tech Stack

* **Language:** Python 3.13
* **API Framework:** FastAPI (Uvicorn)
* **Package Manager:** `uv` (Astral)
* **Database:** PostgreSQL (Amazon RDS)
* **ORM & Querying:** SQLAlchemy + Pydantic
* **Cloud Storage:** Amazon S3 (Boto3)
* **Data Formats:** JSON, CSV (Pandas), AVRO (FastAvro)
* **Infrastructure:** Docker (Non-root user, multi-stage optimized cache)

## ✨ Core Features

1. **Transactional Ingestion (Batch):** REST endpoints designed to insert anywhere from 1 to 1000 records per request efficiently.
2. **Historical Migration:** Uploads raw CSV files to S3 and performs massive batch processing into PostgreSQL.
3. **Dead Letter Queue (DLQ):** Records that fail structural (Pydantic) or relational (Foreign Keys) validation do not crash the application. Instead, they are routed to S3 as `.jsonl` files for future auditing.
4. **Disaster Recovery (Backup/Restore):** Administrative endpoints that serialize entire tables into AVRO format directly in-memory and stream them to S3. Restore operations utilize an `UPSERT` strategy to protect referential integrity.
5. **Analytical Metrics (OLAP):** Read-only endpoints that consume materialized views in the database to answer business questions instantly without overloading Python's memory.

---

## ⚙️ Prerequisites

* [Docker](https://www.docker.com/) installed on your machine.
* AWS Credentials (Access Key & Secret Key) with write permissions to an S3 bucket.
* A PostgreSQL database instance (Local or AWS RDS).

## 🚀 Setup & Local Deployment

### 1. Clone the repository
```bash
git clone [https://github.com/JuanJosephGG/de-challenge-gb.git](https://github.com/JuanJosephGG/de-challenge-gb.git)
cd de-challenge-gb