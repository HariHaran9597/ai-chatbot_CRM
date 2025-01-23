from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import requests
from datetime import datetime

app = Flask(__name__)

# Support ticket storage (in-memory for demo - in production use a database)
tickets = {}
ticket_counter = 0

# Set your Gemini API key
genai.configure(api_key="AIzaSyCJ6_fGefmrYKy7_oRfgJVLQxfZaWB1hcM")

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-pro')

# Zoho CRM API credentials
ZOHO_ACCESS_TOKEN = "1000.da65bb6b3952f621c506f585e1e245f8.648dbba08985bea42a9592b524f6bead"  # Replace with your Access Token
ZOHO_CRM_URL = "https://www.zohoapis.com/crm/v2"

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

# Root route to serve the HTML form
@app.route("/")
def home():
    return render_template("index.html")

# Chat route to handle chatbot requests
@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    email = request.json.get("email")  # Get email from the frontend

    # Fetch customer data from Zoho CRM
    customer_info = get_customer_info(email)
    if customer_info:
        user_input_with_context = f"Customer Info: {customer_info}\n\nUser: {user_input}"
    else:
        user_input_with_context = user_input

    print(f"Debug - Customer info before chatbot call: {customer_info}")  # Debug line
    # Get chatbot response with customer info
    response = chatbot(user_input, email, customer_info)  # Pass customer_info to chatbot

    # Log the interaction in Zoho CRM
    log_interaction(email, user_input, response)

    return jsonify({"response": response})

# Function to fetch customer info from Zoho CRM
def get_customer_info(email):
    # For testing purposes, return hardcoded data for the test email
    if email == "krismarrier@noemail.invalid":
        print("Debug - Returning hardcoded customer info")  # Debug line
        return {
            "name": "Kris Marrier",
            "email": "krismarrier@noemail.invalid",
            "phone": "555-555-5555"
        }

    try:
        headers = {
            "Authorization": f"Zoho-oauthtoken {ZOHO_ACCESS_TOKEN}"
        }
        print(f"Fetching customer info for email: {email}")  # Debugging
        response = requests.get(
            f"{ZOHO_CRM_URL}/Contacts/search?email={email}",
            headers=headers
        )
        print(f"Response status code: {response.status_code}")  # Debugging
        print(f"Response data: {response.json()}")  # Debugging
        if response.status_code == 200:
            data = response.json()
            if data.get("data"):
                contact = data["data"][0]
                return {
                    "name": f"{contact['First_Name']} {contact['Last_Name']}",
                    "email": contact['Email'],
                    "phone": contact.get('Phone', 'N/A'),
                }
        return None
    except Exception as e:
        print(f"Error fetching customer info: {e}")
        return None

# Function to log interactions in Zoho CRM
def log_interaction(email, user_input, bot_response):
    try:
        headers = {
            "Authorization": f"Zoho-oauthtoken {ZOHO_ACCESS_TOKEN}"
        }
        note = f"Chatbot Interaction:\n\nUser: {user_input}\nBot: {bot_response}"
        data = {
            "data": [
                {
                    "Note_Title": "Chatbot Interaction",
                    "Note_Content": note,
                    "Parent_Id": email,  # Associate with the contact
                    "se_module": "Contacts"
                }
            ]
        }
        response = requests.post(
            f"{ZOHO_CRM_URL}/Notes",
            headers=headers,
            json=data
        )
        if response.status_code != 201:
            print(f"Error logging interaction: {response.text}")
    except Exception as e:
        print(f"Error logging interaction: {e}")

# Function to handle chatbot logic
def chatbot(prompt, email, customer_info):
    print(f"Debug - Inside chatbot function - customer_info: {customer_info}")  # Debug line
    
    # Format customer info
    customer_details = ""
    if customer_info:
        customer_details = f"""Customer Info:
Name: {customer_info['name']}
Email: {customer_info['email']}
Phone: {customer_info['phone']}

"""
        print(f"Debug - Formatted customer details: {customer_details}")  # Debug line
    
    # Look for ticket-related keywords
    prompt_lower = prompt.lower()
    if any(word in prompt_lower for word in ['ticket', 'support', 'issue', 'problem', 'help']):
        # Check if user has any tickets
        user_tickets = [t for t in tickets.items() if t[1]['email'] == email]
        if user_tickets:
            ticket_list = "\n".join([f"Ticket {tid}: {t['subject']} (Status: {t['status']})"
                                   for tid, t in user_tickets])
            response = f"{customer_details}Here are your support tickets:\n\n{ticket_list}"
        else:
            response = f"{customer_details}You don't have any support tickets. Would you like to create one?"
    
    # Check for order-related queries
    elif email in order_data:
        order_info = order_data[email]
        response = f"{customer_details}Your order (ID: {order_info['order_id']}) is currently {order_info['status']}.\nEstimated delivery is {order_info['estimated_delivery']}."
    else:
        response = f"{customer_details}I couldn't find any order associated with your email. Please contact customer service for further assistance."

    return response

# Ticket creation endpoint
@app.route("/create_ticket", methods=["POST"])
def create_ticket():
    global ticket_counter
    try:
        data = request.json
        subject = data.get('subject')
        description = data.get('description')
        email = data.get('email')

        if not all([subject, description, email]):
            return jsonify({"error": "Missing required fields"}), 400

        ticket_counter += 1
        ticket_id = f"TICKET-{ticket_counter}"
        
        # Store ticket
        tickets[ticket_id] = {
            "subject": subject,
            "description": description,
            "email": email,
            "status": "Open",
            "created_at": datetime.now().isoformat()
        }

        # Log ticket creation in Zoho CRM
        log_interaction(email, f"Created support ticket: {subject}",
                       f"Ticket ID: {ticket_id}\nDescription: {description}")

        return jsonify({
            "message": "Ticket created successfully",
            "ticket_id": ticket_id
        }), 201

    except Exception as e:
        print(f"Error creating ticket: {e}")
        return jsonify({"error": "Failed to create ticket"}), 500

# Get ticket status
@app.route("/ticket_status/<ticket_id>", methods=["GET"])
def get_ticket_status(ticket_id):
    if ticket_id in tickets:
        return jsonify(tickets[ticket_id]), 200
    return jsonify({"error": "Ticket not found"}), 404

if __name__ == "__main__":
    app.run(debug=True)