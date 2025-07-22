import os
import google.generativeai as genai
import json

from dotenv import load_dotenv
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set. Please set it in a .env file or directly in your system environment.")

genai.configure(api_key=GOOGLE_API_KEY)

MODEL_NAME = "gemini-2.5-pro" 

# Renamed get_gemini_response to get_llm_response to match agent.py's import
def get_llm_response(prompt: str, system_prompt: str = "") -> str:
    """
    Sends a prompt to the Google Gemini LLM and returns its response.
    This function is designed to be the generic interface for the agent.
    """
    try:
        # Create a GenerativeModel instance
        model = genai.GenerativeModel(MODEL_NAME)

        # Build the content for the model.
        # Gemini API often works best with roles for system/user.
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{ "text": system_prompt }]})
            contents.append({"role": "model", "parts": [{ "text": "Okay, I understand. I will follow your instructions." }]}) # Acknowledge system prompt
        
        contents.append({"role": "user", "parts": [{ "text": prompt }]})

        # Generate content
        response = model.generate_content(
            contents,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1 # Lower temperature for more deterministic SQL generation
            )
        )
        
        # Access the text from the response
        return response.text.strip()
    except Exception as e:
        print(f"Error calling Google Gemini API: {e}")
        return f"Error: Failed to get response from Gemini API: {e}"


if __name__ == "__main__":
    # Test the LLM service with Gemini
    print("Testing LLM service with Google Gemini API...")
    test_prompt = "What is the capital of France?"
    response = get_llm_response(test_prompt) # Changed function call here too
    print(f"Prompt: {test_prompt}\nResponse: {response}\n")

    sql_system_prompt = """
    You are an expert in SQLite SQL. Your task is to convert natural language questions into
    accurate and executable SQLite SQL queries.
    You will answer every question that is available in the database 
    
    
    The available tables and their columns are:
    - product_eligibility: eligibility_datetime_utc (TEXT), item_id (INTEGER), eligibility (BOOLEAN), message (TEXT)
    - product_total_sales: date (TEXT), item_id (INTEGER), total_sales (REAL), total_units_ordered (INTEGER)
    - product_ad_sales: date (TEXT), item_id (INTEGER), ad_sales (REAL), impressions (INTEGER), ad_spend (REAL), clicks (INTEGER), units_sold (INTEGER)

    Only return the SQL query. Do NOT include any explanations, comments, or additional text.
    Make sure the query is syntactically correct and uses the correct table and column names.
    If the question cannot be answered with the available tables, return "N/A".
    """
    sql_test_prompt = "Get the total sales for item_id 25."
    sql_response = get_llm_response(sql_test_prompt, system_prompt=sql_system_prompt) # Changed function call here too
    print(f"SQL Prompt: {sql_test_prompt}\nGenerated SQL: {sql_response}\n")
