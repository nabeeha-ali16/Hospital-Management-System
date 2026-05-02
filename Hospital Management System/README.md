# 🏥 Hospital Management System

A complete Hospital Management System built with **Streamlit + SQLite**.

## Features
- 🔐 Role-Based Login (Admin, Doctor, Receptionist)
- 🧑‍⚕️ Patient Management (Add, Edit, Delete, Search, History)
- 👨‍⚕️ Doctor Management (Add, Edit, Delete, Search)
- 📅 Appointment Booking (Book, Edit, Cancel, Delete)
- 💊 Prescription Management (Issue, View, Delete)
- 🧾 Billing System (Generate, Update Status, Revenue Report)
- 📋 Activity Log (Full audit trail)
- ⚙️ User Management (Admin only)
- 📤 Export to CSV and JSON

## How to Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Demo Login Credentials
| Role          | Username          | Password  |
|---------------|-------------------|-----------|
| Admin         | admin             | admin123  |
| Doctor        | doctor1           | doc123    |
| Receptionist  | receptionist1     | rec123    |

## Design Patterns Used
- **Singleton** — Database connection
- **Factory** — Model creation (Patient, Doctor, Appointment)
- **Strategy** — Export formats (CSV, JSON)
- **Decorator** — Activity logging
- **Iterator** — DataFrame iteration

## Syllabus Coverage
| Lecture | Topic | Feature |
|---------|-------|---------|
| 1 | Python Basics | Core logic, conditionals |
| 2 | Collections | Lists, Dicts throughout |
| 3 | OOP | Patient, Doctor, Appointment classes |
| 4 | Modular Programming | database.py, models.py, app.py |
| 5 | Design Patterns | Singleton, Factory, etc. |
| 6 | Exceptions | try/except in all forms |
| 7 | File Handling | CSV/JSON export |
| 8 | Case Study | Full HMS (beyond Bank System) |
