import streamlit as st
import mysql.connector
import ollama
import pandas as pd

with st.sidebar:
    option = st.selectbox(
        "Select the database from MySQL",
        ("energy", "aircompressor"),
    )

# MySQL connection details
MYSQL_CONFIG = {
    "host": "localhost",         # MySQL host
    "user": "root",              # MySQL username
    "password": "password",      # MySQL password
    "database": option         # MySQL database name
}

# Function to connect to MySQL
def connect_to_mysql():
    connection = mysql.connector.connect(**MYSQL_CONFIG)
    return connection

# Function to fetch the database schema dynamically
def get_mysql_schema(connection):
    schema = ""
    cursor = connection.cursor()
    try:
        cursor.execute("SHOW TABLES;")
        tables = [table[0] for table in cursor.fetchall()]
        for table in tables:
            cursor.execute(f"SHOW CREATE TABLE {table};")
            schema += cursor.fetchone()[1] + "\n"
    except Exception as e:
        st.error(f"Error fetching schema: {e}")
    finally:
        cursor.close()
    return schema

# Function to generate SQL using Ollama
def generate_sql_with_ollama(schema, prompt, context_file=r"D:\GK\sql_context.txt"):
    # Load the context from the file
    try:
        with open(context_file, "r") as file:
            system_message = file.read()
    except FileNotFoundError:
        raise Exception("Context file not found. Ensure the file exists and the path is correct.")
    # Replace placeholders in the context
    system_message = system_message.replace("{{SCHEMA}}", schema).replace("{{PROMPT}}", prompt)
    # Generate SQL query using the modified system message
    response = ollama.generate(
        model="HridaAI/hrida-t2sql-128k:latest",
        system=system_message,
        prompt=prompt
    )
    sql_query = response.get("response")
    return sql_query

# Function to execute SQL query on MySQL
def execute_mysql_query(connection, sql_query):
    cursor = connection.cursor()
    try:
        cursor.execute(sql_query)
        results = cursor.fetchall()
        return results
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return None
    finally:
        cursor.close()

# Streamlit App
def main():
    st.title("MySQL Chatbot with Ollama Local LLM")
    st.write("Ask questions from database and get results!")

    # MySQL Connection
    st.subheader("Connecting to MySQL")
    try:
        mysql_connection = connect_to_mysql()
        st.success("Connected to MySQL database!")
    except Exception as e:
        st.error(f"Failed to connect to MySQL: {e}")
        return

    # Fetch Schema
    schema = get_mysql_schema(mysql_connection)
    with st.sidebar:
        if schema:
            st.text_area("Database Schema", schema, height=200)
        else:
            st.error("Failed to fetch the database schema.")
            return

    # User Query
    st.subheader("Ask a Query")
    user_query = st.text_input("Enter your query:", placeholder="E.g., Get all water consumption of flow meter FIT-1104")

    if st.button("Generate and Execute Query"):
        if user_query.strip():
            # Generate SQL using Ollama
            st.info(f"Generating SQL query for: {user_query}")
            sql_query = generate_sql_with_ollama(schema, user_query)
            st.code(sql_query, language="sql")

            if sql_query:
                # Execute SQL on MySQL
                st.info("Executing query on the database...")
                results = execute_mysql_query(mysql_connection, sql_query)

                if results:
                    st.success("Query executed successfully! Results:")
                    
                    st.table(results)
                else:
                    st.warning("No results or query execution failed.")
            else:
                st.error("Failed to generate SQL from the query.")
        else:
            st.error("Please enter a valid query.")
     
    # Close MySQL connection
    mysql_connection.close()

if __name__ == "__main__":
    main()
