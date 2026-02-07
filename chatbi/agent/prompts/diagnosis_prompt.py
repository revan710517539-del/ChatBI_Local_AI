import dspy

class DiagnosisSignature(dspy.Signature):
    """
    Generate natural language insights from SQL query results.
    """
    
    question = dspy.InputField(desc="The user's original question")
    sql = dspy.InputField(desc="The executed SQL query")
    data_sample = dspy.InputField(desc="Sample of the data returned (up to 20 rows)")
    
    summary = dspy.OutputField(desc="A concise summary of the data findings (2-3 sentences)")
    key_points = dspy.OutputField(desc="List of key observations or trends (3-5 bullet points)")

def get_diagnosis_prompt(
    question: str,
    sql: str,
    data_sample: str,
    language: str = "English",
) -> list[dict]:
    """
    Generate prompt for data diagnosis.
    """
    system_prompt = (
        f"You are a Data Analyst expert. Your task is to analyze the provided data sample for the given question and SQL.\n"
        f"Language: {language}\n"
        "===Response Guidelines===\n"
        "1. Provide a clear, concise summary of the answer.\n"
        "2. Identify key trends, anomalies, or interesting facts.\n"
        "3. Focus on business value and insights, not just describing the numbers.\n"
        "4. Do NOT verify the SQL correctness, assume the data is correct.\n"
        "5. Output must be a valid JSON object with 'summary' and 'key_points' fields.\n"
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"Question: {question}\nSQL: {sql}\nData Sample:\n{data_sample}"
        }
    ]
    return messages
