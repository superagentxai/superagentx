from langchain_experimental.sql import SQLDatabaseChain
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

import mysql.connector

template = """Based on the table schema below, write a SQL query that would answer the user's question:
{schema}

Question: {question}
SQL Query:"""
prompt = ChatPromptTemplate.from_template(template)


# Create a connection to the MySQL database
def create_mysql_connection(user: str, password: str, host: str, port: int, database: str):
    return 'mysql+pymysql://{0}:{1}@{2}:{3}/{4}'.format(user, password, host, port, database)
    # return f"mysql://{user}:{password}@{host}:{port}/{database}"


# Initialize the connection
mysql_connection = create_mysql_connection(user='root', password='password', host='localhost', port=3306,
                                           database='employee')


# Create a LangChain SQLDatabase object

db = SQLDatabase.from_uri(mysql_connection)
schema = db.get_table_info()
print(db.dialect)
print(db.get_usable_table_names())
print(schema)

# Initialize a language model
llm = ChatOpenAI(model_name='gpt-4o-2024-08-06')

print(llm)
# Create the LangChain SQLDatabaseChain
db_chain = SQLDatabaseChain(llm=llm, database=db)

# Example Query
query = "Show me how many employees are present"
response = db_chain.invoke(query)

print(response)

# Close the MySQL connection
# mysql_connection.close()
