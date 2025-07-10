from dotenv import load_dotenv
load_dotenv()  # Load environment variables

import streamlit as st
import os
import sqlite3
import openai

# ✅ Configure Groq (OpenAI-compatible) API
openai.api_key = os.getenv("GROQ_API_KEY")
openai.api_base = "https://api.groq.com/openai/v1"

# ✅ Use Groq to convert English to SQL
def get_groq_response(question, prompt):
    try:
        full_prompt = f"{prompt[0]}\n\nQuestion: {question}"
        response = openai.ChatCompletion.create(
            model="llama3-70b-8192",  # You can try "mixtral-8x7b-32768" too
            messages=[
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        # 👇 Print and display the full error for debugging
        import traceback
        error_details = traceback.format_exc()
        print("Groq API error:\n", error_details)
        st.error(f"Groq API error:\n{error_details}")
        return "ERROR"


# ✅ Execute SQL query
import pandas as pd

def read_sql_query(sql, db):
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        column_names = [description[0] for description in cur.description]
        conn.close()

        df = pd.DataFrame(rows, columns=column_names)
        return df

    except Exception as e:
        return f"SQL ERROR: {e}"


# ✅ Prompt template
prompt = [
    """
    You are an expert in converting English questions to SQL queries!
    The SQL database has the name EMPLOYEE and has the following columns:
    - NAME (employee name)
    - DEPARTMENT (employee's department)
    - SALARY (employee's salary in integer)

    Examples:
    - "How many employees are there?" → SELECT COUNT(*) FROM EMPLOYEE;
    - "List all employees in the Engineering department" → SELECT * FROM EMPLOYEE WHERE DEPARTMENT = 'Engineering';
    - "What is the average salary of employees?" → SELECT AVG(SALARY) FROM EMPLOYEE;

    Only return valid SQL queries. Do not include the word 'SQL' or use backticks (```). The output should be only the SQL query.
    """
]


# ✅ Streamlit UI for Talk2Data - SQL Query Assistant

import streamlit as st

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Talk2Data - Natural Language to SQL",
    page_icon="🧠",
    layout="centered"
)

# ---------- STYLING ----------
st.markdown(
    """
    <style>
    .main {
        background-color: #f9f9f9;
    }
    .block-container {
        padding-top: 2rem;
    }
    .stTextInput>div>div>input {
        font-size: 18px;
        padding: 10px;
    }
    .stButton>button {
        background-color: #008CBA;
        color: white;
        padding: 0.6rem 1.2rem;
        font-size: 16px;
        border-radius: 5px;
    }
    .stButton>button:hover {
        background-color: #006f9b;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- HEADER ----------
st.title("🧠 Talk2Data")
st.caption("**Ask questions in plain English. Get instant SQL answers.**")
st.markdown(
    """
    _Examples:_  
    • “List all employees in the Engineering department.”  
    • “What is the average salary?”  
    • “Show all records with salary above 80000.”  
    """
)

# ---------- INPUT ----------
question = st.text_input("🔎 Enter your question:", placeholder="e.g. Show all departments")

submit = st.button("🚀 Generate & Run Query")

# ---------- LOGIC ----------
if submit:
    # Step 1: Get SQL from Groq
    generated_sql = get_groq_response(question, prompt)

    st.markdown("### 💬 Generated SQL Query")
    st.code(generated_sql, language="sql")

    # Step 2: Validate and run
    if generated_sql == "ERROR":
        st.error("❌ Failed to get response from Groq API.")
    elif "SELECT" not in generated_sql.upper():
        st.warning("⚠️ The output doesn't appear to be a valid SELECT query.")
    else:
        result = read_sql_query(generated_sql, "employee.db")

        if isinstance(result, str) and result.startswith("SQL ERROR"):
            st.error(f"❌ {result}")
        elif len(result) == 0:
            st.info("ℹ️ Query executed, but no matching records found.")
        else:
            st.markdown("### 📊 Query Results")
            st.dataframe(result, use_container_width=True)
