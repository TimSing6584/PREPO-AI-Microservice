def build_scoring_prompt(transcript: str, statement: str, model_answer: str) -> dict:
    return {
        "system": (
            "You are a strict but fair technical interview evaluator. "
            "Always address the candidate directly using 'you' and 'your', "
            "never refer to them as 'the student'. "
            "Be concise and specific in your feedback. "
            "IMPORTANT: Only evaluate the candidate's answer against the model answer provided. "
            "Do NOT suggest improvements for concepts not in the model answer. "
            "If the candidate covers all concepts in the model answer score them 95-100. "
            "If the candidate misses more than half the key concepts score below 50. "
        ),
        "user": (
            f"Evaluate this interview answer.\n\n"
            f"Question: {statement}\n\n"
            f"Model answer: {model_answer}\n\n"
            f"Candidate's answer: {transcript}\n\n"
            "Return ONLY a raw JSON object, no markdown, no extra text:\n"
            '{{\n'
            '    "score": <number 0-100>,\n'
            '    "feedback": "<2-3 sentences addressing the candidate directly, state what the candidate got right and what he/she missed>"\n'
            '}}'
        )
    }