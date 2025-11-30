from dotenv import load_dotenv
load_dotenv()  # Load environment variables

import streamlit as st
import os
import sqlite3
import openai
import re
import pandas as pd

# ✅ Define all functions first
def get_all_tables_and_columns(db):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    # Get all tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    
    # Get columns for each table
    table_info = {}
    for (table,) in tables:
        cur.execute(f"PRAGMA table_info({table});")
        columns = [row[1] for row in cur.fetchall()]
        table_info[table] = columns
    
    conn.close()
    return table_info

def get_column_names(db, table):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table});")
    columns = [row[1] for row in cur.fetchall()]
    conn.close()
    return columns

def extract_table_name(question, db):
    # Get all table names
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cur.fetchall()]
    conn.close()
    # Try to find a table name in the question
    for table in tables:
        pattern = re.compile(rf"\b{table}\b", re.IGNORECASE)
        if pattern.search(question):
            return table
    return tables[0] if tables else None

def detect_sql_operation(question):
    ops = ["SELECT", "INSERT", "UPDATE", "DELETE","CREATE", "ALTER", "DROP","DESCRIBE"]
    for op in ops:
        if re.search(rf"\b{op}\b", question, re.IGNORECASE):
            return op
    # Fallback: guess based on keywords
    if re.search(r"show|list|find|display|count|average|sum", question, re.IGNORECASE):
        return "SELECT"
    return None

def run_sql(sql, db, op):
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        if op == "SELECT":
            cur.execute(sql)
            rows = cur.fetchall()
            column_names = [description[0] for description in cur.description]
            conn.close()
            df = pd.DataFrame(rows, columns=column_names)
            return df
        else:
            cur.execute(sql)
            conn.commit()
            affected = cur.rowcount
            conn.close()
            return f"Success! Rows affected: {affected}"
    except Exception as e:
        return f"SQL ERROR: {e}"

# ✅ Configure Groq (OpenAI-compatible) API
openai.api_key = os.getenv("GROQ_API_KEY")
openai.api_base = "https://api.groq.com/openai/v1"

# ✅ Use Groq to convert English to SQL
def get_groq_response(question, prompt):
    try:
        full_prompt = f"{prompt[0]}\n\nQuestion: {question}"
        response = openai.ChatCompletion.create(
            model="llama-3.3-70b-versatile",  # You can try "mixtral-8x7b-32768" too
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


# ✅ Prompt template with examples for all operations
prompt = [
    """
    You are an expert in converting English questions to SQL queries! Generate SQL queries based on the operation requested.

    Examples for different operations:
    
    SELECT and JOIN examples:
    - "Show me all employees" → SELECT * FROM {table};
    - "Find employees in Sales department" → SELECT * FROM {table} WHERE DEPARTMENT = 'Sales';
    - "What is the average salary?" → SELECT AVG(SALARY) FROM {table};
    - "Show all employees with their department details" → 
      SELECT e.*, d.LOCATION, d.HEAD 
      FROM EMPLOYEE e 
      JOIN DEPARTMENTS d ON e.DEPARTMENT = d.NAME;
    - "List all departments with employee count" →
      SELECT d.NAME, d.LOCATION, COUNT(e.NAME) as EMPLOYEE_COUNT 
      FROM DEPARTMENTS d 
      LEFT JOIN EMPLOYEE e ON d.NAME = e.DEPARTMENT 
      GROUP BY d.NAME, d.LOCATION;
    - "Find employees with their projects" →
      SELECT e.NAME, e.DEPARTMENT, p.PROJECT_NAME 
      FROM EMPLOYEE e 
      LEFT JOIN EMPLOYEE_PROJECTS ep ON e.NAME = ep.EMPLOYEE_NAME 
      LEFT JOIN PROJECTS p ON ep.PROJECT_ID = p.ID;
    
    INSERT examples:
    - "Add a new employee John in Engineering with salary 75000" → INSERT INTO {table} (NAME, DEPARTMENT, SALARY) VALUES ('John', 'Engineering', 75000);
    - "Create employee record for Sarah in HR" → INSERT INTO {table} (NAME, DEPARTMENT) VALUES ('Sarah', 'HR');
    
    UPDATE examples:
    - "Change John's salary to 80000" → UPDATE {table} SET SALARY = 80000 WHERE NAME = 'John';
    - "Update department to Marketing for employee Sarah" → UPDATE {table} SET DEPARTMENT = 'Marketing' WHERE NAME = 'Sarah';
    
    DELETE examples:
    - "Remove employee John" → DELETE FROM {table} WHERE NAME = 'John';
    - "Delete all employees with salary below 50000" → DELETE FROM {table} WHERE SALARY < 50000;

    CREATE examples:
    - "Create a new table called PROJECTS" → 
      CREATE TABLE PROJECTS (
          ID INTEGER PRIMARY KEY,
          NAME TEXT,
          STATUS TEXT
      );
    - "Create an index on the NAME column" → CREATE INDEX idx_name ON {table}(NAME);
    - "Create a unique index on EMAIL" → CREATE UNIQUE INDEX idx_email ON {table}(EMAIL);
    - "Create a view of high salary employees" → CREATE VIEW high_salary AS SELECT * FROM {table} WHERE SALARY > 80000;
    
    ALTER TABLE examples:
    - "Add a column END_DATE" → ALTER TABLE {table} ADD COLUMN END_DATE DATE;
    - "Add a foreign key constraint" → ALTER TABLE {table} ADD CONSTRAINT fk_dept FOREIGN KEY (DEPARTMENT) REFERENCES DEPARTMENTS(ID);
    - "Drop the STATUS column" → ALTER TABLE {table} DROP COLUMN STATUS;
    - "Add a unique constraint on EMAIL" → ALTER TABLE {table} ADD CONSTRAINT unq_email UNIQUE (EMAIL);

    DROP examples:
    - "Drop the PROJECTS table" → DROP TABLE IF EXISTS PROJECTS;
    - "Remove the index on NAME" → DROP INDEX IF EXISTS idx_name;
    - "Drop the high salary view" → DROP VIEW IF EXISTS high_salary;

    TRUNCATE example:
    - "Clear all data from EMPLOYEES" → DELETE FROM {table};  -- SQLite doesn't support TRUNCATE, using DELETE instead

    DESCRIBE examples:
    - "Show the structure of EMPLOYEES" → PRAGMA table_info({table});
    - "List all columns in PROJECTS" → PRAGMA table_info(PROJECTS);

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

import glob

# ---------- HEADER ----------
st.title("🧠 Talk2Data")
st.caption("**Ask questions in plain English. Get instant SQL answers.**")

# ---------- DYNAMIC DB & TABLE SELECTION ----------
db_files = glob.glob("*.db")
selected_db = st.selectbox("Select database:", db_files, index=0)

def extract_table_name(question, db):
    # Get all table names
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cur.fetchall()]
    conn.close()
    # Try to find a table name in the question
    for table in tables:
        pattern = re.compile(rf"\\b{table}\\b", re.IGNORECASE)
        if pattern.search(question):
            return table
    return tables[0] if tables else None

selected_table = None
column_names = []

# ---------- OPERATION & INPUT ----------
def detect_sql_operation(question):
    # DML Operations with JOIN support
    if re.search(r"\b(JOIN|COMBINE|MERGE|RELATED)\b", question, re.IGNORECASE):
        return "JOIN"
    elif re.search(r"\b(SELECT|FIND|SHOW|LIST|GET|DISPLAY|COUNT|AVERAGE|SUM)\b", question, re.IGNORECASE):
        return "SELECT"
    elif re.search(r"\b(INSERT|ADD|CREATE\s+(?:NEW )?(?:RECORD|ROW|ENTRY))\b", question, re.IGNORECASE):
        return "INSERT"
    elif re.search(r"\b(UPDATE|MODIFY|CHANGE|SET)\b", question, re.IGNORECASE):
        return "UPDATE"
    elif re.search(r"\b(DELETE|REMOVE|DROP\s+(?:RECORD|ROW|ENTRY))\b", question, re.IGNORECASE):
        return "DELETE"
    # DDL Operations
    elif re.search(r"\b(CREATE\s+(?:TABLE|DATABASE|INDEX|VIEW)|CREATE\s+(?:A\s+)?(?:NEW\s+)?TABLE)\b", question, re.IGNORECASE):
        return "CREATE"
    elif re.search(r"\b(ALTER\s+TABLE|MODIFY\s+TABLE|ADD\s+(?:COLUMN|CONSTRAINT|INDEX)|DROP\s+(?:COLUMN|CONSTRAINT|INDEX)|CHANGE\s+COLUMN)\b", question, re.IGNORECASE):
        return "ALTER"
    elif re.search(r"\b(DROP\s+(?:TABLE|DATABASE|INDEX|VIEW))\b", question, re.IGNORECASE):
        return "DROP"
    elif re.search(r"\b(TRUNCATE|CLEAR|EMPTY)\b", question, re.IGNORECASE):
        return "TRUNCATE"
    elif re.search(r"\b(DESCRIBE|SHOW\s+(?:COLUMNS|STRUCTURE))\b", question, re.IGNORECASE):
        return "DESCRIBE"
    return None

question = st.text_input("🔎 Enter your question:", placeholder="e.g. Show employees with their departments, List all departments with employee count")
submit = st.button("🚀 Generate & Run Query")

selected_table = extract_table_name(question, selected_db) if question else None
operation = detect_sql_operation(question) if question else None
column_names = get_column_names(selected_db, selected_table) if selected_table else []

if selected_table:
    st.markdown(
        f"""
        _Detected table:_ **{selected_table}**  
        _Columns:_ {', '.join(column_names)}
        """
    )
if operation:
    st.markdown(f"_Detected operation:_ **{operation}**")

# Get all tables and columns information
table_info = get_all_tables_and_columns(selected_db)
tables_description = "\n".join([f"Table '{table}' columns: {', '.join(columns)}" for table, columns in table_info.items()])

prompt = [
    f"""
    You are an expert in converting English questions to SQL queries!
    
    Available tables and their columns in the database:
    {tables_description}

    {f"Selected table: {selected_table}" if selected_table else ""}
    {f"Operation: {operation}" if operation else ""}

    Only return valid SQL queries for the requested operation. Do not include the word 'SQL' or use backticks (```). The output should be only the SQL query.
    """
] if operation else ["No operation detected."]


# ---------- LOGIC ----------
def run_sql(sql, db, op):
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        if op == "SELECT":
            cur.execute(sql)
            rows = cur.fetchall()
            column_names = [description[0] for description in cur.description]
            conn.close()
            df = pd.DataFrame(rows, columns=column_names)
            return df
        else:
            cur.execute(sql)
            conn.commit()
            affected = cur.rowcount
            conn.close()
            return f"Success! Rows affected: {affected}"
    except Exception as e:
        return f"SQL ERROR: {e}"

def get_column_names(db, table):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table});")
    columns = [row[1] for row in cur.fetchall()]
    conn.close()
    return columns

if submit:
    if not selected_table:
        st.error("❌ Could not detect a table name in your question. Please mention a table name.")
    elif not operation:
        st.error("❌ Could not detect an SQL operation. Please specify one of these operations:\n" + 
                "• DML: SELECT, INSERT, UPDATE, DELETE\n" +
                "• DDL: CREATE TABLE/INDEX/VIEW, ALTER TABLE, DROP, TRUNCATE\n" +
                "• Other: DESCRIBE, JOIN")
    else:
        # Step 1: Get SQL from Groq
        generated_sql = get_groq_response(question, prompt)

        st.markdown("### 💬 Generated SQL Query")
        st.code(generated_sql, language="sql")

        # Step 2: Validate and run
        if generated_sql == "ERROR":
            st.error("❌ Failed to get response from Groq API.")
        elif operation == "SELECT" and "SELECT" not in generated_sql.upper():
            st.warning("⚠️ The output doesn't appear to be a valid SELECT query.")
        else:
            result = run_sql(generated_sql, selected_db, operation)

            if isinstance(result, str) and result.startswith("SQL ERROR"):
                st.error(f"❌ {result}")
            elif operation == "SELECT":
                if len(result) == 0:
                    st.info("ℹ️ Query executed, but no matching records found.")
                else:
                    st.markdown("### 📊 Query Results")
                    st.dataframe(result, use_container_width=True)
            else:
                st.success(result)
