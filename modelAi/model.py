import ollama

def ModelAi_Response(query) :

    response = ollama.chat(
        model='gemma3:12b',
        messages=[
            {'role': 'system', 'content': "You are a Teacher and Answer in Thai language, And don't reply with emojis." },
            {'role': 'user', 'content': query}
        ]
    )

    response_text = response['message']['content']

    return response_text


def ModelAi_Topic_Chat(query) :

    response = ollama.chat(
        model='llama3.2',
        messages=[
            {
                'role': 'system', 
                'content': "You are a helpful assistant and Answer in Thai language. คำถามนี้พูดถึงเรื่องอะไร โดยไม่ต้องมี *" 
            },
            {'role': 'user', 'content': query}
        ]
    )

    response_text = response['message']['content']

    return response_text