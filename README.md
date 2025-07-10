# 🧠 Talk2Data — Natural Language to SQL App
Ask questions in plain English. Get instant SQL answers. 

Talk2Data is a smart and user-friendly web application that lets you ask questions in plain English and get **instant SQL answers** from your database. It’s powered by **Groq API** and **Streamlit**, and perfect for non-technical users like HRs or analysts who want insights without writing SQL manually.

---

## 🔍 Problem Statement

In many organizations, HR and business teams often need quick access to employee data (e.g., salary, department distribution, etc.) but lack SQL expertise. Talk2Data solves this by converting natural language queries into accurate SQL queries and displaying the results instantly — no coding required!

---

## 🚀 Features

- ✍️ Ask questions in plain English (e.g., "What is the average salary by department?")
- 🔄 Converts your input to SQL using Groq's LLM
- 📊 Executes query on a local SQLite database
- 📋 Displays clean, tabular results with proper column names
- 🖥️ Built with Streamlit (easy to deploy or run locally)

---

## 🧱 Tech Stack

- [Python](https://www.python.org/)
- [Streamlit](https://streamlit.io/)
- [Groq API (LLM)](https://console.groq.com/)
- [SQLite3](https://www.sqlite.org/index.html)
- [Pandas](https://pandas.pydata.org/)

## 🖼️ Demo

<img width="1009" height="893" alt="Screenshot 2025-07-10 135132" src="https://github.com/user-attachments/assets/166603d0-a992-46f6-a50d-4890efc2f68a" />

<img width="969" height="832" alt="Screenshot 2025-07-10 135216" src="https://github.com/user-attachments/assets/8d96a2b4-9a3c-4e3d-ad30-5541a04c42d0" />

## 🤖 How It Works
- User asks a question in plain English.
- The app sends the question + prompt to Groq's LLM.
- Groq returns a pure SQL SELECT query.
- The query is run against a local SQLite database.
- Results are displayed with pandas + Streamlit UI.



