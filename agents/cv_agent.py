from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from pydantic import BaseModel, Field # Ensure pydantic is installed (`pip install pydantic`) if not already a dependency of langchain
import json
from utils.config import OLLAMA_BASE_URL, OLLAMA_MODEL
import re # Import regular expressions for email fallback

def get_llm():
    """Initializes and returns the Ollama LLM instance."""
    try:
        llm = Ollama(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL)
        llm.invoke("Test connection") # Simple test
        return llm
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
        return None

# Define the desired structured output using Pydantic
class CandidateInfo(BaseModel):
    name: str | None = Field(description="Candidate's full name. If not found, return None.")
    email: str | None = Field(description="Candidate's primary email address. Extract only the email. If not found, return None.")
    phone: str | None = Field(description="Candidate's primary phone number. If not found, return None.")
    skills_summary: str | None = Field(description="A brief summary or list of key technical and soft skills mentioned.")
    experience_summary: str | None = Field(description="A brief summary of work experience, including roles and durations if available.")
    education_summary: str | None = Field(description="A brief summary of educational qualifications, degrees, and institutions.")

def extract_email_fallback(text: str) -> str | None:
    """Fallback function to find email using regex if LLM fails."""
    # Simple regex for finding email addresses
    email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    matches = re.findall(email_regex, text)
    if matches:
        # Return the first found email, prioritizing common domain patterns if multiple exist
        return matches[0]
    return None

def extract_cv_details(cv_text):
    """
    Uses an LLM to extract structured information from CV text.
    Returns a dictionary with extracted data.
    """
    llm = get_llm()
    if not llm or not cv_text:
        return {"error": "Could not connect to LLM or CV text is empty."}

    # Using JsonOutputParser for structured output
    parser = JsonOutputParser(pydantic_object=CandidateInfo)

    prompt = PromptTemplate(
        template="""
        You are an expert CV parser. Analyze the following CV text and extract the requested information.
        Format your response as a JSON object containing ONLY the fields described below, matching the schema exactly.
        If a piece of information is not found, set its value to null.
        Do NOT include any text before or after the JSON object.

        {format_instructions}

        CV Text:
        ---
        {cv_content}
        ---

        JSON Output:
        """,
        input_variables=["cv_content"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | llm | parser

    try:
        extracted_data = chain.invoke({"cv_content": cv_text})
        # Basic validation and cleanup
        if not isinstance(extracted_data, dict):
            raise ValueError("LLM did not return a valid dictionary.")

        # Ensure email is extracted, attempt fallback if needed
        if not extracted_data.get('email'):
            print("LLM failed to extract email, attempting regex fallback...")
            extracted_data['email'] = extract_email_fallback(cv_text)
            if extracted_data['email']:
                print(f"Fallback successful: Found email {extracted_data['email']}")
            else:
                 print("Fallback failed: Could not find email with regex.")

        # Handle potential None values returned by the LLM/Pydantic if not found
        result = {
            "name": extracted_data.get('name'),
            "email": extracted_data.get('email'),
            "phone": extracted_data.get('phone'),
            "skills": extracted_data.get('skills_summary'),
            "experience": extracted_data.get('experience_summary'),
            "education": extracted_data.get('education_summary'),
            "error": None
        }
        return result

    except Exception as e:
        print(f"Error during CV parsing: {e}")
        print("Attempting fallback email extraction on raw text...")
        # If JSON parsing fails entirely, still try to get the email
        fallback_email = extract_email_fallback(cv_text)
        return {
            "name": None, "email": fallback_email, "phone": None, "skills": None,
            "experience": None, "education": None,
            "error": f"LLM parsing failed. Details: {e}. Attempted email fallback."
        }