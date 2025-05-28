# 🍽️ Smart Digidara Canteen AI Bot 🤖

## Overview

The Smart Digidara Canteen AI Bot is an intelligent system designed to streamline the canteen ordering process. It integrates a conversational AI assistant, database management, QR code generation, and email notifications to provide a seamless experience for students and canteen staff.

## ✨ Features

- 🤖 **AI Chatbot**: Handles natural language order input using LLaMA3 via LangChain.

- 📋 **Dynamic Menu Fetching**: Retrieves live menu from MySQL database.

- 📦 **Stock Checking**: Confirms item availability before order confirmation.

- 📤 **QR Bill Generation**: Creates and sends a QR code bill via email.

- 📧 **Email Notification**: Sends order summary with QR code to registered student.

- 🧠 **Conversation Memory**: Retains chat history using `ConversationBufferMemory`.

---

## 🚀 How It Works

Student Login/Registration: Asks student ID, and registers new students if not in the database.

Menu Display: Retrieves and shows available menu items.

Natural Language Input: Accepts plain text orders like:

I'd like 2 samosas and 1 cold coffee.

AI Parsing: Uses LLaMA3 (LangChain) to extract items and quantity.

Stock Check: Verifies if the items are available in stock.

Order Confirmation: Saves order to database, generates bill, sends QR via email.

Conversation Logs: Retains chat history to allow natural back-and-forth interaction.



## Prerequisites

Python 3.8 or higher

MySQL Server

Ollama

Gmail Account (for sending emails using App Password)

## Installation

# 1. Clone the Repository

git clone https://github.com/yourusername/smart-digidara-canteen-ai.git
cd smart-digidara-canteen-ai

# 2. Set Up a Virtual Environment

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install Dependencies

## 🧠 Tech Stack

| Component        | Technology Used         |
|------------------|-------------------------|
| Language         | Python 3                |
| AI Model         | LLaMA3 via LangChain    |
| Database         | MySQL                   |
| Email Service    | Gmail SMTP              |
| QR Code Generator| `qrcode` Python library |
| AI Memory        | LangChain Memory        |



pip install -r requirements.txt

# 4. Configure MySQL Database


## Create a database named canteenai.

## Execute the following SQL:

CREATE TABLE students (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(15),
);

CREATE TABLE items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100),
  price DECIMAL(10,2),
  stock INT
);

CREATE TABLE orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    items TEXT,
    total_amount FLOAT,
    status VARCHAR(50),
    order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    student_id int
);
create table stock (
   item_id int AUTO_INCREMENT PRIMARY KEY,
   item_name varchar(100),
   quantity int
);

INSERT INTO stock (item_name, quantity) VALUES
('Samosa', 20),
('Sandwich', 20),
('Cool Drink', 20),
('Brownie', 20),
('Veg Puff', 20),
('Paneer Roll', 20),
('Momos', 20);

create table food_items (
   item_id int AUTO_INCREMENT PRIMARY KEY,
   item_name varchar(100),
   price decimal(10,2),
   stock int
);

INSERT INTO food_items (item_name, price, stock) VALUES
('Samosa', 2.50, 20),
('Sandwich', 4.00, 20),
('Cool Drink', 1.50, 20),
('Brownie', 3.00, 20),
('Veg Puff', 2.00, 20),
('Paneer Roll', 5.00, 20),
('Momos', 3.50, 20);

## After creating table configure the database connection in `config.py` file.
    MYSQL_CONFIG = {
        "host": "localhost",
        "user": "root",
        "password": "your_mysql_password",
        "database": "canteenai"
    }
## 5. Configure Email Settings

🔑 Steps to Generate App Password

1.Go to your Google Account Security page:

2.Visit: https://myaccount.google.com/security

3.Scroll down to "Signing in to Google" section.

4.Click on "App passwords".

5.You may need to sign in again.

6.Under "Select app", choose the app you're using (e.g., Mail, or Other if it's custom).

7.Under "Select device", choose the device you're using or name it manually.

8.Click "Generate".

9.Google will display a 16-character app password. Copy it — this is your app password.



# 🔐 Step 1: Enable 2-Step Verification on your Google Account
Go to: https://myaccount.google.com/security

Under "Signing in to Google", click on 2-Step Verification.

Follow the steps to turn it on (you may need your phone).

# 🔑 Step 2: Generate an App Password
Stay in https://myaccount.google.com/security

Under "Signing in to Google", click App Passwords
(You’ll only see this if 2-Step Verification is enabled.)

Select the app: Mail

Select the device: Other (Custom Name) → Enter something like Python Script

Click Generate

✅ Copy the 16-character app password shown (e.g., abcd efgh ijkl mnop).

💻 Step 3: Update Your Python Script

   Update the script:
   
   SENDER_EMAIL = 'your_email@gmail.com'
   SENDER_PASSWORD = 'your_app_password'

### 🦙 Ollama Installation & Setup Guide (LLaMA 3 Support)

This guide helps you install and run Ollama to use LLaMA 3 and other large language models locally on your machine.

---

## ✅ System Requirements
- Windows 10/11, macOS, or Linux
- Minimum 8–16 GB RAM (recommended)
- Internet connection to download models

---

## 🔽 Step 1: Download and Install Ollama

### 🪟 For Windows:
1. Visit [https://ollama.com](https://ollama.com)
2. Click **Download for Windows**
3. Run the downloaded `.exe` installer
4. Once installed, open **Command Prompt** or **PowerShell**

📥 Step 2: Pull the LLaMA 3 Model

 ollama pull llama3

📥 Step 3: Run the Model
Start chatting with the model:

ollama run llama3

Type your prompt and press Enter:

> What is AI?
< AI stands for Artificial Intelligence...

python canteen_ai_bot.py

Project Structure

smart-digidara-canteen-ai/
├── canteen_agent.py
├── requirements.txt
├── README.md
├── order_qr_codes/
│   └── order_<order_id>.png
└── ...

## 🔄 Project Workflow

1. **User Order Placement**
   - Student interacts with the chatbot (Customer Interaction Agent).
   - LLaMA (via Ollama) interprets natural language input.
   - Agent queries the SQL database for item availability.

2. **Order Processing**
   - If items are available, the order is accepted and logged.
   - The chatbot confirms the order and estimates the bill.

3. **Stock Management**
   - Stock Management Agent updates inventory based on order.
   - Low-stock alerts are generated for admin.

4. **Billing and Dashboard**
   - Billing Agent calculates total cost and generates a bill.
   - QR code or downloadable invoice is provided to student.
   - Admin dashboard updates order analytics in real-time.

5. **Admin Insights**
   - Dashboard visualizes daily revenue, popular items, and stock trends using charts.

6. **Data Storage**
   - All order and stock data is stored in a relational database (e.g., MySQL ).


Troubleshooting

Database Connection Errors: Ensure MySQL server is running and credentials are correct.

Email Sending Issues: Verify SMTP settings and App Password usage.

Ollama Model Issues: Confirm model is downloaded and available via ollama pull llama3.

Future Enhancements

Web Interface using Flask or Django

Payment Gateway Integration

Admin Dashboard for Order and Stock Management

License

This project is licensed under the MIT License.

