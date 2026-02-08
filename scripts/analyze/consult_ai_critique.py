
import os
import sys
from groq import Groq
from dotenv import load_dotenv

# Load Env
load_dotenv()

def consult_ai():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY not found.")
        return

    client = Groq(api_key=api_key)
    
    # Read the Dashboard Code
    file_path = os.path.join("src", "jojo_trading", "ui", "news_dashboard.py")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code_content = f.read()
    except FileNotFoundError:
        print(f"Error: Could not find {file_path}")
        return

    print("--- Consulting AI (Groq Llama-3) for UI/UX Improvements ---")
    print("Analyzing code structure...")

    prompt = f"""
    You are a Senior Product Designer and Streamlit Expert.
    Review the following Python code for a trading news dashboard ('JoJoTrader').
    
    Current Features:
    - Real-time Jin10 news feed.
    - AI Analysis (Sentiment, Heat, Sectors) using Groq.
    - Taiwan/US Session split tabs.
    - Supply chain tagging for TW stocks.
    
    Code:
    ```python
    {code_content}
    ```
    
    Please provide 3-5 concrete, professional UI/UX improvement suggestions to make this tool feel like a "Bloomberg Terminal" or professional trading software. 
    Focus on:
    1. Visual Hierarchy & Aesthetics.
    2. Data Visualization (Charts/Gauges).
    3. User Interaction (Filters/Alerts).
    
    Keep the response concise and actionable.
    """

    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful expert developer."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
        )
        
        print("\n=== AI Improvement Suggestions ===\n")
        print(completion.choices[0].message.content)
        print("\n==================================")
        
    except Exception as e:
        print(f"AI Consultation failed: {e}")

if __name__ == "__main__":
    consult_ai()
