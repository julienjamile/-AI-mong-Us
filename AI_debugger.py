from google import genai
from google.genai import types

def test_api_key(api_key):
    try:
        # Initialize client
        client = genai.Client(api_key=api_key)

        # Simple test prompt
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Say 'API key is working' if you can read this."
        )

        print("✅ SUCCESS!")
        print("Response:", response.text)

    except Exception as e:
        print("❌ ERROR:")
        print(type(e).__name__, "-", e)


if __name__ == "__main__":
    api_key = input("Enter your API key: ").strip()
    test_api_key(api_key)