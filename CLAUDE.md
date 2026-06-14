# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI backend for a patient registration system. Single-file API (`main.py`) backed by AWS DynamoDB. Serves as the backend for an Angular frontend application.

## Commands

### Run locally
```bash
python main.py
```
Server starts on `0.0.0.0:8000`.

### Run with Docker
```bash
docker-compose up --build
```
Exposes port 3000 (maps to internal 8000).

### Install dependencies
```bash
pip install -r requirements.txt
```

## Architecture

- **main.py** — entire API in one file. FastAPI app with CORS open to all origins.
- **DynamoDB table**: `patient-registration-data` with `patientId` as the partition key.
- **No ORM or models** — all endpoints accept/return raw dicts. `convert_floats_to_decimal` handles Python float → DynamoDB Decimal conversion.

### API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/patients` | Create patient (requires `patientId` in body) |
| GET | `/patients` | List patients (single-page scan) |
| GET | `/patients/{patient_id}` | Query by patientId |
| PUT | `/patients/{patient_id}` | Full replace (preserves original timestamp) |
| DELETE | `/delete/{patient_id}` | Delete by patientId |
| GET | `/all-items` | Paginated full table scan |
| POST | `/followups` | Save followup record |
| GET | `/followups` | List followups (scans same table) |

### Key Details

- PUT updates use `put_item` (full replace) instead of `update_expression` to avoid DynamoDB expression size limits on large patient records.
- The `.env` file contains AWS config but `main.py` currently hardcodes region and table name directly (the env-based approach is commented out).
- All data (patients and followups) lives in the same DynamoDB table.
