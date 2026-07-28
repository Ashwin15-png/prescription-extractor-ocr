# 🚀 Enterprise Production Deployment Guide — Prescription Extractor SaaS

This document provides step-by-step instructions for deploying **Prescription Extractor (PrescriptionX)** to production using **Render (Backend)**, **Vercel (Frontend)**, and **Neon PostgreSQL (Cloud Database)**.

---

## 📋 Infrastructure Architecture Overview

* **Backend Service**: Render / Railway / Docker Container (FastAPI + Gunicorn + Uvicorn)
* **Frontend Web Hosting**: Vercel / Netlify / FastAPI Static File Mount
* **Cloud Database**: Neon PostgreSQL (SSL Encrypted, Pooled Connections)
* **OCR Processing**: Tesseract 5.0 + OpenCV 4.x (Linux Binary Package)

---

## 🗄️ 1. Neon PostgreSQL Database Configuration

1. Create a PostgreSQL project on [Neon.tech](https://neon.tech).
2. Retrieve your Connection String from the Neon Dashboard:
   ```text
   postgresql://<user>:<password>@<ep-endpoint>.us-east-2.aws.neon.tech/<dbname>?sslmode=require
   ```
3. Enable Connection Pooling in Neon if high concurrency is expected.
4. Set the `DATABASE_URL` environment variable in your backend environment settings.

---

## ⚙️ 2. Backend Deployment (Render / Railway)

### Option A: Render Deployment (Recommended)
1. Log into [Render Dashboard](https://dashboard.render.com/) and click **New + > Web Service**.
2. Connect your GitHub repository: `ashwinkumar/prescription-extractor`.
3. Configure the service settings:
   * **Name**: `prescription-extractor-api`
   * **Environment**: `Python 3`
   * **Region**: Oregon (US West) or closest region
   * **Branch**: `main`
   * **Build Command**:
     ```bash
     apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-eng libgl1-mesa-glx && pip install -r backend/requirements.txt
     ```
   * **Start Command**:
     ```bash
     gunicorn -c gunicorn.conf.py backend.app.main:app
     ```
4. Add **Environment Variables**:
   * `ENV` = `production`
   * `DEBUG` = `False`
   * `DATABASE_URL` = `postgresql://<user>:<password>@<neon-host>/neondb?sslmode=require`
   * `TESSERACT_CMD` = `/usr/bin/tesseract`
   * `MAX_UPLOAD_SIZE_MB` = `10`
   * `CORS_ORIGINS` = `https://prescription-extractor.vercel.app,http://localhost:8000`

### Option B: Docker Container Deployment (Railway / Fly.io / AWS ECS)
1. Deploy using the provided production `Dockerfile`:
   ```bash
   docker build -t prescription-extractor:latest .
   docker run -d -p 8000:8000 --env-file .env prescription-extractor:latest
   ```

---

## 🌐 3. Frontend Deployment (Vercel / Netlify)

### Vercel Deployment
1. Log into [Vercel](https://vercel.com/) and click **Add New > Project**.
2. Import the GitHub repository `ashwinkumar/prescription-extractor`.
3. Configure project settings:
   * **Framework Preset**: `Other`
   * **Root Directory**: `./`
   * **Output Directory**: `frontend/web`
4. Add Environment Variable:
   * `API_BASE_URL` = `https://prescription-extractor-api.onrender.com`
5. Click **Deploy**.

---

## 🔒 4. Environment Variables Reference

| Variable Name | Environment | Example Value | Description |
| :--- | :--- | :--- | :--- |
| `ENV` | All | `production` / `development` | Runtime environment mode |
| `DEBUG` | All | `False` | Enables detailed tracebacks (Set `False` in prod) |
| `DATABASE_URL` | Production | `postgresql://...neon.tech/neondb?sslmode=require` | PostgreSQL Database URI |
| `TESSERACT_CMD` | Linux/Prod | `/usr/bin/tesseract` | Path to Tesseract binary executable |
| `MAX_UPLOAD_SIZE_MB` | All | `10` | Maximum file upload size limit |
| `CORS_ORIGINS` | Production | `https://your-frontend.vercel.app` | Allowed CORS origins list |

---

## 🩺 5. Post-Deployment Verification & Health Checks

Verify your deployment using the following automated endpoints:

1. **System Health Check**:
   ```bash
   curl -i https://prescription-extractor-api.onrender.com/health
   ```
   * Expected output: `{"status": "healthy", "environment": "production", "database": "healthy", "version": "2.0.0"}`

2. **OpenAPI Interactive Documentation**:
   * Visit `https://prescription-extractor-api.onrender.com/docs`

3. **Frontend Application Verification**:
   * Visit `https://prescription-extractor.vercel.app`
   * Upload sample prescription image
   * Confirm OCR extraction fields populate
   * Click **Save** and verify record appears in Dashboard

---

## ↩️ 6. Rollback Procedures

If a critical issue occurs after deployment:

1. **Render Rollback**:
   * Go to **Render Dashboard > Events**.
   * Find the last successful deploy event.
   * Click **Rollback to this deploy**.

2. **Vercel Rollback**:
   * Go to **Vercel Dashboard > Deployments**.
   * Locate the previous stable build.
   * Click **... > Instant Rollback**.

3. **Database Recovery**:
   * Neon supports Instant Point-In-Time Restore (PITR) & Branching.
   * To revert database state, navigate to **Neon Dashboard > Branches** and restore from snapshot.

---

## 🔍 7. Troubleshooting Guide

| Symptom | Cause | Resolution |
| :--- | :--- | :--- |
| `500 Internal Error` on Upload | Tesseract binary missing on host | Ensure `apt-get install -y tesseract-ocr` is executed during build. |
| `CORS Error` on Frontend | Mismatched API domain origin | Add your Vercel frontend URL to `CORS_ORIGINS` in backend environment variables. |
| `sqlalchemy.exc.OperationalError` | Incorrect Neon SSL Mode | Ensure `?sslmode=require` is appended to `DATABASE_URL`. |
| Upload size error | File size exceeds 10MB | Check `MAX_UPLOAD_SIZE_MB` configuration or compress image. |
