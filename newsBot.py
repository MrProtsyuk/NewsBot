import os
import smtplib
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

def generate_news_digest() -> str:
    """Uses Gemini 3.5 Flash with Google Search Grounding to generate a daily digest."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Enable Google Search grounding so the model can browse the live web
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )
    
    # Configure the model to act as a strict HTML editor
    config = types.GenerateContentConfig(
        tools=[grounding_tool],
        temperature=0.2, # Lower temperature forces factual, concise reporting
        system_instruction="You are an expert news editor. Output the response entirely in raw, clean HTML suitable for an email body. Do not wrap the output in markdown code blocks."
    )
    
    # Construct the prompt dynamically based on your topics
    prompt_text = "Please search for the latest news, updates, and articles from the past 24 hours on the following topics:\n"
    for topic in TOPICS_OF_INTEREST:
        prompt_text += f"- {topic}\n"
    
    prompt_text += "\nSynthesize the most important findings. Filter out clickbait. Use <h2> for each topic, and <ul>/<li> for bullet points. Briefly summarize each point and include the source links in the HTML."

    print("Gemini is compiling your news digest. This may take a few moments...")
    
    # Call the model
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt_text,
        config=config
    )
    
    return response.text

def send_email(html_content: str):
    """Sends the generated HTML via email."""
    msg = EmailMessage()
    msg['Subject'] = "Your Daily Custom News Digest"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    
    # Fallback text if the email client rejects HTML
    msg.set_content("Please enable HTML to view your daily news digest.")
    
    # The actual HTML body
    msg.add_alternative(html_content, subtype='html')

    try:
        # Connect to Gmail's SMTP server
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
        # Run the pipeline
        digest_html = generate_news_digest()
        send_email(digest_html)