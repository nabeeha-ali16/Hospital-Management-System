"""
Database Module - Singleton Pattern
Manages SQLite database for Hospital Management System
"""
import sqlite3
import os
import hashlib
from datetime import datetime


class Database:
    """Singleton Database class"""
    _instance = None
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._connection is None:
            db_path = os.path.join(os.path.dirname(__file__), "hospital.db")
            self._connection = sqlite3.connect(db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
            self._create_tables()
            self._seed_data()

    def get_connection(self):
        return self._connection

    def _create_tables(self):
        cur = self._connection.cursor()

        # Users table (role-based login)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin','doctor','receptionist')),
                full_name TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # Patients table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                blood_group TEXT,
                phone TEXT,
                email TEXT,
                address TEXT,
                emergency_contact TEXT,
                registered_at TEXT DEFAULT (datetime('now')),
                is_active INTEGER DEFAULT 1
            )
        """)

        # Doctors table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doctor_id TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                specialization TEXT,
                phone TEXT,
                email TEXT,
                qualification TEXT,
                experience_years INTEGER,
                fee REAL DEFAULT 0.0,
                is_available INTEGER DEFAULT 1,
                joined_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # Appointments table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appointment_id TEXT UNIQUE NOT NULL,
                patient_id TEXT,
                doctor_id TEXT,
                appointment_date TEXT,
                appointment_time TEXT,
                status TEXT DEFAULT 'Scheduled' CHECK(status IN ('Scheduled','Completed','Cancelled','No-Show')),
                reason TEXT,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(patient_id) REFERENCES patients(patient_id),
                FOREIGN KEY(doctor_id) REFERENCES doctors(doctor_id)
            )
        """)

        # Prescriptions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS prescriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prescription_id TEXT UNIQUE NOT NULL,
                appointment_id TEXT,
                patient_id TEXT,
                doctor_id TEXT,
                diagnosis TEXT,
                medicines TEXT,
                instructions TEXT,
                follow_up_date TEXT,
                issued_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(appointment_id) REFERENCES appointments(appointment_id)
            )
        """)

        # Bills table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_id TEXT UNIQUE NOT NULL,
                patient_id TEXT,
                appointment_id TEXT,
                consultation_fee REAL DEFAULT 0.0,
                medicine_charge REAL DEFAULT 0.0,
                lab_charge REAL DEFAULT 0.0,
                other_charge REAL DEFAULT 0.0,
                total_amount REAL DEFAULT 0.0,
                payment_status TEXT DEFAULT 'Pending' CHECK(payment_status IN ('Pending','Paid','Partially Paid')),
                payment_method TEXT,
                billed_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY(patient_id) REFERENCES patients(patient_id)
            )
        """)

        # Activity log table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT,
                action TEXT,
                details TEXT,
                timestamp TEXT DEFAULT (datetime('now'))
            )
        """)

        self._connection.commit()

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def _seed_data(self):
        cur = self._connection.cursor()
        cur.execute("SELECT COUNT(*) as c FROM users")
        if cur.fetchone()["c"] > 0:
            return

        users = [
            ("admin", self._hash_password("admin123"), "admin", "System Administrator"),
            ("doctor1", self._hash_password("doc123"), "doctor", "Dr. Ahmed Raza"),
            ("receptionist1", self._hash_password("rec123"), "receptionist", "Sara Khan"),
        ]
        cur.executemany("INSERT INTO users (username,password,role,full_name) VALUES (?,?,?,?)", users)

        doctors = [
            ("D001", "Dr. Ahmed Raza", "Cardiology", "0300-1234567", "ahmed@hospital.com", "MBBS, FCPS", 10, 1500.0),
            ("D002", "Dr. Fatima Malik", "Neurology", "0301-2345678", "fatima@hospital.com", "MBBS, MD", 8, 2000.0),
            ("D003", "Dr. Usman Khan", "Orthopedics", "0302-3456789", "usman@hospital.com", "MBBS, MS", 12, 1800.0),
            ("D004", "Dr. Ayesha Tariq", "Pediatrics", "0303-4567890", "ayesha@hospital.com", "MBBS, DCH", 6, 1200.0),
            ("D005", "Dr. Bilal Hassan", "General Medicine", "0304-5678901", "bilal@hospital.com", "MBBS", 4, 1000.0),
        ]
        cur.executemany("""
            INSERT INTO doctors (doctor_id,full_name,specialization,phone,email,qualification,experience_years,fee)
            VALUES (?,?,?,?,?,?,?,?)
        """, doctors)

        patients = [
            ("P001", "Muhammad Ali", 35, "Male", "B+", "0311-1111111", "ali@email.com", "Lahore", "0311-9999999"),
            ("P002", "Amna Siddiqui", 28, "Female", "A+", "0312-2222222", "amna@email.com", "Karachi", "0312-8888888"),
            ("P003", "Tariq Mehmood", 52, "Male", "O-", "0313-3333333", "tariq@email.com", "Islamabad", "0313-7777777"),
        ]
        cur.executemany("""
            INSERT INTO patients (patient_id,full_name,age,gender,blood_group,phone,email,address,emergency_contact)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, patients)

        self._connection.commit()

    def log_activity(self, user, action, details=""):
        cur = self._connection.cursor()
        cur.execute("INSERT INTO activity_log (user,action,details) VALUES (?,?,?)", (user, action, details))
        self._connection.commit()
