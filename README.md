# Ozon Free Items Tracker
**This repository is no longer functional and is no longer supported.** 

A web application designed to track and hunt items on the Russian online marketplace **Ozon** that participated in the *"Points for Reviews"* promotion. 

At its peak, this tool allowed users to automate item sourcing and purchase products for **just 10% of their original cost** by leveraging review cashback rewards.

### Why was it shut down?
* **Ozon Policy Change:** The marketplace completely disabled the public "Points for Reviews" promotional campaign for regular buyers.
* **Restricted Access:** The feature has been heavily modified and is now exclusively available to verified bloggers. 
* **Obsolescence:** Because public users can no longer access these deals, web-scraping and automated tracking for this campaign are obsolete.

The codebase remains public strictly for historical and portfolio purposes.

## 🛠️ Tech Stack & Dependencies

The project was built on a modern, high-performance Python stack. Project dependencies and virtual environments were managed using `uv`.

### Core Components
* **Framework:** `Django 6.0` — Core backend infrastructure.
* **Task Queue:** `Django-Q2` / `Crontab` — Handles background worker tracking jobs and scheduled tasks (not implemented)
* **Scraping & Automation:** 
  * `DrissionPage 4.1` — Advanced web automation tool used to bypass anti-scraping protections and simulate real browser behavior.
  * `BeautifulSoup4` + `lxml` — Fast HTML parsing and data extraction.
* **Database:** `PostgreSQL` via `psycopg[binary]`.
* **Code Quality:** `Ruff` — Extremely fast linter and formatter.
* **Configuration:** `python-dotenv` — Environment variable management.
