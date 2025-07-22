import streamlit as st
import os
import sys

# Add the project directory to the Python path
# This is crucial so Python can find 'llm.py', 'sql.py', and 'agent.py'
# Assumes app.py is in the root of your project directory
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the AI Agent from your project
# Ensure 'agent.py' is in the same directory or accessible via PYTHONPATH
try:
    from agent import AIAgent
except ImportError as e:
    st.error(f"Failed to import AIAgent: {e}")
    st.error("Please ensure 'agent.py' is in your project directory and its imports (llm.py, sql.py) are correctly set up.")
    st.stop() # Stop the app if a critical import fails

# Initialize the AI Agent globally.
# This will also trigger the database initialization (product_data.db)
# and set up the connection to the configured LLM (Ollama or Gemini).
ai_agent = None # Initialize to None
try:
    st.info("Initializing AI Agent and connecting to database/LLM...")
    ai_agent = AIAgent()
    st.success("AI Agent initialized and connected!")
except Exception as e:
    st.error(f"Failed to initialize AI Agent or connect to backend services: {e}")
    st.warning("Please ensure the following:")
    st.warning("1. Your `sql.py` file has been run at least once (`python sql.py`) to create and populate `product_data.db`.")
    st.warning("2. Your LLM service is running and accessible:")
    st.warning("   - If using **Ollama**: Ensure Ollama desktop app is running and your chosen model (e.g., `llama3`) is downloaded and active (`ollama run llama3` in a separate terminal).")
    st.warning("   - If using **Google Gemini API**: Ensure your `GOOGLE_API_KEY` is correctly set in a `.env` file in your project root.")
    st.warning("3. Check your terminal for more detailed error messages from `agent.py`, `llm.py`, or `sql.py`.")
    st.stop() # Stop the app if initialization fails

## Streamlit App Configuration
st.set_page_config(page_title="AI SQL Data Retriever", layout="centered")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .main-header {
        font-size: 2.5em;
        color: #4CAF50;
        text-align: center;
        margin-bottom: 30px;
        font-weight: 700;
    }
    .stTextInput > div > div > input {
        border-radius: 10px;
        padding: 10px;
        font-size: 1.1em;
        border: 1px solid #ddd;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        border-radius: 10px;
        padding: 10px 20px;
        font-size: 1.2em;
        font-weight: bold;
        border: none;
        cursor: pointer;
        transition: background-color 0.3s ease, box-shadow 0.3s ease;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
        width: 100%; /* Make button full width */
        margin-top: 20px;
    }
    .stButton > button:hover {
        background-color: #45a049;
        box-shadow: 3px 3px 8px rgba(0,0,0,0.3);
    }
    .response-subheader {
        font-size: 1.8em;
        color: black; /* Changed color to black */
        margin-top: 40px;
        margin-bottom: 15px;
        font-weight: 600;
    }
    .response-text {
        background-color: #f0f2f6; /* Light grey background */
        color: #1a1a1a; /* Very dark grey/almost black text for better contrast */
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        line-height: 1.6;
        white-space: pre-wrap; /* Preserves whitespace and line breaks */
        overflow-x: auto; /* Allows horizontal scrolling for long lines */
        font-family: 'monospace'; /* Use monospace for data output */
    }
    .stSpinner > div {
        color: #4CAF50 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("<h1 class='main-header'>Ask your questions about Product Data</h1>", unsafe_allow_html=True)

# Input text box for the user's question
question = st.text_input(
    "Enter your question:",
    placeholder="e.g., 'Show me the total sales for item_id 25', 'List all product eligibilities that are FALSE', 'What are the ad sales and impressions for item_id 0?'",
    key="input"
)

# Button to submit the question
submit = st.button("Get Answer")

# If the submit button is clicked and a question is provided
if submit and question:
    if ai_agent: # Ensure agent was initialized successfully
        with st.spinner('Processing your request... This might take a moment as the AI generates the SQL query and fetches data.'):
            try:
                # Use the AI agent to process the natural language question
                response_text = ai_agent.process_question(question)
                
                st.markdown("<h2 class='response-subheader'>The Response Is:</h2>", unsafe_allow_html=True)
                st.markdown(f"<div class='response-text'>{response_text}</div>", unsafe_allow_html=True)
                
                # --- Bonus: Placeholder for graphs/visuals ---
                # To add graphs, your ai_agent.process_question would need to return
                # structured data (e.g., a dictionary with 'answer_text' and 'chart_data').
                # Then, you would use Streamlit's charting functions here.
                # Example:
                # if 'chart_data' in response_object and response_object['chart_data']:
                #     st.bar_chart(response_object['chart_data'])
                # --------------------------------------------

            except Exception as e:
                st.error(f"An error occurred while processing your request: {e}")
                st.info("Please check the terminal where your Streamlit app is running for more details.")
    else:
        st.error("AI Agent was not initialized. Please resolve the setup issues mentioned above.")

elif submit and not question:
    st.warning("Please enter a question to get an answer.")

