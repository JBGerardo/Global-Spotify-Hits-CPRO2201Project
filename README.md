# Global Spotify Hits: Song Popularity Across Different Countries

This project is for **CPRO 2201 – Python Programming II**.  
We analyze a public Spotify Charts dataset using **NumPy, Pandas, Matplotlib**, and a **Django + SQLite** web application to present insights such as:

- How popular songs appear across multiple countries.
- Chart diversity per country.
- How long tracks stay on the charts.
- Comparison of global hits vs country-specific hits.

---

## Tech Stack

- Python (virtual environment)
- NumPy, Pandas, Matplotlib
- Django, SQLite
- Git and GitHub for version control
- VS Code as the main IDE

---

## Project Structure

- `data/` – Raw and processed Spotify datasets.
- `notebooks/` – Jupyter notebooks for exploration.
- `analysis/` – Reusable Python scripts for cleaning and analysis.
- `webapp/` – Django project and app for the web interface.
- `docs/` – Report and reference materials.

More details will be added as the project progresses.

---

## Getting Started (Local Setup)

These steps assume **Python 3.10+** and **Git** are installed.

### 1. Clone the repository

```bash
git clone <REPO-URL>
cd Global-Spotify-Hits-CPRO2201Project-main

### 2. Creat and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
# source venv/bin/activate


## 3. Install Dependencies
pip install -r requirements.txt

## 4. Go to the Django Project Folder
cd webapp

## 5. Apply database migration
python manage.py migrate

## 6. Data Loading
cd webapp     # if you are not already here
python manage.py load_charts --file charts_2023.csv

## 7. Verify that data is loaded
python manage.py shell

# Then in Python Shell:
from charts.models import ChartEntry
ChartEntry.objects.count()   # should be > 0
exit()

If the count is 0:

# Make sure data/raw/charts_2023.csv exists.
# Confirm the command was typed correctly (load_charts --file charts_2023.csv).
# Check for any error messages printed when running the command.

-------------------------
#Running the Web App
cd webapp #if needed
python manage.py runserver
