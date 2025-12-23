import streamlit as st
import pandas as pd
from transformers import pipeline
import os
from wordcloud import WordCloud
import matplotlib.pyplot as plt


# --- CONFIGURATION ---
DATA_FOLDER = "data"
PRODUCTS_FILE = os.path.join(DATA_FOLDER, "products.csv")
REVIEWS_FILE = os.path.join(DATA_FOLDER, "reviews.csv")
TESTIMONIALS_FILE = os.path.join(DATA_FOLDER, "testimonials.csv")

# --- CACHING THE AI MODEL ---
# @st.cache_resource ensures the model loads only once, making the app faster
@st.cache_resource
def load_sentiment_model():
    return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

# --- DATA LOADING ---
def load_data(filepath):
    if os.path.exists(filepath):
        return pd.read_csv(filepath)
    else:
        return None

# --- MAIN APP ---
def main():
    st.set_page_config(page_title="HW3: AI Dashboard", layout="wide")
    st.title("📊 HW3: E-Commerce AI Dashboard")
    st.markdown("Monitor brand reputation using scraped data and Deep Learning.")
    
    st.sidebar.header("Navigation")
    page = st.sidebar.radio("Go to:", ["Products", "Testimonials", "Reviews (AI Analysis)"])
    
    # --- 1. PRODUCTS PAGE ---
    if page == "Products":
        st.header("📦 Product Catalog")
        df = load_data(PRODUCTS_FILE)
        if df is not None:
            st.metric("Total Products", len(df))
            st.dataframe(df, use_container_width=True)
        else:
            st.error(f"File not found: {PRODUCTS_FILE}. Run scraper.py first.")

    # --- 2. TESTIMONIALS PAGE ---
    elif page == "Testimonials":
        st.header("🗣️ Customer Testimonials")
        df = load_data(TESTIMONIALS_FILE)
        if df is not None:
            # Calculate Average Rating if 'stars' exists
            if 'stars' in df.columns:
                avg_stars = df['stars'].mean()
                st.metric("Average Customer Rating", f"{avg_stars:.2f} ⭐")
            
            st.dataframe(df, use_container_width=True)
        else:
            st.error(f"File not found: {TESTIMONIALS_FILE}. Run scraper.py first.")

    # --- 3. REVIEWS PAGE (THE CORE TASK) ---
    elif page == "Reviews (AI Analysis)":
        st.header("🤖 Reviews & Sentiment Analysis")
        df = load_data(REVIEWS_FILE)
        
        if df is not None:
            # Preprocessing: Convert 'date' to datetime
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
            
            # --- MONTH FILTER ---
            months = ["January", "February", "March", "April", "May", "June", 
                      "July", "August", "September", "October", "November", "December"]
            
            col1, col2 = st.columns([1, 2])
            with col1:
                selected_month_name = st.select_slider("Select Month (2023)", options=months)
            
            # Filter Data
            month_map = {name: i+1 for i, name in enumerate(months)}
            selected_month_num = month_map[selected_month_name]
            
            filtered_df = df[
                (df['date'].dt.month == selected_month_num) & 
                (df['date'].dt.year == 2023)
            ]
            
            st.info(f"Found **{len(filtered_df)}** reviews for {selected_month_name} 2023.")
            
            if not filtered_df.empty:
                # Show raw filtered data
                with st.expander("View Raw Reviews"):
                    st.dataframe(filtered_df)
                
                # --- AI ANALYSIS SECTION ---
                st.divider()
                st.subheader("🧠 Deep Learning Analysis")
                
                if st.button("Analyze Sentiment for this Month"):
                    with st.spinner("Loading model and analyzing text..."):
                        classifier = load_sentiment_model()
                        
                        # Prepare text (handle empty values and truncate to 512 tokens)
                        texts = filtered_df['text'].fillna("").astype(str).tolist()
                        texts = [t[:512] for t in texts]
                        
                        # Run Inference
                        results = classifier(texts)
                        
                        # Add results to DataFrame
                        filtered_df = filtered_df.copy() # Avoid SettingWithCopy warning
                        filtered_df['Sentiment'] = [r['label'] for r in results]
                        filtered_df['Confidence'] = [r['score'] for r in results]
                        
                        st.success("Analysis Complete!")
                        
                        # --- VISUALIZATION ---
                        col_chart, col_stats = st.columns(2)
                        
                        with col_chart:
                            st.subheader("Sentiment Distribution")
                            counts = filtered_df['Sentiment'].value_counts()
                            st.bar_chart(counts, color="#ff4b4b")
                        
                        with col_stats:
                            st.subheader("Detailed Results")
                            st.dataframe(filtered_df[['date', 'Sentiment', 'Confidence', 'text']], use_container_width=True)
                            
                            avg_conf = filtered_df['Confidence'].mean()
                            st.metric("Avg. Model Confidence", f"{avg_conf:.2%}")

                                                # --- WORD CLOUD BONUS FEATURE ---
                        st.subheader("☁️ Word Cloud of Review Texts")

                        # Combine all review texts into one big string
                        all_text = " ".join(filtered_df['text'].dropna().astype(str).tolist())

                        if all_text.strip():
                            # Generate the word cloud
                            wc = WordCloud(
                                width=800,
                                height=400,
                                background_color="white"
                            ).generate(all_text)

                            # Display with matplotlib
                            fig, ax = plt.subplots(figsize=(10, 5))
                            ax.imshow(wc, interpolation="bilinear")
                            ax.axis("off")

                            st.pyplot(fig)
                        else:
                            st.info("No text available to generate a word cloud for this month.")


            else:
                st.warning("No reviews available for this month to analyze.")
        else:
            st.error(f"File not found: {REVIEWS_FILE}. Run scraper.py first.")

if __name__ == "__main__":
    main()
