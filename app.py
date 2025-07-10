import streamlit as st
import pandas as pd
import requests
import json
import time
from openai import OpenAI
import os

# 🚀 Setup your API keys here
openai_key = os.getenv("OPENAI_API_KEY") or st.sidebar.text_input("Enter OpenAI Key", type="password")
serpapi_key = os.getenv("SERPAPI_KEY") or st.sidebar.text_input("Enter SerpAPI Key", type="password")

client = OpenAI(api_key=openai_key)

# 🚀 Helper functions
def classify_brand_image(rating):
    if rating < 4:
        return "Average"
    elif 4 <= rating <= 4.6:
        return "Need to Improve"
    else:
        return "Too Good"

def get_businesses_from_google_maps(query):
    url = "https://serpapi.com/search"
    params = {
        "engine": "google_maps",
        "type": "search",
        "q": query,
        "api_key": serpapi_key
    }
    response = requests.get(url, params=params)
    data = response.json()
    businesses = []
    for res in data.get("local_results", []):
        businesses.append({
            "Company Name": res.get("title", ""),
            "Website": res.get("website", ""),
            "Type": res.get("type", ""),
            "Rating": res.get("rating", 0)
        })
    return pd.DataFrame(businesses)

def get_full_gpt_analysis(company_name, website, company_type):
    prompt = f"""
You are a digital marketing consultant.

Return ONLY a JSON object like this:
{{
"insight": "...",
"hook": "...",
"speed": "...",
"theme": "...",
"seo": "...",
"social": "..."
}}

Business:
- Name: {company_name}
- Website: {website}
- Type: {company_type}
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.choices[0].message.content.strip()
    try:
        data = json.loads(text)
        return (
            data.get("insight", ""),
            data.get("hook", ""),
            data.get("speed", ""),
            data.get("theme", ""),
            data.get("seo", ""),
            data.get("social", "")
        )
    except json.JSONDecodeError:
        st.warning(f"⚠️ JSON failed for {company_name}. Showing raw: {text[:100]}...")
        return "", "", "", "", "", ""

# 🚀 Streamlit UI
st.title("🚀 AI Lead Finder & Marketing Audit Tool")
query = st.text_input("Enter type of business & location (like 'Ayurveda Clinics Dubai'):")

if st.button("Run Agent"):
    if query:
        with st.spinner(f"Searching for: {query} ..."):
            df = get_businesses_from_google_maps(query)
            results = []
            for i, row in df.iterrows():
                company = row["Company Name"]
                website = row.get("Website", "")
                ctype = row.get("Type", "")
                rating = row.get("Rating", 0)
                brand_image = classify_brand_image(rating)

                insight, hook, speed, theme, seo, social = get_full_gpt_analysis(company, website, ctype)
                time.sleep(1)

                if insight:
                    results.append({
                        "Company Name": company,
                        "Website": website,
                        "Type": ctype,
                        "Rating": rating,
                        "Brand Image": brand_image,
                        "GPT Insight": insight,
                        "Outreach Hook": hook,
                        "Website Speed Insight": speed,
                        "Theme Suggestion": theme,
                        "SEO Quick Audit": seo,
                        "Social Presence Guess": social
                    })
            
            out_df = pd.DataFrame(results)
            st.success("✅ Done! See your leads below.")
            st.dataframe(out_df)
            csv = out_df.to_csv(index=False)
            st.download_button("📥 Download CSV", csv, "leads.csv", "text/csv")
    else:
        st.warning("Please enter a business & location to start.")
else:
    st.info("👉 Please enter your API keys in the sidebar to start.")
