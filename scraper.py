import requests
from bs4 import BeautifulSoup
import csv
import os
import time

# --- CONFIGURATION ---
BASE_URL = "https://web-scraping.dev"
GRAPHQL_URL = "https://web-scraping.dev/api/graphql"
TESTIMONIALS_API_URL = "https://web-scraping.dev/api/testimonials"
DATA_FOLDER = "data"
PRODUCTS_FILE = "products.csv"
REVIEWS_FILE = "reviews.csv"
TESTIMONIALS_FILE = "testimonials.csv"

# --- HELPER FUNCTIONS ---
def save_to_csv(data, folder, filename):
    if not data:
        print(f"No data to save for {filename}")
        return

    if not os.path.exists(folder):
        os.makedirs(folder)
        
    filepath = os.path.join(folder, filename)
    keys = data[0].keys()
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)
        
    print(f"Saved {len(data)} items to {filepath}")

# --- 1. PRODUCT SCRAPER ---
def scrape_products():
    print("\n--- Starting Product Scraping ---")
    all_products = []
    current_url = f"{BASE_URL}/products"
    
    while current_url:
        print(f"Fetching: {current_url}")
        try:
            resp = requests.get(current_url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            print(f"Error fetching product page: {e}")
            break

        containers = soup.select("div.row.product")
        if not containers:
            print("No products found on this page.")
            
        for p in containers:
            try:
                name = p.select_one(".description h3 a").get_text(strip=True)
                price = p.select_one(".price-wrap .price").get_text(strip=True)
                desc = p.select_one(".short-description").get_text(strip=True)
                all_products.append({"name": name, "price": price, "description": desc})
            except: continue

        # Pagination
        next_link = None
        for link in soup.select("div.paging a"):
            if ">" in link.get_text() or "Next" in link.get_text():
                href = link.get('href')
                if href:
                    next_link = href if href.startswith("http") else BASE_URL + href
                    break
        current_url = next_link
        if current_url: time.sleep(1)

    return all_products

# --- 2. REVIEWS SCRAPER (GraphQL) ---
def scrape_reviews_graphql():
    print("\n--- Starting Review Scraping (GraphQL) ---")
    all_reviews = []
    
    query = """
    query GetReviews($first: Int, $after: String) {
      reviews(first: $first, after: $after) {
        edges {
          node {
            rid
            text
            rating
            date
          }
          cursor
        }
        pageInfo {
          endCursor
          hasNextPage
        }
      }
    }
    """
    
    cursor = None
    has_next = True
    page = 1
    
    while has_next:
        print(f"Fetching reviews page {page}...")
        payload = {
            "query": query,
            "variables": {
                "first": 20,
                "after": cursor
            }
        }
        
        try:
            response = requests.post(GRAPHQL_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            
            reviews_data = data.get("data", {}).get("reviews", {})
            edges = reviews_data.get("edges", [])
            page_info = reviews_data.get("pageInfo", {})
            
            if not edges:
                print("No reviews found in response.")
                break
            
            for edge in edges:
                node = edge.get("node", {})
                all_reviews.append({
                    "date": node.get("date"),
                    "stars": node.get("rating"),
                    "text": node.get("text")
                })
            
            has_next = page_info.get("hasNextPage", False)
            cursor = page_info.get("endCursor")
            page += 1
            time.sleep(1)
            
        except Exception as e:
            print(f"Error fetching reviews: {e}")
            break

    return all_reviews

# --- 3. TESTIMONIALS SCRAPER (HTMX + Star Counting) ---
def scrape_testimonials():
    print("\n--- Starting Testimonials Scraping (HTMX) ---")
    all_testimonials = []
    
    # Headers required to mimic the browser's infinite scroll request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://web-scraping.dev/testimonials",
        "Hx-Request": "true",
        "Hx-Current-Url": "https://web-scraping.dev/testimonials"
    }
    
    page = 1
    while True:
        url = f"{TESTIMONIALS_API_URL}?page={page}"
        print(f"Fetching API: {url}")
        
        try:
            resp = requests.get(url, headers=headers)
            
            # 403 usually means we reached the end of pages
            if resp.status_code != 200:
                print(f"API status {resp.status_code}. Stopping.")
                break
            
            # HTMX usually returns HTML snippets, so we parse with BeautifulSoup
            try:
                # 1. Try JSON (unlikely for HTMX but possible)
                data = resp.json()
                items = data if isinstance(data, list) else data.get('data', [])
                if not items: break
                for item in items:
                    all_testimonials.append({
                        "text": item.get("text", ""),
                        "stars": item.get("rating", 0) 
                    })
                page += 1
                continue
            except:
                # 2. Fallback to HTML parsing (Standard for HTMX)
                soup = BeautifulSoup(resp.text, "html.parser")
                items = soup.select("div.testimonial")
                
                if not items:
                    print("No more items found in HTML.")
                    break
                    
                print(f"  - Found {len(items)} testimonials.")
                
                for t in items:
                    # Extract Text
                    text_el = t.select_one("p.text")
                    text = text_el.get_text(strip=True) if text_el else ""
                    
                    # Extract Stars (Count SVGs inside .rating)
                    rating_el = t.select_one("span.rating")
                    if rating_el:
                        # Count how many <svg> tags are inside the rating span
                        stars = len(rating_el.find_all("svg"))
                    else:
                        stars = 0
                        
                    all_testimonials.append({
                        "text": text,
                        "stars": stars
                    })
                
                page += 1
                time.sleep(1)
            
        except Exception as e:
            print(f"Error scraping testimonials: {e}")
            break
            
    return all_testimonials

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # 1. Scrape Products
    products_data = scrape_products()
    save_to_csv(products_data, DATA_FOLDER, PRODUCTS_FILE)
    
    # 2. Scrape Reviews
    reviews_data = scrape_reviews_graphql()
    save_to_csv(reviews_data, DATA_FOLDER, REVIEWS_FILE)
    
    # 3. Scrape Testimonials
    testimonials_data = scrape_testimonials()
    save_to_csv(testimonials_data, DATA_FOLDER, TESTIMONIALS_FILE)
