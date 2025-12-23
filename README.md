# PythonWebScrapingApp

Homework project for a Data Mining class.  
The app scrapes product, review, and testimonial data from a mock e‑commerce website and provides an interactive Streamlit dashboard with sentiment analysis.

---

## How to Use

### 1. Download the project

Clone the repository or download the ZIP and extract it:

git clone https://github.com/pavlean1/PythonWebScrapingApp.git

cd PythonWebScrapingApp
(If you downloaded a ZIP, just extract it and `cd` into the folder.)

---

### 2. (Optional) Create and activate a virtual environment

python -m venv venv

venv\Scripts\activate # Windows

or on macOS / Linux:

source venv/bin/activate

---

### 3. Install requirements

python -m pip install -r requirements.txt

---

### 4. Run the scraper

This downloads products, reviews, and testimonials into the `data/` folder:

python scraper.py

---

### 5. Run the web app

Start the Streamlit dashboard:

streamlit run app.py

Then open the URL shown in the terminal (usually `http://localhost:8501`) in your browser.

---

### Project Structure

- `scraper.py` – Web scraping scripts (products, reviews via GraphQL, testimonials via HTMX).
- `app.py` – Streamlit application with sentiment analysis and visualizations.
- `data/` – Folder where CSV files are saved (`products.csv`, `reviews.csv`, `testimonials.csv`).
- `requirements.txt` – Python dependencies for the project.




