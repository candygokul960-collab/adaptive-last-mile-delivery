# Deploy to Streamlit Community Cloud

## What is prepared
- `app.py` is the Streamlit entry point.
- A **Project Downloads** tab provides buttons for the Word/Markdown abstract, PPTX presentation, and a ZIP of the source code.
- `.gitignore` excludes virtual environments, caches, and secrets.
- The project runs with simulated demand and traffic data by default.

## 1. Create a GitHub repository
1. Sign in to GitHub and create a new repository, for example `adaptive-last-mile-delivery`.
2. Keep it Public if you want the simplest Streamlit Community Cloud setup, or use a private repository if your account supports it.
3. Upload the *contents* of this project folder to the repository root. The root should contain `app.py`, `requirements.txt`, `src/`, `data/`, `ABSTRACT.md`, and the presentation file.
4. Do not upload your `venv/`, `.venv/`, `.env`, or `.streamlit/secrets.toml`.

## 2. Deploy on Streamlit Community Cloud
1. Open https://share.streamlit.io/ and sign in with GitHub.
2. Choose **Create app**.
3. Select the repository and branch you uploaded.
4. Set **Main file path** to `app.py`.
5. Select **Deploy** and wait for dependency installation and app startup.

## 3. After deployment
- Open the generated `*.streamlit.app` URL.
- Check all dashboard tabs and the Project Downloads tab.
- Test all four download buttons.
- If a deployment error appears, open **Manage app → Logs** and use the full traceback to troubleshoot.

## Notes
- `requirements.txt` lists the Python dependencies. Streamlit Cloud installs them during deployment.
- No API secrets are required for the simulated-data demo.
- Do not add API keys directly to Python files or commit `.env`/Secrets files.
- This prototype does not currently fetch live traffic or road-network routes. Its traffic and demand are simulated, and route times are illustrative.
