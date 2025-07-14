from ollama import ChatResponse, chat


def large_language_model(prompt: str):
    res: ChatResponse=chat(model='llama3.2', messages=[
        {
            "role": "system",
            "content": "you are male"
        },
        {
            "role": "user",
            "content": prompt
        }
    ])

    return res.message.content