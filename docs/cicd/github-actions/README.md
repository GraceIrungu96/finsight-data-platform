# GitHub Actions CI/CD Workflow Architecture

## Overview
This document outlines the automated testing and deployment pipeline for the FinSight Data Platform. The workflow ensures that every code change undergoes automated linting, containerized database integration testing, and strict data quality contract validation before merging into the main branch.

## Pipeline Execution Flow
1. **Trigger:** Activated on every `push` or `pull_request` targeting the `main` branch.
2. **Service Container:** Spins up an ephemeral `postgres:15` container instance configured with environment variables mirroring production settings on port `5433`.
3. **Environment Setup:** Provisions a clean Python 3.12 runtime environment and caches pip dependencies for performance.
4. **Code Quality Gate (Ruff):** Executes static analysis and linting across the `src/` codebase.
5. **Integration & Data Quality Test:** 
   * Generates sample financial transactions (`generate_mock_data.py`).
   * Executes the `postgres_reader` module to test live connection pooling, Pydantic schema validation, and idempotent database insertion against PostgreSQL.
