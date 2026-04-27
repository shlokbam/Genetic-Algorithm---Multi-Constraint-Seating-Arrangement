# Deployment Instructions for Render

To deploy your **Exam Seating Optimizer** to Render, follow these steps:

### 1. Create a New Web Service
1. Log in to your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** and select **Web Service**.
3. Connect your GitHub repository.

### 2. Configure Service Settings
When prompted for configuration, use the following settings:

*   **Name**: `exam-seating-optimizer` (or anything you prefer)
*   **Environment**: `Python 3`
*   **Region**: Select the one closest to you (e.g., `Singapore` or `Oregon`)
*   **Branch**: `main`
*   **Build Command**: `pip install -r requirements.txt`
*   **Start Command**: `gunicorn app:app`

### 3. Instance Type
Select the **Free** tier (or higher if you need more performance).

### 4. Advanced (Environment Variables)
Render will automatically assign a `PORT`, which the application is now configured to handle automatically. You don't need to add any manual environment variables.

---

### Files I Have Added/Modified for You:
- **`requirements.txt`**: Added all necessary libraries (`flask`, `pandas`, `openpyxl`, `gunicorn`).
- **`app.py`**: Updated to listen on the correct port and host for production.

Once you click **Create Web Service**, Render will build and deploy your site!
