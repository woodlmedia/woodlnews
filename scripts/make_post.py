import os
from huggingface_hub import InferenceClient # Ensure this is imported
# from openai import OpenAI # Not needed if using InferenceClient like this

# Get the model ID from the environment variable
HF_MODEL_ID = os.environ.get("HF_MODEL")
# Get your Hugging Face token (which we'll try as the api_key for the provider)
HF_API_TOKEN = os.environ.get("HF_TOKEN")

if not HF_MODEL_ID:
    raise ValueError("HF_MODEL environment variable not set (e.g., Qwen/Qwen3-30B-A3B).")
if not HF_API_TOKEN:
    raise ValueError("HF_TOKEN environment variable not set (your Hugging Face API token).")

# Initialize the client to use the "novita" provider
# We are trying to use your HF_TOKEN as the api_key here.
# If this causes authentication errors with novita,
# you may need a specific API key from novita.ai.
print("Attempting to initialize InferenceClient with provider 'novita'.")
try:
    client = InferenceClient(
        provider="novita",
        api_key=HF_API_TOKEN  # Using your HF_TOKEN here
    )
    print("InferenceClient initialized successfully with provider 'novita'.")
except Exception as e:
    print(f"Error initializing InferenceClient with provider 'novita': {e}")
    # Consider re-raising the exception or handling it as a fatal error for the script
    raise

def ask_llm(title: str, summary: str, feed_content: str):
    # This prompt engineering is crucial.
    # For a chat model, you might structure it as a conversation.
    # You can have a system message to set the context/role of the AI.
    # And then a user message with the specific request.

    system_prompt = "You are a helpful assistant that creates engaging social media posts based on news articles."
    user_prompt = (
        f"Please generate a concise and engaging social media post (e.g., for Twitter/X or a short blog update) "
        f"based on the following article details:\n"
        f"Title: {title}\n"
        f"Summary: {summary}\n"
        f"Key Content Snippet: \"{feed_content[:500]}...\"" # Limit length if too long
        f"\nThe post should be suitable for a general audience and encourage engagement."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    print(f"Attempting chat completion with model: {HF_MODEL_ID} via novita provider.")
    print(f"Messages being sent: {messages}")

    try:
        completion = client.chat.completions.create(
            model=HF_MODEL_ID,  # This now correctly refers to your chosen model like Qwen/Qwen3-30B-A3B
            messages=messages,
            max_tokens=150  # Adjust as needed, max_tokens for the completion itself
            # temperature=0.7 # Optional: for creativity. 0.0 for more deterministic
        )
        # The response structure might vary slightly by provider, but this is typical for OpenAI-like APIs
        generated_text = completion.choices[0].message.content
        print("Successfully received response from LLM via novita.")
        return generated_text.strip()
    except Exception as e:
        print(f"Error calling chat completions API with model {HF_MODEL_ID} via novita: {e}")
        # To see more details about the error from the provider:
        # import traceback
        # print(traceback.format_exc())
        # if hasattr(e, 'response') and e.response is not None:
        #     try:
        #         print(f"Error details: {e.response.json()}")
        #     except: # noqa E722
        #         print(f"Error details (text): {e.response.text}")
        return None

# Example of how you might call it (ensure this is integrated into your main script logic)
# if __name__ == "__main__":
#     # This is for testing; your main script will get these from the feed
#     test_title = "New AI Discovery"
#     test_summary = "Scientists have found a new way for AI to learn."
#     test_content = "The AI model, named Cerebras-GPT by a team of researchers, has shown remarkable ability in understanding complex patterns..."
#     post = ask_llm(test_title, test_summary, test_content)
#     if post:
#         print("\nGenerated Post:")
#         print(post)
#     else:
#         print("\nFailed to generate post.")
