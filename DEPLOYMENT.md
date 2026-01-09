# Deployment Guide: Google Sites Integration

This guide explains how to embed your existing Streamlit app into `wiljanvandenberge.com` and set up the `mw-tracker` subdomain.

## Phase 1: Embed in Google Sites

We will place your running Streamlit app inside a specific page on your Google Site so it retains your website's header and navigation.

1.  **Get your App URL:** Copy the link to your running app (e.g., `https://your-app-name.streamlit.app`).
    *   **Crucial:** Add `/?embed=true` to the end of your URL (e.g., `https://your-app-name.streamlit.app/?embed=true`). This prevents "Too many redirects" errors caused by browser privacy settings.
2.  **Create a Page:** Open your Google Sites editor. Create a new page (e.g., name it "MW Tracker").
3.  **Insert Embed:**
    *   On the right sidebar, click **Insert** > **Embed**.
    *   Paste your **Streamlit App URL (with the embed parameter)**.
    *   Select **"Whole page"** if offered, or just "Insert".
4.  **Resize:**
    *   **Crucial Step:** Drag the blue dots to make the frame as wide and *tall* as possible.
    *   Streamlit apps can be long. Make the embed frame tall enough so users don't have to scroll *twice* (once for the site, once for the widget).
5.  **Publish:** Click **Publish** on Google Sites.
    *   Note the final URL of this page (e.g., `https://www.wiljanvandenberge.com/mw-tracker`).

## Phase 2: Finalizing the URL

Since you are using your existing domain `wiljanvandenberge.com` with Google Sites, the app will be accessible at:
`https://www.wiljanvandenberge.com/mw-tracker` (or whatever you named the page).

This is a clean, professional link that keeps users within your primary website context.

## Maintenance: How to Update Data

The app is configured to always use a **Light Theme** (defined in `.streamlit/config.toml`) to match your website. To update the minimum wage stats:

1.  **Run Locally:**
    ```bash
    # Run these on your Mac
    python3 mw_tracker/fetch_indices.py
    python3 mw_tracker/scraper.py
    python3 mw_tracker/create_mw_archive.py
    ```
2.  **Push to GitHub:**
    ```bash
    git add data/*.csv
    git commit -m "data: update minimum wage figures"
    git push origin main
    ```
3.  **Done:** Streamlit Cloud watches your repository. It will see the new commit and automatically restart the app with the fresh data (usually within 30-60 seconds).
