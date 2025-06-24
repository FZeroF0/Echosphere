# EchoSphere: Real-time Messaging Platform

[![Python Version](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![Flask Version](https://img.shields.io/badge/Flask-2.3.x-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-SQLite-informational.svg)](https://www.sqlite.org/index.html)
[![Bootstrap Version](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)](https://getbootstrap.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A modern web-based messaging platform designed for real-time communication, featuring user authentication, contact management, private messaging, and file attachments. Built with Flask, SQLite, and Bootstrap, this project demonstrates foundational full-stack web development skills with an eye towards scalable and secure real-time features.

## Table of Contents

* [Features](#features)
* [Technologies Used](#technologies-used)
* [Getting Started](#getting-started)
    * [Prerequisites](#prerequisites)
    * [Installation](#installation)
    * [Database Initialization](#database-initialization)
* [Usage](#usage)
* [Future Enhancements](#future-enhancements)
* [Contributing](#contributing)
* [License](#license)

## Features

* **User Registration & Login:** Secure user authentication system.
* **Contact Management:** Users can add other registered users to their contact list by email.
* **Private Messaging:** Send one-to-one text messages between users.
* **File Attachments:** Ability to send and view media files (e.g., images, PDFs) within messages.
* **Polling for Live Updates:** Messages are periodically fetched to provide a near real-time chat experience.
* **Responsive User Interface:** Built with Bootstrap 5.3.3 for a modern and mobile-friendly design.
* **Flash Messaging:** Provides user feedback for actions like login success, registration, and errors.

## Technologies Used

* **Backend:**
    * **Python 3.x:** The core programming language.
    * **Flask (2.3.x):** A lightweight web framework for the backend logic.
    * **Flask-SocketIO:** Integrated for future real-time messaging capabilities (currently uses polling).
    * **Werkzeug Security:** For secure password hashing and verification.
    * **python-dotenv:** For managing environment variables during development.
* **Frontend:**
    * **HTML5, CSS3:** Structure and styling of web pages.
    * **Bootstrap 5.3.3:** CSS framework for responsive and modern UI components.
    * **JavaScript (ES6+):** For asynchronous form submissions (AJAX) and message polling.
* **Database:**
    * **SQLite3:** A lightweight, file-based SQL database for storing user, contact, and message data.

## Getting Started

Follow these instructions to get a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

* Python 3.x installed on your system.
* `pip` (Python package installer).

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/FZeroF0/Echosphere.git](https://github.com/FZeroF0/Echosphere.git)
    cd Echosphere
    ```

2.  **Create and activate a virtual environment:**
    It's highly recommended to use a virtual environment to manage project dependencies.

    ```bash
    python3 -m venv venv
    ```

    * **On macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```
    * **On Windows (Command Prompt):**
        ```bash
        venv\Scripts\activate.bat
        ```
    * **On Windows (PowerShell):**
        ```powershell
        .\venv\Scripts\Activate.ps1
        ```

3.  **Install dependencies:**
    Make sure your virtual environment is active, then install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Environment Variables:**
    Create a file named `.env` in the root directory of your project (the same folder as `app.py`). This file will store your Flask `SECRET_KEY`.

    **Important:** The `.env` file is excluded from Git via `.gitignore` for security.

    ```
    SECRET_KEY=your_very_long_and_random_secret_key_here
    ```
    * **Generate a strong `SECRET_KEY`:** You can generate a good one by running this in a Python interpreter:
        ```python
        import os
        print(os.urandom(24).hex()) # For a 24-byte (192-bit) key
        ```
        Copy the output and paste it as the value for `SECRET_KEY`.

5.  **Run the Flask application:**
    Ensure your virtual environment is active.
    ```bash
    export FLASK_APP=app.py
    flask run
    ```
    The application will typically be accessible at `http://127.0.0.1:5000/`.

### Database Initialization

The `app.py` script is designed to automatically create the `app.db` file and all necessary tables (`users`, `messages`, `user_contacts`) if they do not already exist when the application starts. You don't need to run separate database migration commands for this initial setup.

## Usage

1.  **Register:** Navigate to the root URL (e.g., `http://127.0.0.1:5000/`) and create a new user account.
2.  **Login:** Use your newly registered credentials to log in.
3.  **Add Contacts:** Go to the "Add Contact" page and enter the email of another registered user to add them to your contacts.
4.  **Send Messages:** Visit the "Send Message" page, select a contact, type your message, and optionally attach a file.
5.  **View Messages:** Navigate to your messages page (e.g., `/messages/<your_user_id>`) to see your chat history.

## Future Enhancements

This project is a work in progress, and the following key enhancements are planned or highly recommended to improve its functionality, security, and scalability:

* **Security (Critical):**
    * Add more robust server-side input validation and sanitization to prevent common vulnerabilities like SQL injection and Cross-Site Scripting (XSS).
* **Real-time Communication:**
    * Fully integrate **Flask-SocketIO** for true instant, bidirectional messaging. Replace the current 5-second polling mechanism with WebSocket-based push notifications for real-time updates.
* **User Interface & Experience:**
    * Implement dynamic chat bubbles in the `messages.html` to resemble a more traditional chat interface.
    * Add read receipts.
    * Improve file preview/display within chat.
* **Scalability & Deployment (DevOps Focus):**
    * Containerize the application using **Docker** by creating a `Dockerfile` and `docker-compose.yml`.
    * Explore deployment to cloud platforms (e.g., AWS EC2, DigitalOcean, Heroku) using a production-ready WSGI server like **Gunicorn** and a reverse proxy like **Nginx**.
    * Implement comprehensive logging and monitoring solutions.
* **Additional Features:**
    * Group chat functionality.
    * User profiles and avatars.
    * Message editing and deletion.

## Contributing

Contributions are welcome! If you have suggestions or want to improve the project, feel free to fork the repository, make your changes, and submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
