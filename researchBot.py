import os
import smtplib
import feedparser
from email.message import EmailMessage
from google import genai
from google.genai import types

# ---------------- Configuration ---------------- #
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL = SENDER_EMAIL 

# arXiv categories: quant-ph (Quantum Physics), cs.CR (Cryptography), cs.DS (Data Structures)
ARXIV_CATEGORIES = ["cat:quant-ph", "cat:cs.CR", "cat:cs.DS", '(cat:quant-ph+OR+cat:cs.DS)+AND+all:%22hybrid+quantum-classical%22']
MAX_PAPERS_PER_CATEGORY = 4
# ----------------------------------------------- #

def fetch_academic_papers() -> str:
    """Queries the arXiv API for the most recent papers in specified domains."""
    compiled_abstracts = ""
    
    for category in ARXIV_CATEGORIES:
        # Construct the arXiv API endpoint URL
        url = f"http://export.arxiv.org/api/query?search_query={category}&max_results={MAX_PAPERS_PER_CATEGORY}&sortBy=submittedDate&sortOrder=descending"
        
        feed = feedparser.parse(url)
        clean_category_name = category.replace("cat:", "").upper()
        compiled_abstracts += f"\n=== CATEGORY: {clean_category_name} ===\n"
        
        for entry in feed.entries:
            # Extract authors list cleanly
            authors = ", ".join([author.name for author in entry.authors]) if 'authors' in entry else "Unknown"
            
            compiled_abstracts += f"Title: {entry.title}\n"
            compiled_abstracts += f"Authors: {authors}\n"
            compiled_abstracts += f"Link: {entry.link}\n"
            compiled_abstracts += f"Abstract: {entry.summary}\n"
            compiled_abstracts += "----------------------------------------\n"
            
    return compiled_abstracts

def generate_literature_digest() -> str:
    """Uses Gemini 3.5 Flash to synthesize dense abstracts into an executive briefing."""
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    print("Fetching latest papers from arXiv...")
    raw_paper_data = fetch_academic_papers()
    
    config = types.GenerateContentConfig(
        temperature=0.2, # Low temperature ensures highly accurate reporting of the math/theses
        system_instruction=(
            "You are an elite academic research advisor and computer science professor. "
            "Your job is to read dense academic abstracts and synthesize them into highly readable, "
            "insightful summaries for an executive briefing. Output the response entirely in raw, "
            "clean HTML suitable for an email body. Do not use markdown code blocks."
        )
    )
    
    prompt_text = f"""
    I have pulled the latest pre-print papers from arXiv. Please review the following titles and abstracts, 
    filter out highly niche or derivative papers, and highlight the most impactful breakthroughs or developments.
    
    For each selected paper, provide:
    1. A simplified, 2-sentence breakdown of the core problem and the authors' proposed solution/thesis.
    2. Why this paper matters to structural computer science or quantum theory.
    3. A clickable hyperlink to the full paper using the provided URL.
    
    Structure the email beautifully using <h2> for categories, <h3> for paper titles, and standard paragraph/list tags. 
    Wrap critical concepts, algorithms, or mathematical terms in bold text.
    
    Here is the raw literature data to process:
    {raw_paper_data}
    """

    print("Gemini is reading and synthesizing abstracts...")
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt_text,
        config=config
    )
    
    return response.text

def send_email(html_content: str):
    """Delivers the literature review to your inbox."""
    msg = EmailMessage()
    msg['Subject'] = "Your Daily Academic Paper Radar"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg.set_content("Please enable HTML to view your academic report.")
    msg.add_alternative(html_content, subtype='html')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
            print(f"Academic digest delivered successfully!")
    except Exception as e:
        print(f"Failed to send email. Error: {e}")

if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY environment variable not set.")
    else:
        try:
            digest_html = generate_literature_digest()
            send_email(digest_html)
        except Exception as err:
            print(f"Execution failed: {err}")