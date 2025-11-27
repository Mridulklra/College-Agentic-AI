College Agentic AI

This project is an intelligent AI-based assistant designed for college-related queries.
It can understand uploaded files and respond with relevant answers using an agent-style workflow.

Features

Upload any file (PDF / CSV / Images / Text)

Extracts information and answers queries based on file content

Backend prototype built using FastAPI + Python

Plans for upcoming features:

Frontend interface

Backend–Frontend integration

Email automation (send/receive college updates)

How to Run

Create virtual environment:

python -m venv venv


Activate:

venv\Scripts\activate


Install dependencies:

pip install -r requirements.txt


Start server:

uvicorn main:app --reload

Project Structure
├── main.py
├── backend.py
├── uploads/
├── requirements.txt
└── sample_timetable.txt

Future Scope

Full agentic workflow

Chat UI for students

Scheduling, emailing, and automated notifications
