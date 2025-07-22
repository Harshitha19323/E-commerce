# 🤖 SQL Ecommerce Agent

A web-based application built with Streamlit that allows users to query their product data using natural language. Powered by a Large Language Model (LLM), this agent converts English questions into SQL queries, fetches results from a local SQLite database, and presents them in a human-readable format.

## 🚀 Live App

> [🌐 Access sql Ecommerce agent](https://e-commerce-zderuxssw7tcefkbnsqtcd.streamlit.app/)
> 

# ✨ Features

 
 1.Natural Language to SQL: 
 
  Converts user questions (e.g., "Show me total sales for item_id 25") into executable SQLite queries.

2.Local Data Integration:

   Connects to a local SQLite database (product_data.db) populated from your CSV datasets (Product-Level Eligibility, Total Sales, Ad Sales).

3.Flexible LLM Backend:

   Supports both local LLMs , cloud-based LLM APIs like Google Gemini.

4.Interactive Web UI:

   A simple and intuitive Streamlit interface for asking questions and viewing results.

5.Modular Design:

   Structured into separate Python modules (llm.py, sql.py, agent.py, app.py) for maintainability and scalability.




# 🚀 Getting Started
Follow these steps to set up and run the AI SQL Agent on your local machine.


# ✅ Prerequisites

- Python 3.8+
- Git
- Google API key: A Google AI Studio API Key.
- (Optional) Streamlit Community Cloud account for deployment

---
# 📦 Installation


1. Install Python dependencies:

```bash
pip install -r requirements.txt
```


2. Set up your LLM API Key (if using Google Gemini):
   
      Create a file named .env in the root of your project directory and add your Google API key:

```bash
# Set your Groq API Key
echo "GROQ_API_KEY=your-api-key-here" > .env
```


3. ⚙ Setup & Run
- Prepare your Database:
  
     Run the sql.py script once to download your CSV data from Google Sheets and populate the product_data.db SQLite database.

```bash
python sql.py
```
You should see messages about successful downloads and data imports.

-  Start your LLM Service:

      If using Google Gemini API,No separate server is needed, but ensure you have an active internet connection and your GOOGLE_API_KEY is correctly set in .env.


```bash
python llm.py
```

-  Run the Streamlit Application:

   Open a terminal, navigate to your project's root directory, and run the Streamlit app:


```bash
streamlit run app.py
```

---

## ☁ Deployment (Streamlit Cloud)

1. Push your code to GitHub:

bash
git add .
git commit -m "Initial commit"
git push origin main


2. Go to [Streamlit Cloud](https://streamlit.io/cloud):

- Connect your GitHub repo  
- Set `app.py` as the main file  
- Add your **GROQ_API_KEY** in **Secrets**  
- Deploy

---

## 📚 Dependencies

Listed in `requirements.txt`:


streamlit
google-generativeai
python-dotenv
requests==2.28.1
ollama
openai


---


## 🤝 Contributing

We welcome contributions!  
To contribute:

1. Fork the repo  
2. Create a new feature branch  
3. Submit a pull request

---

This will open the application in your web browser, usually at http://localhost:8501/.

---
## 📂 Project Structure
E-commerce-agent/

├── app.py       
├── agent.py           
├── llm.py            
├── sql.py          
├── .env         
├── product_data.db       
├── requirements.txt 
      
---
