# Vehicle Cataloging and Lending Application

## Project Overview
This project was developed as part of CS 3240 Software Engineering at the University of Virginia. The primary goal was to learn practical software development skills through the creation of a Cataloging and Lending Application (CLA). Working collaboratively in groups of five, each member undertook specialized roles to effectively deliver a fully functional web application.

---

## Project Features
- **Google Authentication:** Secure login using Google accounts, differentiating user types.
- **User Roles:** Supports Anonymous Users, Patrons, Librarians, and Django Administrators, each with distinct access and functionalities.
- **Item Management:** Comprehensive item handling including addition, editing, deletion, ratings, and comments.
- **Collection Management:** Creation and management of public/private item collections.
- **Borrowing Requests:** Patrons can request to borrow items, managed and approved by Librarians.
- **Search Functionality:** Robust search capabilities for items and collections.
- **Cloud Integration:** Amazon S3 used for storing item-related files.
- **Database Management:** PostgreSQL for data persistence and management.

---

## Authors
- Todd Balwinski (Requirements Manager)
- Andy Liang (Srum Master)
- Krish Patel (DevOps Manager)
- Derick Lee (Software Architecht)
- Kevin Arleen (Testing Manager)

---

## My Role: Requirements Manager
As the Requirements Manager, I led the requirements elicitation process to define clear and comprehensive features based on user and stakeholder needs. My responsibilities included:
- Organizing and leading the requirements elicitation sessions.
- Documenting and maintaining the requirements throughout the project lifecycle.
- Managing the GitHub feature and issue tracker, ensuring accurate and timely updates reflecting project status and priorities.

[Requirements Elicitation Document (Participant Names Redacted)](https://github.com/user-attachments/files/20263394/Requirements.Elicitation.Document.Participant.Names.Redacted.pdf)

---

## Tech Stack
- **Programming Language:** Python 3
- **Framework:** Django 5
- **Database:** PostgreSQL (Production), SQLite (Local Development)
- **Cloud Hosting:** Heroku
- **Cloud Storage:** Amazon S3
- **CI/CD:** GitHub Actions
- **Version Control:** GitHub
- **Authentication:** Google Account API

---

## Running Locally

### Prerequisites
- Python 3
- pip
- SQLite (for local development)
- Git

### Installation and Setup
1. Clone the repository:
```bash
git clone https://github.com/yourusername/yourrepository.git
cd yourrepository
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables (Google API credentials, Amazon S3 credentials, PostgreSQL URL if used locally, etc.) in a `.env` file or directly in `settings.py`.

5. Apply database migrations:
```bash
python manage.py migrate
```

6. Run the development server:
```bash
python manage.py runserver
```

Visit `http://localhost:8000` to interact with the application locally.
