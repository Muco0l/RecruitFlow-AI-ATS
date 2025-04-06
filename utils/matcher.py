from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from utils.config import OLLAMA_BASE_URL, OLLAMA_MODEL
import re # For extracting the score

def get_llm():
    """Initializes and returns the Ollama LLM instance."""
    try:
        llm = Ollama(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL)
        llm.invoke("Test connection") # Simple test
        return llm
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
        return None

def calculate_match_score(jd_summary, candidate_data):
    """
    Uses an LLM to calculate a match score between a JD summary and candidate data.
    Returns an integer score (0-100) or -1 on error.
    """
    llm = get_llm()
    if not llm:
        print("Matcher Error: Could not connect to LLM.")
        return -1
    if not jd_summary or not candidate_data:
        print("Matcher Error: Missing JD summary or candidate data.")
        return -1

    # Combine relevant candidate info into a single string
    candidate_profile = f"""
    Candidate Skills: {candidate_data.get('skills', 'N/A')}
    Candidate Experience: {candidate_data.get('experience', 'N/A')}
    Candidate Education: {candidate_data.get('education', 'N/A')}
    """

    prompt_template = PromptTemplate.from_template(
        """
        You are a hiring expert comparing a job description summary against a candidate profile.
        Analyze the match based on skills, experience, and qualifications.

        Job Description Summary:
        ---
        {jd_summary}
        ---

        Candidate Profile:
        ---
        {candidate_profile}
        ---

        Based on the comparison, provide a match score between 0 (no match) and 100 (perfect match).
        Focus on the relevance of the candidate's skills and experience to the job requirements.
        Output ONLY the integer score. For example: 85
        Score:
        """
    )

    parser = StrOutputParser()
    chain = prompt_template | llm | parser

    try:
        result_str = chain.invoke({
            "jd_summary": jd_summary,
            "candidate_profile": candidate_profile
        })

        # Extract the number from the LLM response
        match = re.search(r'\d+', result_str)
        if match:
            score = int(match.group(0))
            # Clamp score to 0-100 range
            return max(0, min(100, score))
        else:
            print(f"Matcher Warning: Could not parse score from LLM response: '{result_str}'")
            # Could try a simpler keyword match here as a fallback if needed
            return 0 # Default to low score if parsing fails

    except Exception as e:
        print(f"Error during matching: {e}")
        return -1