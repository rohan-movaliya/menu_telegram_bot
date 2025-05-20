from fastapi import FastAPI
from langchain_google_genai import ChatGoogleGenerativeAI
from PyPDF2 import PdfReader
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from typing import List
import os
import json
import re

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Get the API key from environment
google_api_key = os.getenv("GOOGLE_API_KEY")

class MenuResponse(BaseModel):
    Date: str
    Breakfast: Optional[List[str]]
    Lunch: Optional[List[str]]
    Dinner: Optional[List[str]]

def get_pdf_text(file_path: str) -> str:
    try:
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

@app.get("/menu", response_model=MenuResponse)
async def query_documents():
    pdf_text = get_pdf_text("SD Menu.pdf")
    
    if not pdf_text:
        return {"Date": "", "Breakfast": [], "Lunch": [], "Dinner": []}

    today = datetime.now().strftime("%A, %B %d, %Y")
    
    question = f"""
    Today is {today}.
    Based on the following menu, what is in today's menu?
    
    Menu Contents is:
    {pdf_text}

    Give me output in Dictionary format like this:

    {{
        "Date": "",
        "Breakfast": "",
        "Lunch": "",
        "Dinner": ""
    }}
    """

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro", 
        google_api_key=google_api_key
    )

    response = llm.invoke(question)
    cleaned = response.content.replace("```json", "").replace("```", "").strip()

    json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if json_match:
        try:
            menu_data = json.loads(json_match.group())

            # Convert multiline strings to lists
            for k in ["Breakfast", "Lunch", "Dinner"]:
                if k in menu_data and isinstance(menu_data[k], str):
                    menu_data[k] = [item.strip() for item in menu_data[k].split("\n") if item.strip()]
                    
            return menu_data
        except json.JSONDecodeError:
            return {"Date": "", "Breakfast": [], "Lunch": [], "Dinner": []}
    else:
        return {"Date": "", "Breakfast": [], "Lunch": [], "Dinner": []}
