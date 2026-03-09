# MeshMind v2 — Auth Model

## Overview

- **JWT-based** auth for on-prem internal deployment
- **Bearer token** in `Authorization` header: `Authorization: Bearer <token>`
- **Argon2** password hashing

## Login Flow

1. `POST /api/auth/login` with `{ "username": "admin", "password": "admin" }`
2. Response: `{ "token": "...", "user": { "id", "username", ... } }`
3. Use `Authorization: Bearer <token>` for subsequent requests

## Protected Endpoints

All routes except `/health`, `/ready`, `/api/health`, `/api/ready`, `/api/auth/login` require authentication.

## Dev Admin Seed

Set `MESHMIND_SEED_DEV_ADMIN=true` to create admin user (username: `admin`, password: `admin`) on startup.

**Do not use in production.**

## Environment

| Variable | Description |
|----------|-------------|
| `JWT_SECRET` | Secret for signing JWTs (required in production) |
| `MESHMIND_SEED_DEV_ADMIN` | `true` to seed dev admin |
