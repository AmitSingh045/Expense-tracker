# Guide: Deploying Django with Neon Postgres

This guide provides step-by-step instructions to deploy your **Expense Tracker** application to production using **Neon Postgres** for the database and **Render** (or any similar hosting provider) for the web server.

---

## Step 1: Create a Neon Postgres Database

1. Sign up/Log in at [Neon Console](https://console.neon.tech/).
2. Click **Create Project** (or use an existing one).
3. Name your project (e.g., `expense-tracker`) and select your database version (PostgreSQL 15 or 16 is recommended).
4. Click **Create Project**.
5. Once created, Neon will show your database connection string in the dashboard. It will look like this:
   ```
   postgresql://alex:AbCdEf123456@ep-cool-snowflake-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
6. **Copy this connection string**. This is your `DATABASE_URL` for production.

---

## Step 2: Prepare Host Environment Variables

When deploying your web service, you must configure the following environment variables in your hosting provider's dashboard (e.g., Render, Railway, or Heroku):

| Variable Name | Recommended Value | Purpose |
| :--- | :--- | :--- |
| `SECRET_KEY` | *Generates a random 50+ character string* | Kept private for cryptographic signing. |
| `DEBUG` | `False` | Disables verbose error pages in production. |
| `ALLOWED_HOSTS` | `your-app-name.onrender.com` | Prevents HTTP host header attacks. |
| `CSRF_TRUSTED_ORIGINS` | `https://your-app-name.onrender.com` | Allows secure POST/form requests over SSL. |
| `DATABASE_URL` | *Your copied Neon connection string* | Tells Django how to connect to Neon. |
| `DB_SSL_REQUIRE` | `True` | Enforces SSL for Postgres connections. |

---

## Step 3: Deploy to Render (Example)

Render is one of the easiest and most robust ways to deploy python applications. Since we have already created the [Procfile](file:///c:/Users/User/Documents/Expense_tracker_fixed/Expense%20tracker/Procfile) and [requirements.txt](file:///c:/Users/User/Documents/Expense_tracker_fixed/Expense%20tracker/requirements.txt), Render will auto-detect the service settings.

### 1. Link Your Git Repository
1. Push your latest code changes to a GitHub or GitLab repository.
2. Go to the [Render Dashboard](https://dashboard.render.com/) and click **New** -> **Web Service**.
3. Connect your GitHub/GitLab account and select your repository.

### 2. Configure Web Service Settings
- **Name**: `expense-tracker`
- **Region**: Select a region close to your Neon database region (e.g., US East) to reduce latency.
- **Branch**: `main` (or your deployment branch)
- **Runtime**: `Python`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn finance_tracker.wsgi:application`

### 3. Add Environment Variables
1. Scroll down and click **Advanced**.
2. Click **Add Environment Variable** and add the values from **Step 2** above.

---

## Step 4: Run Migrations and Seed Database

In a standard production environment, you need to run Django's `migrate` command to set up tables on Neon Postgres.

### Option A: Automate using Render Build Script (Recommended)
You can automatically run migrations during every deploy by modifying Render's Build Command to:
```bash
pip install -r requirements.txt && python manage.py migrate
```

### Option B: Run commands manually on the Server Console
If you prefer running them manually:
1. In your Render dashboard, select your Web Service.
2. Click on the **Shell** tab on the left.
3. Run the migration command:
   ```bash
   python manage.py migrate
   ```
4. Run the seed data command to populate initial categories/accounts (if needed):
   ```bash
   python manage.py seed_data
   ```

---

## Troubleshooting

### CSRF Verification Failed Error
If you receive a `CSRF Verification Failed` error when trying to log in or submit forms:
- Verify that your `CSRF_TRUSTED_ORIGINS` environment variable is set to the exact URL of your site (including the `https://` prefix, e.g., `https://my-expense-tracker.onrender.com`).

### SSL Connection Errors
If you see an error like `SSL connection is required`:
- Verify that your `DATABASE_URL` contains `?sslmode=require` at the end.
- Verify that `DB_SSL_REQUIRE=True` is defined in your web host's environment settings.
