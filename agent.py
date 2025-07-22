import json
from typing import Dict, Any, Generator
import sys # Import sys for exiting gracefully on critical errors

# Print immediately to confirm script starts
print("DEBUG: agent.py script started.")

# Import services
# Changed to import get_llm_response for generic LLM interaction
from llm import get_llm_response 
from sql import execute_query, initialize_database, DATABASE_FILE

print("DEBUG: Imports successful in agent.py.")

class AIAgent:
    def __init__(self):
        print(f"DEBUG: AIAgent.__init__ called. Attempting to initialize database: {DATABASE_FILE}")
        try:
            # Call the database initialization function from sql.py
            initialize_database() 
            self.db_schema = self._get_db_schema()
            print(f"DEBUG: AIAgent: Database initialized and schema loaded successfully.")
        except Exception as e:
            print(f"ERROR: AIAgent initialization failed during database setup: {e}", file=sys.stderr)
            print("Please ensure 'sql.py' runs correctly and 'product_data.db' is accessible.", file=sys.stderr)
            raise # Re-raise the exception to stop execution if init fails

    def _get_db_schema(self) -> str:
        """
        Generates a simplified schema description for the LLM.
        This should accurately reflect your product_data.db tables.
        """
        schema = """
        Available tables and their columns:
        - product_eligibility: eligibility_datetime_utc (TEXT), item_id (INTEGER), eligibility (BOOLEAN), message (TEXT)
        - product_total_sales: date (TEXT), item_id (INTEGER), total_sales (REAL), total_units_ordered (INTEGER)
        - product_ad_sales: date (TEXT), item_id (INTEGER), ad_sales (REAL), impressions (INTEGER), ad_spend (REAL), clicks (INTEGER), units_sold (INTEGER)
        """
        return schema

    def _generate_sql_query(self, natural_language_question: str) -> str:
        """
        Uses the LLM to convert a natural language question into an SQL query.
        """
        system_prompt = f"""
        You are an expert in SQLite SQL. Your task is to convert natural language questions into
        accurate and executable SQLite SQL queries.
        
        {self.db_schema}

        Only return the SQL query. Do NOT include any explanations, comments, or additional text.
        Make sure the query is syntactically correct and uses the correct table and column names.
        If the question cannot be answered with the available tables, return "N/A".
        """
        
        prompt = f"Convert the following question into an SQL query: '{natural_language_question}'"
        
        print(f"DEBUG: AI Agent: Sending prompt to LLM for SQL generation: '{prompt}'")
        try:
            sql_query = get_llm_response(prompt, system_prompt=system_prompt) 
            print(f"DEBUG: AI Agent: LLM generated SQL: '{sql_query}'")
        except Exception as e:
            print(f"ERROR: AI Agent: Failed to get response from LLM: {e}", file=sys.stderr)
            return "N/A" # Indicate failure to generate SQL
        
        # Basic validation: ensure it looks like a SQL query
        if not sql_query.strip().upper().startswith(("SELECT", "INSERT", "UPDATE", "DELETE")):
            print(f"DEBUG: AI Agent: LLM response did not look like a valid SQL query: '{sql_query}'")
            return "N/A"
        
        return sql_query.strip()

    def _format_response(self, query_result: Dict[str, Any], original_question: str) -> str:
        """
        Formats the SQL query result into a human-readable string.
        """
        if "error" in query_result:
            print(f"DEBUG: AI Agent ERROR: Database query error: {query_result['error']}")
            return f"I encountered an error while fetching data: {query_result['error']}"
        
        if "message" in query_result:
            print(f"DEBUG: AI Agent: Non-SELECT query message: {query_result['message']}")
            return query_result["message"]
            
        columns = query_result.get("columns", [])
        rows = query_result.get("rows", [])

        if not rows:
            print(f"DEBUG: AI Agent: No results found for question: '{original_question}'")
            return f"I couldn't find any results for your question: '{original_question}'."

        response_parts = [f"Here are the results for '{original_question}':\n"]
        
        header_row = " | ".join(columns)
        response_parts.append(header_row)
        response_parts.append("-" * len(header_row))

        for row in rows:
            row_values = [str(row.get(col, 'N/A')) for col in columns]
            response_parts.append(" | ".join(row_values))
        
        print(f"DEBUG: AI Agent: Formatted response generated.")
        return "\n".join(response_parts)

    def process_question(self, question: str) -> str:
        """
        Main method to process a natural language question.
        """
        print(f"DEBUG: AI Agent: Processing question: '{question}'")
        sql_query = self._generate_sql_query(question)

        if sql_query == "N/A":
            print(f"DEBUG: AI Agent: Could not generate SQL for question: '{question}'")
            return "I'm sorry, I couldn't generate a valid SQL query for that question based on the available data."
        
        print(f"DEBUG: AI Agent: Executing SQL query: '{sql_query}'")
        query_result = execute_query(sql_query)
        return self._format_response(query_result, question)

    def stream_process_question(self, question: str) -> Generator[str, None, None]:
        """
        Processes a question and yields responses in stages for streaming.
        """
        yield "Thinking...\n"
        
        sql_query = self._generate_sql_query(question)
        
        if sql_query == "N/A":
            yield "I'm sorry, I couldn't generate a valid SQL query for that question based on the available data.\n"
            return
        
        yield f"Generated SQL query: `{sql_query}`\n"
        yield "Fetching data...\n"
        
        query_result = execute_query(sql_query)
        formatted_response = self._format_response(query_result, question)
        
        yield formatted_response + "\n"
        yield "Process complete."

if __name__ == "__main__":
    print("\n--- Running AI Agent tests directly ---")
    try:
        print("DEBUG: Attempting to instantiate AIAgent...")
        agent = AIAgent()
        print("DEBUG: AIAgent instantiated successfully.")
        
        print("\n--- Testing Agent with a simple question ---")
        question1 = "What is the eligibility status and message for item_id 29?"
        response1 = agent.process_question(question1)
        print(f"Response for Q1:\n{response1}")

        print("\n--- Testing Agent with another question ---")
        question2 = "Show me the total sales and total units ordered for item_id 0 on 2025-06-01."
        response2 = agent.process_question(question2)
        print(f"Response for Q2:\n{response2}")

        print("\n--- Testing Agent with ad sales data ---")
        question3 = "List the ad sales, impressions, and clicks for item_id 3 on 2025-06-01."
        response3 = agent.process_question(question3)
        print(f"Response for Q3:\n{response3}")

        print("\n--- Testing Agent with a question it can't answer ---")
        question4 = "What is the weather like today in London?"
        response4 = agent.process_question(question4)
        print(f"Response for Q4:\n{response4}")

        print("\n--- Testing Agent with a streaming response (simulated) ---")
        question5 = "List all item_ids and their eligibility from the product_eligibility table."
        print(f"Response for Q5 (streaming):")
        for chunk in agent.stream_process_question(question5):
            print(chunk, end='')
        print("\n--- Agent tests complete ---")
    except Exception as e:
        print(f"\nCRITICAL ERROR: AN UNEXPECTED EXCEPTION OCCURRED DURING AGENT TESTS: {e}", file=sys.stderr)
        print("Please review the error message and ensure all dependencies are met and services are running.", file=sys.stderr)
        sys.exit(1) # Exit with an error code

