import mysql.connector
import qrcode
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from langchain.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory

# -------------------- CONFIG --------------------
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "Vini@01",
    "database": "canteenai"
}
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = 'vini535353@gmail.com'
SENDER_PASSWORD = 'huci vdiu tvig nvep'  # Use Gmail App Password

# LangChain LLM
llm = Ollama(model="llama3")
memory = ConversationBufferMemory(memory_key="chat_history", input_key="user_input")
prompt_template = PromptTemplate(
    input_variables=["chat_history", "user_input"],
    template="""
You are a helpful canteen assistant. Interact with the user and help them with their order.

Conversation so far:
{chat_history}

User: {user_input}
Assistant:"""
)

conversation = LLMChain(llm=llm, prompt=prompt_template, memory=memory, verbose=False)

def ask_ollama(prompt_text):
    return conversation.invoke({"user_input": prompt_text})["text"].strip()

def get_db_connection():
    try:
        return mysql.connector.connect(**MYSQL_CONFIG)
    except mysql.connector.Error as e:
        print(f"❌ Database connection failed: {e}")
        return None

# -------------------- Student Functions --------------------
def get_student_info_by_id(student_id):
    db = get_db_connection()
    if not db:
        return None
    cursor = db.cursor()
    cursor.execute("SELECT name, phone, email FROM students WHERE id = %s", (student_id,))
    result = cursor.fetchone()
    db.close()
    if result:
        return {"id": student_id, "name": result[0], "phone": result[1], "email": result[2]}
    return None

def insert_new_student(student_id, name, phone, email):
    db = get_db_connection()
    if not db:
        return
    cursor = db.cursor()
    cursor.execute("INSERT INTO students (id, name, phone, email) VALUES (%s, %s, %s, %s)", (student_id, name, phone, email))
    db.commit()
    db.close()

# -------------------- Menu & Order Logic --------------------
def get_menu():
    db = get_db_connection()
    if not db:
        return {}
    cursor = db.cursor()
    cursor.execute("SELECT item_name, price FROM food_items")
    items = cursor.fetchall()
    db.close()
    return {item[0].lower(): item[1] for item in items}

def parse_order(order_text, menu):
    lines = order_text.strip().split("\n")
    items = []
    for line in lines:
        if "," in line:
            item, qty = [x.strip(" *").strip() for x in line.split(",")]
            item_lower = item.lower()
            if item_lower in menu:
                try:
                    items.append((item.title(), int(qty)))
                except ValueError:
                    continue
    return items

def calculate_total(parsed_items, menu):
    total = 0
    for item, qty in parsed_items:
        item_lower = item.lower()  # Ensure case-insensitive matching
        if item_lower in menu:
            total += menu[item_lower] * qty
    return total

def insert_order(student_id, order_items_str, total):
    db = get_db_connection()
    if not db:
        return None
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO orders (student_id, items, total_amount, status)
        VALUES (%s, %s, %s, %s)
    """, (student_id, order_items_str, total, "Pending"))
    order_id = cursor.lastrowid
    db.commit()
    db.close()
    return order_id

def generate_qr_file(order_id, items, total):
    details = f"Order ID: {order_id}\nItems:\n"
    for item, qty in items:
        details += f"- {item} x {qty}\n"
    details += f"Total: ₹{total}"
    qr = qrcode.make(details)
    filename = f"order_{order_id}.png"
    qr.save(filename)
    return filename

def check_stock(item_name, requested_qty):
    db = get_db_connection()
    if not db:
        return False
    cursor = db.cursor()
    cursor.execute("SELECT quantity FROM stock WHERE item_name = %s", (item_name.lower(),))
    result = cursor.fetchone()
    db.close()
    if result and result[0] >= requested_qty:
        return True
    return False

def reduce_stock(parsed_items):
    db = get_db_connection()
    if not db:
        return
    cursor = db.cursor()
    try:
        for item_name, qty in parsed_items:
            cursor.execute("UPDATE stock SET quantity = quantity - %s WHERE item_name = %s", (qty, item_name.lower()))
        db.commit()
    except mysql.connector.Error as e:
        print(f"❌ Failed to update stock: {e}")
        db.rollback()
    finally:
        db.close()

def get_alternative_items(unavailable_items, stock):
    stock_text = "\n".join([f"{row[0]}: {row[1]}" for row in stock.items()])
    unavailable_text = ", ".join(unavailable_items)
    prompt = f"""
Some items are out of stock: {unavailable_text}.
Here is the current stock availability:
{stock_text}

Suggest one or two alternative items that are available and similar.
"""
    return ask_ollama(prompt)

def send_email(to_email, subject, body, qr_file):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with open(qr_file, 'rb') as f:
            qr_img = MIMEImage(f.read())
            qr_img.add_header('Content-Disposition', 'attachment', filename=qr_file)
            msg.attach(qr_img)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email successfully sent to {to_email}")
        print("\n--- Conversation Memory ---")
        print(memory.buffer)
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def handle_availability_query(user_input, menu):
    words = user_input.lower().split()
    for word in words:
        if word in menu:
            return f"✅ Yes, {word.title()} is available!"
    suggest_prompt = f"""
User asked: \"{user_input}\"
Here is the menu: {', '.join(menu.keys())}
If the item is NOT available, suggest one similar in taste/structure.
Format: \"Sorry, we don't have <item>. But you can try <similar_item>!\"
"""
    return ask_ollama(suggest_prompt)

# -------------------- MAIN INTERACTION --------------------
print("🤖 Welcome to Smart Digidara Canteen AI Bot!")
student_id = input("\n📛 Please enter your student ID: ").strip()
student = get_student_info_by_id(student_id)

if not student:
    print("🆕 It looks like you're a new user! Let's register you.")
    name = input("👤 Enter your name: ").strip()
    phone = input("📞 Enter your phone number: ").strip()
    email = input("📧 Enter your email: ").strip()
    insert_new_student(student_id, name, phone, email)
    student = {"id": student_id, "name": name, "phone": phone, "email": email}
    print(f"\n🎉 Welcome {name}! You're now registered in CanteenMate AI.")
else:
    print(f"\n👋 Welcome back, {student['name']}! Nice to see you again.")
    greeting = ask_ollama(f"Student {student['name']} just entered the canteen. Greet them in a friendly tone.")
    print("🤖", greeting)

# --- Menu Display ---
menu = get_menu()
menu_text = "\n".join([f"{item.title()} - ₹{price}" for item, price in menu.items()])
print("\n📋 Menu:\n" + menu_text)

user_input = input("\n🧑 What would you like to order today? ")

parsed_items = []

while True:
    if "available" in user_input.lower():
        availability_msg = handle_availability_query(user_input, menu)
        print("🤖", availability_msg)

    elif any(keyword in user_input.lower() for keyword in ["search", "find", "show", "have", "get"]):
        search_prompt = f"""
You are an AI assistant at a canteen.

User asked: \"{user_input}\"
Here is the menu: {', '.join(menu.keys())}

Check if the user is trying to search or find a specific item (e.g., using words like 'find', 'search', 'get').

Reply with:
- If the item is in the menu: "✅ Yes, we have <item_name>!"
- If not: "❌ Sorry, we don't have that right now."
"""
        search_response = ask_ollama(search_prompt)
        print("🤖", search_response)

    elif any(word in user_input.lower() for word in ["healthy", "vegetarian", "protein", "low calorie"]):
        diet_prompt = f"""
User asked: \"{user_input}\"
Here is the menu: {menu_text}

Based on the query, identify one or two menu items that best fit the dietary preference (e.g., vegetarian, high protein, low calorie).

Output:
"Based on your preference, you might like: <item1>, <item2>. Would you like to order one of these?"
"""
        diet_response = ask_ollama(diet_prompt)
        print("🤖", diet_response)

    else:
        parse_prompt = f"""
Menu:
{menu_text}
User said: \"{user_input}\"
Extract exact quantity and item name from the user's sentence. 
Return only items from the menu with quantities.

Output format:
* Item, Quantity
"""
        parsed_text = ask_ollama(parse_prompt)
        print("\n🤖 Got this order:\n" + parsed_text)

        new_items = parse_order(parsed_text, menu)
        if new_items:
            # Merge items to avoid duplicates
            item_dict = {item: qty for item, qty in parsed_items}  # Current items as dict
            for item, qty in new_items:
                if item in item_dict:
                    item_dict[item] = qty  # Update quantity for existing item
                else:
                    item_dict[item] = qty  # Add new item
            parsed_items = [(item, qty) for item, qty in item_dict.items()]
            print(f"🤖 Updated order: {', '.join([f'{item} x {qty}' for item, qty in parsed_items])}")

            suggest_prompt = f"""
User ordered:
{parsed_text}
From this menu: {menu_text}
Suggest an extra item from the menu that complements their order. 
Explain why in a short friendly message.
End with: 'Would you like to add it?'
"""
            suggestion = ask_ollama(suggest_prompt)
            print("🤖", suggestion)

            user_reply = input("🧑 Your reply: ").strip().lower()
            if "yes" in user_reply or "add" in user_reply:
                matched_items = [item for item in menu.keys() if item in suggestion.lower()]
                if matched_items:
                    final_suggestion = matched_items[-1]  # Take the last matched item
                    # Add or update the suggested item
                    item_dict = {item: qty for item, qty in parsed_items}
                    if final_suggestion.title() in item_dict:
                        item_dict[final_suggestion.title()] += 1
                    else:
                        item_dict[final_suggestion.title()] = 1
                    parsed_items = [(item, qty) for item, qty in item_dict.items()]
                    print(f"🤖 Great! Added {final_suggestion.title()} to your order.")
                else:
                    print("⚠️ Could not identify suggested item to add.")
        else:
            print("🤖 Sorry, I couldn’t understand that. Try again!")

    user_input = input("\n🧑 Want to add more? (or type 'done' to finish): ")
    if user_input.strip().lower() == "done":
        break

# Display final order
while True:
    if parsed_items:
        print("\n🧾 Here's your current order:")
        for item, qty in parsed_items:
            print(f"- {item.title()} x {qty}")

        unavailable = []
        for item, qty in parsed_items:
            if not check_stock(item, qty):
                unavailable.append(item)

        if unavailable:
            print("❌ Some items are not available in the requested quantity.")

            # Get alternative suggestions
            db = get_db_connection()
            if db:
                cursor = db.cursor()
                cursor.execute("SELECT item_name, quantity FROM stock")
                stock_rows = cursor.fetchall()
                db.close()
                stock_dict = {row[0]: row[1] for row in stock_rows}

                suggestion = get_alternative_items(unavailable, stock_dict)
                print("🤖", suggestion)

                choice = input("🤖 Would you like to update your order? (yes/no): ").strip().lower()
                if choice in ["yes", "y"]:
                    print("🔁 Okay, let's try again. Add or remove items as needed.")
                    user_input = input("\n🧑 What would you like to order? ")
                    parsed_items = parse_order(user_input)  # Re-parse the new order
                    continue  # Loop again to re-check and confirm
                    # parsed_items = []  # Reset order for new input
                    # break  # Exit finalization loop, re-initiate order gathering
                else:
                    print("❌ Order cancelled. See you next time!")
                    parsed_items = []  # Clear order
                    break
            else:
                print("❌ Database connection failed. Order cannot proceed.")
                break
        else:
            total = calculate_total(parsed_items, menu)
            print(f"Total Amount: ₹{total:.2f}")

            student_id = input("\n🤖 Can you give me your student ID? ").strip()
            student = get_student_info_by_id(student_id)
            if not student:
                print("⚠️ Student not found. Please try again.")
                continue
            else:
                confirm = input("🤖 Do you want to place this order? (yes/no): ").strip().lower()
                if confirm in ["yes", "y"]:
                    order_items_str = "\n".join([f"{item}, {qty}" for item, qty in parsed_items])
                    order_id = insert_order(student_id, order_items_str, total)

                    if order_id:
                        # Reduce stock
                        reduce_stock(parsed_items)

                        print(f"\n✅ Order ID: {order_id} confirmed.")
                        qr_file = generate_qr_file(order_id, parsed_items, total)

                        msg_body = f"""Hello {student['name']},

Thanks for ordering from CanteenMate AI!

Order ID: {order_id}
Total: ₹{total:.2f}

Please find your QR attached for pickup.

Bon appétit!
– CanteenMate AI 🤖
"""
                        send_email(student["email"], f"Your Canteen Order #{order_id}", msg_body, qr_file)
                        print(f"📧 QR and details sent to {student['email']}")
                        break
                    else:
                        print("❌ Failed to place order due to database issue.")
                        break
                else:
                    print("❌ Order Cancelled.")
                    break
    else:
        print("❌ No items were ordered.")
        break