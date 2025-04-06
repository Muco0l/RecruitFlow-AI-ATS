from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from utils.config import OLLAMA_BASE_URL, OLLAMA_MODEL

def get_llm():
    """Initializes and returns the Ollama LLM instance."""
    try:
        llm = Ollama(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL)
        # Perform a simple test invocation
        llm.invoke("Test connection")
        print(f"Successfully connected to Ollama model: {OLLAMA_MODEL} at {OLLAMA_BASE_URL}")
        return llm
    except Exception as e:
        print(f"Error connecting to Ollama: {e}")
        print(f"Please ensure Ollama is running and the model '{OLLAMA_MODEL}' is available at {OLLAMA_BASE_URL}")
        return None

def summarize_job_description(jd_text):
    """
    Uses an LLM to summarize the key aspects of a job description.
    Returns a structured summary string.
    """
    llm = get_llm()
    if not llm or not jd_text:
        return "Error: Could not connect to LLM or JD text is empty."

    prompt_template = PromptTemplate.from_template(
        """
        You are an expert recruitment assistant. Analyze the following job description and extract the key information.
        Provide a concise summary covering these points:
        1.  **Key Responsibilities:** (List 2-4 main duties)
        2.  **Required Skills:** (List essential technical and soft skills)
        3.  **Required Experience:** (Specify years of experience, domains, etc.)
        4.  **Required Qualifications:** (Mention degrees, certifications, etc.)

        Job Description:
        ---
        {job_description}
        ---

        Concise Summary:
        """
    )

    parser = StrOutputParser()
    chain = prompt_template | llm | parser

    try:
        summary = chain.invoke({"job_description": jd_text})
        return summary.strip()
    except Exception as e:
        print(f"Error during JD summarization: {e}")
        return f"Error: Could not generate summary. Details: {e}"