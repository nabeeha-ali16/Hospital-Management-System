"""
Models Module - OOP Classes (Lecture 3 - OOP)
All entity classes with encapsulation and data access
"""
import hashlib
from database import Database


def _hash(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


class User:
    def __init__(self, row):
        self.id = row["id"]
        self.username = row["username"]
        self.role = row["role"]
        self.full_name = row["full_name"]

    @staticmethod
    def authenticate(username, password):
        db = Database().get_connection()
        row = db.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, _hash(password))
        ).fetchone()
        return User(row) if row else None

    @staticmethod
    def get_all():
        db = Database().get_connection()
        return db.execute("SELECT * FROM users ORDER BY role").fetchall()

    @staticmethod
    def create(username, password, role, full_name):
        db = Database().get_connection()
        db.execute(
            "INSERT INTO users (username,password,role,full_name) VALUES (?,?,?,?)",
            (username, _hash(password), role, full_name)
        )
        db.commit()

    @staticmethod
    def delete(user_id):
        db = Database().get_connection()
        db.execute("DELETE FROM users WHERE id=?", (user_id,))
        db.commit()

    @staticmethod
    def change_password(user_id, new_password):
        db = Database().get_connection()
        db.execute("UPDATE users SET password=? WHERE id=?", (_hash(new_password), user_id))
        db.commit()


class Patient:
    def __init__(self, row):
        self.id = row["id"]
        self.patient_id = row["patient_id"]
        self.full_name = row["full_name"]
        self.age = row["age"]
        self.gender = row["gender"]
        self.blood_group = row["blood_group"]
        self.phone = row["phone"]
        self.email = row["email"]
        self.address = row["address"]
        self.emergency_contact = row["emergency_contact"]
        self.registered_at = row["registered_at"]
        self.is_active = row["is_active"]

    @staticmethod
    def _next_id():
        db = Database().get_connection()
        row = db.execute("SELECT COUNT(*) as c FROM patients").fetchone()
        return f"P{str(row['c'] + 1).zfill(3)}"

    @staticmethod
    def get_all(active_only=False):
        db = Database().get_connection()
        if active_only:
            return db.execute("SELECT * FROM patients WHERE is_active=1 ORDER BY registered_at DESC").fetchall()
        return db.execute("SELECT * FROM patients ORDER BY registered_at DESC").fetchall()

    @staticmethod
    def get_by_id(patient_id):
        db = Database().get_connection()
        return db.execute("SELECT * FROM patients WHERE patient_id=?", (patient_id,)).fetchone()

    @staticmethod
    def search(query):
        db = Database().get_connection()
        q = f"%{query}%"
        return db.execute(
            "SELECT * FROM patients WHERE full_name LIKE ? OR patient_id LIKE ? OR phone LIKE ?",
            (q, q, q)
        ).fetchall()

    @staticmethod
    def create(full_name, age, gender, blood_group, phone, email, address, emergency_contact):
        db = Database().get_connection()
        pid = Patient._next_id()
        db.execute("""
            INSERT INTO patients (patient_id,full_name,age,gender,blood_group,phone,email,address,emergency_contact)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (pid, full_name, age, gender, blood_group, phone, email, address, emergency_contact))
        db.commit()
        return pid

    @staticmethod
    def update(patient_id, full_name, age, gender, blood_group, phone, email, address, emergency_contact):
        db = Database().get_connection()
        db.execute("""
            UPDATE patients SET full_name=?,age=?,gender=?,blood_group=?,phone=?,email=?,address=?,emergency_contact=?
            WHERE patient_id=?
        """, (full_name, age, gender, blood_group, phone, email, address, emergency_contact, patient_id))
        db.commit()

    @staticmethod
    def deactivate(patient_id):
        db = Database().get_connection()
        db.execute("UPDATE patients SET is_active=0 WHERE patient_id=?", (patient_id,))
        db.commit()

    @staticmethod
    def delete(patient_id):
        db = Database().get_connection()
        db.execute("DELETE FROM patients WHERE patient_id=?", (patient_id,))
        db.commit()


class Doctor:
    def __init__(self, row):
        self.id = row["id"]
        self.doctor_id = row["doctor_id"]
        self.full_name = row["full_name"]
        self.specialization = row["specialization"]
        self.phone = row["phone"]
        self.email = row["email"]
        self.qualification = row["qualification"]
        self.experience_years = row["experience_years"]
        self.fee = row["fee"]
        self.is_available = row["is_available"]

    @staticmethod
    def _next_id():
        db = Database().get_connection()
        row = db.execute("SELECT COUNT(*) as c FROM doctors").fetchone()
        return f"D{str(row['c'] + 1).zfill(3)}"

    @staticmethod
    def get_all(available_only=False):
        db = Database().get_connection()
        if available_only:
            return db.execute("SELECT * FROM doctors WHERE is_available=1 ORDER BY full_name").fetchall()
        return db.execute("SELECT * FROM doctors ORDER BY full_name").fetchall()

    @staticmethod
    def get_by_id(doctor_id):
        db = Database().get_connection()
        return db.execute("SELECT * FROM doctors WHERE doctor_id=?", (doctor_id,)).fetchone()

    @staticmethod
    def search(query):
        db = Database().get_connection()
        q = f"%{query}%"
        return db.execute(
            "SELECT * FROM doctors WHERE full_name LIKE ? OR doctor_id LIKE ? OR specialization LIKE ?",
            (q, q, q)
        ).fetchall()

    @staticmethod
    def create(full_name, specialization, phone, email, qualification, experience_years, fee):
        db = Database().get_connection()
        did = Doctor._next_id()
        db.execute("""
            INSERT INTO doctors (doctor_id,full_name,specialization,phone,email,qualification,experience_years,fee)
            VALUES (?,?,?,?,?,?,?,?)
        """, (did, full_name, specialization, phone, email, qualification, experience_years, fee))
        db.commit()
        return did

    @staticmethod
    def update(doctor_id, full_name, specialization, phone, email, qualification, experience_years, fee, is_available):
        db = Database().get_connection()
        db.execute("""
            UPDATE doctors SET full_name=?,specialization=?,phone=?,email=?,qualification=?,
            experience_years=?,fee=?,is_available=? WHERE doctor_id=?
        """, (full_name, specialization, phone, email, qualification, experience_years, fee, is_available, doctor_id))
        db.commit()

    @staticmethod
    def delete(doctor_id):
        db = Database().get_connection()
        db.execute("DELETE FROM doctors WHERE doctor_id=?", (doctor_id,))
        db.commit()


class Appointment:
    def __init__(self, row):
        self.id = row["id"]
        self.appointment_id = row["appointment_id"]
        self.patient_id = row["patient_id"]
        self.doctor_id = row["doctor_id"]
        self.appointment_date = row["appointment_date"]
        self.appointment_time = row["appointment_time"]
        self.status = row["status"]
        self.reason = row["reason"]
        self.notes = row["notes"]
        self.created_at = row["created_at"]

    @staticmethod
    def _next_id():
        db = Database().get_connection()
        row = db.execute("SELECT COUNT(*) as c FROM appointments").fetchone()
        return f"APT{str(row['c'] + 1).zfill(4)}"

    @staticmethod
    def get_all():
        db = Database().get_connection()
        return db.execute("""
            SELECT a.*, p.full_name as patient_name, d.full_name as doctor_name, d.specialization
            FROM appointments a
            LEFT JOIN patients p ON a.patient_id = p.patient_id
            LEFT JOIN doctors d ON a.doctor_id = d.doctor_id
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
        """).fetchall()

    @staticmethod
    def get_by_patient(patient_id):
        db = Database().get_connection()
        return db.execute("""
            SELECT a.*, d.full_name as doctor_name, d.specialization
            FROM appointments a
            LEFT JOIN doctors d ON a.doctor_id = d.doctor_id
            WHERE a.patient_id=? ORDER BY a.appointment_date DESC
        """, (patient_id,)).fetchall()

    @staticmethod
    def get_by_doctor(doctor_id):
        db = Database().get_connection()
        return db.execute("""
            SELECT a.*, p.full_name as patient_name
            FROM appointments a
            LEFT JOIN patients p ON a.patient_id = p.patient_id
            WHERE a.doctor_id=? ORDER BY a.appointment_date DESC
        """, (doctor_id,)).fetchall()

    @staticmethod
    def create(patient_id, doctor_id, date, time, reason, notes=""):
        db = Database().get_connection()
        aid = Appointment._next_id()
        db.execute("""
            INSERT INTO appointments (appointment_id,patient_id,doctor_id,appointment_date,appointment_time,reason,notes)
            VALUES (?,?,?,?,?,?,?)
        """, (aid, patient_id, doctor_id, date, time, reason, notes))
        db.commit()
        return aid

    @staticmethod
    def update_status(appointment_id, status, notes=""):
        db = Database().get_connection()
        db.execute(
            "UPDATE appointments SET status=?, notes=? WHERE appointment_id=?",
            (status, notes, appointment_id)
        )
        db.commit()

    @staticmethod
    def update(appointment_id, patient_id, doctor_id, date, time, reason, notes, status):
        db = Database().get_connection()
        db.execute("""
            UPDATE appointments SET patient_id=?,doctor_id=?,appointment_date=?,appointment_time=?,
            reason=?,notes=?,status=? WHERE appointment_id=?
        """, (patient_id, doctor_id, date, time, reason, notes, status, appointment_id))
        db.commit()

    @staticmethod
    def delete(appointment_id):
        db = Database().get_connection()
        db.execute("DELETE FROM appointments WHERE appointment_id=?", (appointment_id,))
        db.commit()


class Prescription:
    @staticmethod
    def _next_id():
        db = Database().get_connection()
        row = db.execute("SELECT COUNT(*) as c FROM prescriptions").fetchone()
        return f"RX{str(row['c'] + 1).zfill(4)}"

    @staticmethod
    def get_all():
        db = Database().get_connection()
        return db.execute("""
            SELECT pr.*, p.full_name as patient_name, d.full_name as doctor_name
            FROM prescriptions pr
            LEFT JOIN patients p ON pr.patient_id = p.patient_id
            LEFT JOIN doctors d ON pr.doctor_id = d.doctor_id
            ORDER BY pr.issued_at DESC
        """).fetchall()

    @staticmethod
    def get_by_patient(patient_id):
        db = Database().get_connection()
        return db.execute("""
            SELECT pr.*, d.full_name as doctor_name
            FROM prescriptions pr
            LEFT JOIN doctors d ON pr.doctor_id = d.doctor_id
            WHERE pr.patient_id=? ORDER BY pr.issued_at DESC
        """, (patient_id,)).fetchall()

    @staticmethod
    def create(appointment_id, patient_id, doctor_id, diagnosis, medicines, instructions, follow_up):
        db = Database().get_connection()
        rxid = Prescription._next_id()
        db.execute("""
            INSERT INTO prescriptions (prescription_id,appointment_id,patient_id,doctor_id,diagnosis,medicines,instructions,follow_up_date)
            VALUES (?,?,?,?,?,?,?,?)
        """, (rxid, appointment_id, patient_id, doctor_id, diagnosis, medicines, instructions, follow_up))
        db.commit()
        return rxid

    @staticmethod
    def delete(prescription_id):
        db = Database().get_connection()
        db.execute("DELETE FROM prescriptions WHERE prescription_id=?", (prescription_id,))
        db.commit()


class Bill:
    @staticmethod
    def _next_id():
        db = Database().get_connection()
        row = db.execute("SELECT COUNT(*) as c FROM bills").fetchone()
        return f"BILL{str(row['c'] + 1).zfill(4)}"

    @staticmethod
    def get_all():
        db = Database().get_connection()
        return db.execute("""
            SELECT b.*, p.full_name as patient_name
            FROM bills b LEFT JOIN patients p ON b.patient_id = p.patient_id
            ORDER BY b.billed_at DESC
        """).fetchall()

    @staticmethod
    def get_by_patient(patient_id):
        db = Database().get_connection()
        return db.execute(
            "SELECT * FROM bills WHERE patient_id=? ORDER BY billed_at DESC", (patient_id,)
        ).fetchall()

    @staticmethod
    def create(patient_id, appointment_id, consult_fee, medicine, lab, other, method):
        db = Database().get_connection()
        bid = Bill._next_id()
        total = consult_fee + medicine + lab + other
        db.execute("""
            INSERT INTO bills (bill_id,patient_id,appointment_id,consultation_fee,medicine_charge,lab_charge,other_charge,total_amount,payment_method,payment_status)
            VALUES (?,?,?,?,?,?,?,?,?,'Paid')
        """, (bid, patient_id, appointment_id, consult_fee, medicine, lab, other, total, method))
        db.commit()
        return bid, total

    @staticmethod
    def update_status(bill_id, status):
        db = Database().get_connection()
        db.execute("UPDATE bills SET payment_status=? WHERE bill_id=?", (status, bill_id))
        db.commit()

    @staticmethod
    def delete(bill_id):
        db = Database().get_connection()
        db.execute("DELETE FROM bills WHERE bill_id=?", (bill_id,))
        db.commit()
