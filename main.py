import os
import smtplib
import urllib.parse
import feedparser
from dotenv import load_dotenv
from email.message import EmailMessage
from google import genai
from google.genai import types

# ---------------- Configuration ---------------- #
# Ensure you have set your GEMINI_API_KEY environment variable
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Email Configuration
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD") # Use a 16-character App Password if using Gmail
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

# The core instructions for the bot's daily search
TOPICS_OF_INTEREST = [
    "Latest developments in quantum computing",
    "Free Courses related to Quantum Computing, Software Engineering, Python, Cryptography, and Mathematics",
    "Trends and updates regarding the Summer 2027 tech internship market",
    "Recent publications or discoveries relating to 19th-century European history",
    "Financial Trends",
    "SpaceX",
    "NASA",
]
# ----------------------------------------------- #

def fetch_rss_news(topics: list) -> str:
    """Fetches the latest news summaries from Google News RSS for the given topics."""
    compiled_news = ""
    
    for topic in topics:
        # Encode the topic string to be URL-safe (e.g., changing spaces to %20)
        encoded_topic = urllib.parse.quote_plus(topic)
        rss_url = f"https://news.google.com/rss/search?q={encoded_topic}&hl=en-US&gl=US&ceid=US:en"
        
        feed = feedparser.parse(rss_url)
        
        compiled_news += f"\n### Topic: {topic} ###\n"
        
        # Grab the top 5 articles per topic to keep the context window manageable
        for entry in feed.entries[:5]:
            compiled_news += f"- Title: {entry.title}\n"
            compiled_news += f"  Link: {entry.link}\n"
            compiled_news += f"  Date: {entry.published}\n\n"
            
    return compiled_news

def generate_news_digest() -> str:
    """Passes the scraped RSS text to Gemini 3.5 Flash for editing and HTML formatting."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # 1. Fetch the raw news data ourselves
    print("Fetching raw news via RSS...")
    raw_news_data = fetch_rss_news(TOPICS_OF_INTEREST)
    
    # 2. Configure the model purely as an editor
    config = types.GenerateContentConfig(
        temperature=0.2, 
        system_instruction="You are an expert news editor. Output the response entirely in raw, clean HTML suitable for an email body. Do not wrap the output in markdown code blocks."
    )
    
    # 3. Construct the prompt with the injected data
    prompt_text = (
        "I have gathered the latest raw news articles from RSS feeds. Please read through them, "
        "synthesize the most important findings, and filter out any clickbait or irrelevant noise.\n\n"
        "Format the output beautifully. Use <h2> for each topic category, and <ul>/<li> for bullet points. "
        "Briefly summarize the headline and include the provided source links as clickable hyperlinks.\n\n"
        f"Here is the raw news data to process:\n{raw_news_data}"
    )

    print("Gemini is editing your news digest...")
    
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt_text,
        config=config
    )
    
    return response.text

def send_email(html_content: str):
    """Sends the generated HTML via email."""
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("Error: Missing email credentials.")
        return

    msg = EmailMessage()
    msg['Subject'] = "Your Daily Custom News Digest"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg.set_content("Please enable HTML to view your daily news digest.")
    msg.add_alternative(html_content, subtype='html')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
            print(f"Successfully delivered the daily digest to {RECEIVER_EMAIL}!")
    except Exception as e:
        print(f"Failed to send email. Error: {e}")

if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("Error: Please set your GEMINI_API_KEY environment variable.")
    else:
        digest_html = generate_news_digest()
        send_email(digest_html)