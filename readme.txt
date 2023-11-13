# Project Setup Guide

# Prerequisites
# Make sure you have Python installed on your computer.
# If not, visit https://www.python.org/downloads/ and download Python for Windows/Linux.

# Install Django and virtualenvwrapper
pip install django
pip install virtualenvwrapper

# Project Setup
# Open the project in Visual Studio Code.
# Open the terminal within VS Code.

# Create Virtual Environment
mkvirtualenv <Name_of_Virtual_Environment>
# Example: mkvirtualenv venv

# Activate Virtual Environment
workon <Name_of_Virtual_Environment>
# Example: workon venv

# Install Dependencies
pip install -r requirements.txt

# Apply Migrations
python manage.py makemigrations
python manage.py migrate

# Create Superuser
python manage.py createsuperuser
# Follow the prompts to set up your superuser account.

# Run the Server
python manage.py runserver

# Visit http://127.0.0.1:8000/admin and log in with your superuser details.

# Create a chat thread:
# Visit http://127.0.0.1:8000/chat/create/key to get the secret code.
# Copy the code and paste it into the secret field while creating the chat thread.

# Create another user.

# Data Constructs for Websockets

# Connect Logged-in User to a Chat Thread
data = {'username': '<logged_in_username>', 'chat_id': '<chat_thread_id>'}

# User is Typing
data = {'sender': '<user_username>', 'function': 'isTyping'}

# User Stopped Typing
data = {'sender': '<user_username>', 'function': 'notTyping'}

# User Deletes Message for Everyone
data = {'function': 'delete', 'message_id': '<chat_message_id>', 'sender': '<sender_username>'}

# User Deletes Message for Himself Only
# Send a GET request to /chat/<chat_id>/message/<message_id>/delete/

# User Sends a Message
data = {'function': 'message', 'message': '<message_text>', 'sender': '<sender_username>', 'sender_id': '<sender_user_id>'}

# Message Delivered
data = {'function': 'isDelivered', 'message_id': '<chat_message_id>'}

# User online or offline status feature upcoming...

# Feel free to explore and enhance the project. Happy coding!
