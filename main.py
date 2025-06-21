import os
import sqlite3
import streamlit as st

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

#  SQLite query executor
def read_sql_query(sql, db_path="candidates.db"):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        conn.commit()
        conn.close()
        return rows
    except Exception as e:
        return [("❌ Error executing SQL:", str(e))]

#  Streamlit UI
st.set_page_config(page_title="Groq SQL Assistant")
st.header("🔍 VigiloAI")

#  User inputs Groq API Key
api_key = st.text_input("Enter your Groq API Key", type="password")

#  User inputs question
user_question = st.text_input("Ask your Query:")

#  Only proceed if both are entered
if api_key and user_question and st.button("Submit"):
    try:
        os.environ["GROQ_API_KEY"] = api_key  # Set key dynamically

        # 🔗 Define the prompt
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """
            You are an expert at translating natural language questions into precise SQL queries!

            The SQL database has the table name `candidates` and contains the following columns:
            SrNo, Name, ID, DOB, Category, Subject, Center, Year.

            Examples:
            - "How many records are available in the table?"  
            → SELECT COUNT(*) FROM candidates;

            - "List all candidates whose Category is 'OBC'"  
            → SELECT * FROM candidates WHERE Category = "OBC";
                        
            - "How many candidates are there whose id starts from RJUD and dob of 1965"  
            → SELECT COUNT(*) FROM candidates 
                WHERE ID LIKE 'RJUD%' 
                AND DOB LIKE '%1965';

            Important rules:
            - Do NOT include ``` or the word "sql" in the output.
            - Only output clean, executable SQL query.
"""),
            ("user", "{question}")
        ])

        #  Create the chain
        llm = ChatGroq(model_name="gemma2-9b-it", temperature=0)
        sql_chain = prompt_template | llm | StrOutputParser()

        #  Invoke the model
        with st.spinner("Generating SQL query..."):
            sql_query = sql_chain.invoke({"question": user_question})
            st.code(sql_query, language="sql")

            #  Run query
            result = read_sql_query(sql_query)
            st.subheader("🗂️ Query Result:")
            for row in result:
                st.markdown(f"<p style='font-size:80px; color:green'>{row}</p>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

