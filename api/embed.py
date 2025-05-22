import openai


def embed_text(text: str):
    # Use OpenAI to get the embedding vector
    response = openai.Embedding.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response['data'][0]['embedding']