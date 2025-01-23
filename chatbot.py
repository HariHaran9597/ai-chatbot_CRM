import google.generativeai as genai

# Set your Gemini API key
genai.configure(api_key="AIzaSyCJ6_fGefmrYKy7_oRfgJVLQxfZaWB1hcM")

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-pro')

# Simulated order data
order_data = {
    "krismarrier@noemail.invalid": {
        "order_id": "12345",
        "status": "Shipped",
        "estimated_delivery": "2023-11-05"
    },
    "sage-wieser@noemail.invalid": {
        "order_id": "67890",
        "status": "Processing",
        "estimated_delivery": "2023-11-10"
    }
}

def chatbot(prompt, email):
    # Check if the email has an associated order
    if email in order_data:
        order_info = order_data[email]
        response = f"Your order (ID: {order_info['order_id']}) is currently {order_info['status']}. Estimated delivery is {order_info['estimated_delivery']}."
    else:
        response = "I couldn't find any order associated with your email. Please contact customer service for further assistance."

    return response

# Test the chatbot
if __name__ == "__main__":
    while True:
        email = input("Enter your email: ")
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        response = chatbot(user_input, email)
        print(f"Bot: {response}")