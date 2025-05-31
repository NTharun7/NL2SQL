import sys
import ollama
import psycopg2

# === PostgreSQL Connection Details ===
DB_NAME = "sers"
DB_USER = ""
DB_PASSWORD = ""
DB_HOST = "localho"
DB_PORT = "5432"

# === Generate SQL from Natural Language Query ===
def generate_sql(natural_language_query):
    prompt = f"""
You are a PostgreSQL SQL generator. Convert the following natural language query into a valid SQL query.

Only use this table: `users` with columns:
- id (SERIAL)
- name (TEXT)
- item (TEXT)
- quantity (INTEGER)
- amount (NUMERIC)
- city (TEXT)
- date (DATE)

❌ Do NOT use or mention: created_at, timestamp, signup_date, transactions, etc.
✅ Use only the 'users' table and its columns.
✅ Return only the raw SQL query (no markdown, no explanations).
✅ Query must include 'FROM users'.

Query: {natural_language_query}
"""

    response = ollama.chat(
        model="llama3",
        messages=[{"role": "user", "content": prompt}]
    )

    content = response["message"]["content"].strip()

    # Filter valid SQL
    for line in content.splitlines():
        line = line.strip().rstrip(";")
        if line.lower().startswith("select") and "from users" in line.lower():
            return line + ";"


    

# === Execute SQL and Print Results ===
def execute_sql(query):
    try:
        # Basic safety checks
        if "from users" not in query.lower():
            print("❌ Invalid SQL: missing 'FROM users'.")
            return

        forbidden = ["transactions", "created_at", "timestamp", "signup_date"]
        if any(bad in query.lower() for bad in forbidden):
            print("❌ Invalid SQL: Detected unsupported column or table.")
            print("💡 Only the 'users' table and listed columns are allowed.")
            return

        # Connect and execute
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
        )
        cursor = conn.cursor()
        cursor.execute(query)

        query_type = query.strip().split()[0].lower()

        if query_type == "select":
            col_names = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()
            conn.close()

            if results:
                print("\n📊 Query Results:")
                print(" | ".join(col_names))
                print("-" * 50)
                for row in results:
                    print(" | ".join(str(value) for value in row))
            else:
                print("✅ Query executed, but no rows returned.")
        else:
            conn.commit()
            conn.close()
            print(f"✅ {query_type.capitalize()} query executed successfully.")

    except Exception as e:
        print("❌ Error:", str(e))

# === Main Entry Point ===
if __name__ == "__main__":
    if len(sys.argv) > 1:
        nl_query = " ".join(sys.argv[1:])
    else:
        nl_query = input("\n💬 Enter your natural language query: ")

    sql_query = generate_sql(nl_query)

    print("\n🧠 Generated SQL Query:")
    print(sql_query)

    print("\n🚀 Executing SQL Query...")
    execute_sql(sql_query)
