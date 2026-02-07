def get_sql_prompt(
    question: str,
    table_schema: str,
    initial_prompt: str | None = None,
    few_shots: list = [],
    dialect: str = "PostgreSQL",
    **kwargs,
):
    """Example:

    ```python
    get_sql_prompt(
        question="What are the top 10 customers by sales?",
        few_shots=[{"question": "What are the top 10 customers by sales?", "sql": "SELECT * FROM customers ORDER BY sales DESC LIMIT 10"}],
        table_schema="[{'name':'orders','measures':[{'name':'orders.count','type':'number'},{'name':'orders.number','type':'number'}],'dimensions':[{'name':'orders.id','type':'number'}]]",
    ).

    ```

    This method is used to generate a prompt for the LLM to generate SQL.

    Args:
        initial_prompt (str): The initial prompt for the LLM.
        question (str): The question to generate SQL for.
        few_shots (list): A list of questions and their corresponding SQL statements.
        table_schema (list): A list of DDL statements.
        dialect (str): The SQL dialect to use.
        kwargs: Additional keyword arguments.

    Returns:
        any: The prompt for the LLM to generate SQL.
    """

    if initial_prompt is None:
        initial_prompt = f"You are a {dialect} expert. Please help to generate a SQL query to answer the question. Your response should ONLY be based on the given context and follow the response guidelines and format instructions. "

    # add table schema to prompt
    initial_prompt += f"===Table Schema===\n{table_schema}\n\n"

    # add response guidelines to prompt
    initial_prompt += (
        "===Response Guidelines \n"
        "1. CRITICAL: You MUST generate a valid SQL query. Do NOT return explanations or error messages. \n"
        "2. CRITICAL: Do NOT query information_schema or system catalogs. Use the provided table schema above. \n"
        "3. If the provided context is sufficient, please generate a valid SQL query without any explanations for the question. \n"
        "4. If you're unsure about column names, make educated guesses based on the schema provided (e.g., if you see a 'region' column, use it). \n"
        "5. Please use the most relevant table(s) from the schema provided above. \n"
        "6. If the question has been asked and answered before, please repeat the answer exactly as it was given before. \n"
        f"7. Ensure that the output SQL is {dialect}-compliant and executable, and free of syntax errors. \n"
        "8. Your response should contain ONLY the SQL query, nothing else. \n"
        "9. For TOP N queries, use ORDER BY and LIMIT clauses. \n"
    )

    messages = [
        {
            "role": "system",
            "content": initial_prompt,
        }
    ]

    # add few shots to prompt
    for shot in few_shots:
        if shot is not None:
            if "question" in shot and "sql" in shot:
                messages.append(
                    {
                        "role": "user",
                        "content": shot["question"],
                    }
                )

                messages.append(
                    {
                        "role": "assistant",
                        "content": shot["sql"],
                    }
                )

    messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    return messages


def get_correction_prompt(
    question: str,
    wrong_sql: str,
    error_message: str,
    table_schema: str,
    dialect: str = "PostgreSQL",
) -> list[dict]:
    """
    Generate prompt for SQL correction.

    Args:
        question: The original question.
        wrong_sql: The failed SQL query.
        error_message: The error message from the database.
        table_schema: The table schema.
        dialect: The SQL dialect.

    Returns:
        list[dict]: The messages for the LLM.
    """
    system_prompt = (
        f"You are a {dialect} expert. Fix the failed SQL query below. \n"
        f"===Table Schema===\n{table_schema}\n\n"
        "===Instructions===\n"
        "1. Fix the error while maintaining the original intent.\n"
        f"2. Use valid {dialect} syntax.\n"
        "3. Output ONLY the corrected SQL query. No explanation.\n"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user", 
            "content": f"Question: {question}\nFailed SQL: {wrong_sql}\nError: {error_message}"
        }
    ]
    return messages
