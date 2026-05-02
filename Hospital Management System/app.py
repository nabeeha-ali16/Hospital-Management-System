import streamlit as st
import pandas as pd
import json
import csv
import io
import os
import sys
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(__file__))

from database import Database
from models import User, Patient, Doctor, Appointment, Prescription, Bill

st.set_page_config(
    page_title="Hospital Management System",
    page_icon=" ",
    layout="wide",
    initial_sidebar_state="expanded"
)

with open(os.path.join(os.path.dirname(__file__), "styles.css")) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.page = "Dashboard"

def show_success(msg): st.success(f"✅ {msg}")
def show_error(msg):   st.error(f"❌ {msg}")
def show_info(msg):    st.info(f"ℹ️ {msg}")

def log(action, details=""):
    user = st.session_state.user.username if st.session_state.user else "system"
    Database().log_activity(user, action, details)

def export_to_csv(data, filename):
    if not data:
        show_info("No data to export.")
        return
    df = pd.DataFrame([dict(r) for r in data])
    csv_bytes = df.to_csv(index=False).encode()
    st.download_button("⬇️ Download CSV", csv_bytes, file_name=filename, mime="text/csv")

def export_to_json(data, filename):
    if not data:
        show_info("No data to export.")
        return
    json_bytes = json.dumps([dict(r) for r in data], indent=2, default=str).encode()
    st.download_button(" Download JSON", json_bytes, file_name=filename, mime="application/json")

def rows_to_df(rows):
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([dict(r) for r in rows])

def login_page():
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div class='login-card'>
            <div class='login-title'>Hospital Management System</div>
            <div class='login-sub'>Hospital Management System</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        with st.container():
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")

            if st.button(" Login", use_container_width=True, type="primary"):
                if username and password:
                    user = User.authenticate(username, password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user = user
                        log("LOGIN", f"Role: {user.role}")
                        st.rerun()
                    else:
                        show_error("Invalid username or password")
                else:
                    show_error("Please enter credentials")

            st.markdown("---")
            st.markdown("**Demo Accounts:**")
            st.code("admin / admin123\ndoctor1 / doc123\nreceptionist1 / rec123")

def sidebar():
    with st.sidebar:
        st.markdown("## Hospital Management System")
        st.markdown(f"**{st.session_state.user.full_name}**")
        st.markdown(f"*Role: {st.session_state.user.role.title()}*")
        st.markdown("---")

        role = st.session_state.user.role

        menu_items = {
            "• Dashboard": "Dashboard",
            "• Patients": "Patients",
            "• Doctors": "Doctors",
            "• Appointments": "Appointments",
            "• Prescriptions": "Prescriptions",
            "• Billing": "Billing",
            "• Activity Log": "Activity Log",
        }

        if role == "admin":
            menu_items["User Management"] = "Users"

        for label, page in menu_items.items():
            if st.button(label, use_container_width=True,
                         type="primary" if st.session_state.page == page else "secondary"):
                st.session_state.page = page
                st.rerun()

        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            log("LOGOUT")
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()
            
def page_dashboard():
    st.markdown("<div class='section-header'>Dashboard Overview</div>", unsafe_allow_html=True)

    patients   = Patient.get_all(active_only=True)
    doctors    = Doctor.get_all(available_only=True)
    appts      = Appointment.get_all()
    bills      = Bill.get_all()
    prescriptions = Prescription.get_all()

    total_revenue = sum(b["total_amount"] for b in bills if b["payment_status"] == "Paid")
    today_appts   = [a for a in appts if a["appointment_date"] == str(date.today())]
    scheduled     = [a for a in appts if a["status"] == "Scheduled"]

    # Metric cards
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""<div class='metric-card card-blue'>
            <h2>{len(patients)}</h2><p>Active Patients</p></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class='metric-card card-green'>
            <h2>{len(doctors)}</h2><p>Available Doctors</p></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class='metric-card card-orange'>
            <h2>{len(today_appts)}</h2><p>Today's Appointments</p></div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class='metric-card card-purple'>
            <h2>{len(prescriptions)}</h2><p>Prescriptions</p></div>""", unsafe_allow_html=True)
    with c5:
        st.markdown(f"""<div class='metric-card card-red'>
            <h2>₨{total_revenue:,.0f}</h2><p>Total Revenue</p></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Today's Appointments")
        if today_appts:
            df = pd.DataFrame([{
                "ID": a["appointment_id"],
                "Patient": a["patient_name"],
                "Doctor": a["doctor_name"],
                "Time": a["appointment_time"],
                "Status": a["status"]
            } for a in today_appts])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            show_info("No appointments scheduled for today.")

    with col2:
        st.markdown("### Appointment Status Breakdown")
        if appts:
            status_counts = {}
            for a in appts:
                status_counts[a["status"]] = status_counts.get(a["status"], 0) + 1
            df_status = pd.DataFrame(list(status_counts.items()), columns=["Status", "Count"])
            st.bar_chart(df_status.set_index("Status"))
        else:
            show_info("No appointment data available.")

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("### Recently Registered Patients")
        if patients:
            df = pd.DataFrame([{
                "ID": p["patient_id"],
                "Name": p["full_name"],
                "Age": p["age"],
                "Gender": p["gender"],
                "Phone": p["phone"]
            } for p in patients[:5]])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            show_info("No patients registered.")

    with col4:
        st.markdown("### Recent Bills")
        if bills:
            df = pd.DataFrame([{
                "Bill ID": b["bill_id"],
                "Patient": b["patient_name"],
                "Total": f"₨{b['total_amount']:,.0f}",
                "Status": b["payment_status"]
            } for b in bills[:5]])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            show_info("No billing records.")

def page_patients():
    st.markdown("<div class='section-header'>Patient Management</div>", unsafe_allow_html=True)

    tabs = st.tabs(["• All Patients", "• Add Patient", "• Edit Patient", "• Delete Patient", "• Patient History"])

    with tabs[0]:
        col1, col2 = st.columns([3, 1])
        with col1:
            search = st.text_input("Search patients (name, ID, phone)")
        with col2:
            show_inactive = st.checkbox("Show Inactive")

        patients = Patient.search(search) if search else Patient.get_all(active_only=not show_inactive)

        if patients:
            df = pd.DataFrame([{
                "ID": p["patient_id"],
                "Name": p["full_name"],
                "Age": p["age"],
                "Gender": p["gender"],
                "Blood": p["blood_group"],
                "Phone": p["phone"],
                "Email": p["email"],
                "Registered": p["registered_at"][:10] if p["registered_at"] else "",
                "Active": "✅" if p["is_active"] else "❌"
            } for p in patients])
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Showing {len(patients)} patient(s)")

            col_e, col_j = st.columns(2)
            with col_e: export_to_csv(patients, "patients.csv")
            with col_j: export_to_json(patients, "patients.json")
        else:
            show_info("No patients found.")

    with tabs[1]:
        st.markdown("#### Register New Patient")
        with st.form("add_patient"):
            c1, c2 = st.columns(2)
            with c1:
                name  = st.text_input("Full Name *")
                age   = st.number_input("Age *", 0, 150, 25)
                gender= st.selectbox("Gender *", ["Male", "Female", "Other"])
                blood = st.selectbox("Blood Group", ["A+","A-","B+","B-","AB+","AB-","O+","O-","Unknown"])
            with c2:
                phone  = st.text_input("Phone *")
                email  = st.text_input("Email")
                address= st.text_area("Address", height=68)
                emerg  = st.text_input("Emergency Contact")

            if st.form_submit_button("Register Patient", type="primary"):
                if name and phone:
                    try:
                        pid = Patient.create(name, age, gender, blood, phone, email, address, emerg)
                        log("ADD_PATIENT", f"Registered {name} as {pid}")
                        show_success(f"Patient registered! ID: **{pid}**")
                    except Exception as e:
                        show_error(str(e))
                else:
                    show_error("Name and Phone are required.")

    with tabs[2]:
        st.markdown("#### Edit Patient Details")
        patients_all = Patient.get_all()
        if patients_all:
            options = {f"{p['patient_id']} — {p['full_name']}": p["patient_id"] for p in patients_all}
            selected = st.selectbox("Select Patient", list(options.keys()))
            pid = options[selected]
            p = Patient.get_by_id(pid)
            if p:
                with st.form("edit_patient"):
                    c1, c2 = st.columns(2)
                    with c1:
                        name  = st.text_input("Full Name", value=p["full_name"])
                        age   = st.number_input("Age", 0, 150, p["age"] or 0)
                        gender= st.selectbox("Gender", ["Male","Female","Other"],
                                             index=["Male","Female","Other"].index(p["gender"]) if p["gender"] in ["Male","Female","Other"] else 0)
                        blood = st.selectbox("Blood Group", ["A+","A-","B+","B-","AB+","AB-","O+","O-","Unknown"],
                                             index=["A+","A-","B+","B-","AB+","AB-","O+","O-","Unknown"].index(p["blood_group"]) if p["blood_group"] in ["A+","A-","B+","B-","AB+","AB-","O+","O-","Unknown"] else 8)
                    with c2:
                        phone  = st.text_input("Phone", value=p["phone"] or "")
                        email  = st.text_input("Email", value=p["email"] or "")
                        address= st.text_area("Address", value=p["address"] or "", height=68)
                        emerg  = st.text_input("Emergency Contact", value=p["emergency_contact"] or "")

                    if st.form_submit_button("Save Changes", type="primary"):
                        try:
                            Patient.update(pid, name, age, gender, blood, phone, email, address, emerg)
                            log("EDIT_PATIENT", f"Updated {pid}")
                            show_success("Patient updated successfully!")
                        except Exception as e:
                            show_error(str(e))
        else:
            show_info("No patients available.")

    with tabs[3]:
        st.markdown("#### Delete / Deactivate Patient")
        patients_all = Patient.get_all()
        if patients_all:
            options = {f"{p['patient_id']} — {p['full_name']}": p["patient_id"] for p in patients_all}
            selected = st.selectbox("Select Patient to Delete", list(options.keys()))
            pid = options[selected]

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Deactivate (Soft Delete)", use_container_width=True):
                    Patient.deactivate(pid)
                    log("DEACTIVATE_PATIENT", pid)
                    show_success(f"Patient {pid} deactivated.")
            with col_b:
                if st.button("Permanently Delete", use_container_width=True, type="primary"):
                    Patient.delete(pid)
                    log("DELETE_PATIENT", pid)
                    show_success(f"Patient {pid} deleted permanently.")
                    st.rerun()
        else:
            show_info("No patients to delete.")

    # ── Tab 5: Patient History
    with tabs[4]:
        st.markdown("#### Patient Full History")
        patients_all = Patient.get_all()
        if patients_all:
            options = {f"{p['patient_id']} — {p['full_name']}": p["patient_id"] for p in patients_all}
            selected = st.selectbox("Select Patient for History", list(options.keys()))
            pid = options[selected]
            p = Patient.get_by_id(pid)

            if p:
                info_col, _ = st.columns([2, 1])
                with info_col:
                    st.markdown(f"""
                    | Field | Value |
                    |-------|-------|
                    | **Patient ID** | {p['patient_id']} |
                    | **Name** | {p['full_name']} |
                    | **Age / Gender** | {p['age']} / {p['gender']} |
                    | **Blood Group** | {p['blood_group']} |
                    | **Phone** | {p['phone']} |
                    | **Email** | {p['email']} |
                    | **Address** | {p['address']} |
                    | **Emergency Contact** | {p['emergency_contact']} |
                    | **Registered** | {p['registered_at']} |
                    """)

                st.markdown("##### Appointment History")
                appts = Appointment.get_by_patient(pid)
                if appts:
                    df = pd.DataFrame([{
                        "Appt ID": a["appointment_id"], "Date": a["appointment_date"],
                        "Time": a["appointment_time"], "Doctor": a["doctor_name"],
                        "Reason": a["reason"], "Status": a["status"]
                    } for a in appts])
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    show_info("No appointments found.")

                st.markdown("##### Prescription History")
                rxs = Prescription.get_by_patient(pid)
                if rxs:
                    df = pd.DataFrame([{
                        "RX ID": r["prescription_id"], "Date": r["issued_at"][:10],
                        "Doctor": r["doctor_name"], "Diagnosis": r["diagnosis"],
                        "Medicines": r["medicines"]
                    } for r in rxs])
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    show_info("No prescriptions found.")

                st.markdown("##### Billing History")
                bills = Bill.get_by_patient(pid)
                if bills:
                    df = pd.DataFrame([{
                        "Bill ID": b["bill_id"], "Date": b["billed_at"][:10],
                        "Total": f"₨{b['total_amount']:,.0f}", "Status": b["payment_status"]
                    } for b in bills])
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    show_info("No bills found.")

def page_doctors():
    st.markdown("<div class='section-header'>Doctor Management</div>", unsafe_allow_html=True)

    tabs = st.tabs(["• All Doctors", "• Add Doctor", "• Edit Doctor", "• Delete Doctor"])

    with tabs[0]:
        search = st.text_input("Search doctors (name, ID, specialization)")
        doctors = Doctor.search(search) if search else Doctor.get_all()
        if doctors:
            df = pd.DataFrame([{
                "ID": d["doctor_id"], "Name": d["full_name"],
                "Specialization": d["specialization"], "Qualification": d["qualification"],
                "Experience": f"{d['experience_years']} yrs", "Fee": f"₨{d['fee']:,.0f}",
                "Phone": d["phone"], "Available": "✅" if d["is_available"] else "❌"
            } for d in doctors])
            st.dataframe(df, use_container_width=True, hide_index=True)
            col_e, col_j = st.columns(2)
            with col_e: export_to_csv(doctors, "doctors.csv")
            with col_j: export_to_json(doctors, "doctors.json")
        else:
            show_info("No doctors found.")

    with tabs[1]:
        st.markdown("#### Add New Doctor")
        with st.form("add_doctor"):
            c1, c2 = st.columns(2)
            with c1:
                name   = st.text_input("Full Name *")
                spec   = st.selectbox("Specialization *", [
                    "General Medicine", "Cardiology", "Neurology", "Orthopedics",
                    "Pediatrics", "Gynecology", "Dermatology", "ENT", "Ophthalmology",
                    "Psychiatry", "Radiology", "Oncology", "Urology", "Other"
                ])
                qual   = st.text_input("Qualification (e.g. MBBS, FCPS)")
                exp    = st.number_input("Experience (years)", 0, 60, 1)
            with c2:
                phone  = st.text_input("Phone *")
                email  = st.text_input("Email")
                fee    = st.number_input("Consultation Fee (₨)", 0.0, step=100.0, value=1000.0)

            if st.form_submit_button("Add Doctor", type="primary"):
                if name and phone:
                    try:
                        did = Doctor.create(name, spec, phone, email, qual, exp, fee)
                        log("ADD_DOCTOR", f"Added Dr. {name} as {did}")
                        show_success(f"Doctor added! ID: **{did}**")
                    except Exception as e:
                        show_error(str(e))
                else:
                    show_error("Name and Phone are required.")

    with tabs[2]:
        st.markdown("#### Edit Doctor Details")
        doctors_all = Doctor.get_all()
        if doctors_all:
            options = {f"{d['doctor_id']} — {d['full_name']}": d["doctor_id"] for d in doctors_all}
            selected = st.selectbox("Select Doctor", list(options.keys()))
            did = options[selected]
            d = Doctor.get_by_id(did)
            if d:
                SPECS = ["General Medicine","Cardiology","Neurology","Orthopedics","Pediatrics",
                         "Gynecology","Dermatology","ENT","Ophthalmology","Psychiatry","Radiology","Oncology","Urology","Other"]
                with st.form("edit_doctor"):
                    c1, c2 = st.columns(2)
                    with c1:
                        name  = st.text_input("Full Name", value=d["full_name"])
                        spec  = st.selectbox("Specialization", SPECS,
                                             index=SPECS.index(d["specialization"]) if d["specialization"] in SPECS else len(SPECS)-1)
                        qual  = st.text_input("Qualification", value=d["qualification"] or "")
                        exp   = st.number_input("Experience", 0, 60, d["experience_years"] or 0)
                    with c2:
                        phone = st.text_input("Phone", value=d["phone"] or "")
                        email = st.text_input("Email", value=d["email"] or "")
                        fee   = st.number_input("Fee (₨)", 0.0, step=100.0, value=float(d["fee"] or 0))
                        avail = st.checkbox("Available", value=bool(d["is_available"]))

                    if st.form_submit_button("Save Changes", type="primary"):
                        try:
                            Doctor.update(did, name, spec, phone, email, qual, exp, fee, int(avail))
                            log("EDIT_DOCTOR", f"Updated {did}")
                            show_success("Doctor updated successfully!")
                        except Exception as e:
                            show_error(str(e))

    with tabs[3]:
        st.markdown("#### Delete Doctor")
        doctors_all = Doctor.get_all()
        if doctors_all:
            options = {f"{d['doctor_id']} — {d['full_name']}": d["doctor_id"] for d in doctors_all}
            selected = st.selectbox("Select Doctor to Delete", list(options.keys()))
            did = options[selected]
            if st.button("Delete Doctor", type="primary"):
                Doctor.delete(did)
                log("DELETE_DOCTOR", did)
                show_success(f"Doctor {did} deleted.")
                st.rerun()

def page_appointments():
    st.markdown("<div class='section-header'>Appointment Management</div>", unsafe_allow_html=True)

    tabs = st.tabs(["• All Appointments", "• Book Appointment", "• Edit Appointment", "• Cancel / Delete"])

    with tabs[0]:
        appts = Appointment.get_all()
        status_filter = st.selectbox("Filter by Status", ["All", "Scheduled", "Completed", "Cancelled", "No-Show"])
        if status_filter != "All":
            appts = [a for a in appts if a["status"] == status_filter]

        if appts:
            df = pd.DataFrame([{
                "ID": a["appointment_id"], "Patient": a["patient_name"],
                "Doctor": a["doctor_name"], "Specialization": a["specialization"],
                "Date": a["appointment_date"], "Time": a["appointment_time"],
                "Reason": a["reason"], "Status": a["status"]
            } for a in appts])
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"{len(appts)} appointment(s) shown")
            col_e, col_j = st.columns(2)
            with col_e: export_to_csv(appts, "appointments.csv")
            with col_j: export_to_json(appts, "appointments.json")
        else:
            show_info("No appointments found.")

    with tabs[1]:
        st.markdown("#### Book New Appointment")
        patients = Patient.get_all(active_only=True)
        doctors  = Doctor.get_all(available_only=True)

        if not patients or not doctors:
            show_error("Need at least one active patient and one available doctor.")
        else:
            with st.form("book_appointment"):
                c1, c2 = st.columns(2)
                p_opts = {f"{p['patient_id']} — {p['full_name']}": p["patient_id"] for p in patients}
                d_opts = {f"{d['doctor_id']} — {d['full_name']} ({d['specialization']})": d["doctor_id"] for d in doctors}

                with c1:
                    p_sel = st.selectbox("Patient *", list(p_opts.keys()))
                    appt_date = st.date_input("Date *", min_value=date.today())
                    reason = st.text_input("Reason for Visit *")
                with c2:
                    d_sel  = st.selectbox("Doctor *", list(d_opts.keys()))
                    appt_time = st.time_input("Time *")
                    notes  = st.text_area("Notes", height=68)

                if st.form_submit_button("Book Appointment", type="primary"):
                    if reason:
                        try:
                            aid = Appointment.create(
                                p_opts[p_sel], d_opts[d_sel],
                                str(appt_date), str(appt_time)[:5], reason, notes
                            )
                            log("BOOK_APPOINTMENT", f"Booked {aid}")
                            show_success(f"Appointment booked! ID: **{aid}**")
                        except Exception as e:
                            show_error(str(e))
                    else:
                        show_error("Reason is required.")

    with tabs[2]:
        st.markdown("#### Edit Appointment")
        appts_all = Appointment.get_all()
        if appts_all:
            options = {f"{a['appointment_id']} — {a['patient_name']} @ {a['appointment_date']}": a["appointment_id"] for a in appts_all}
            selected = st.selectbox("Select Appointment", list(options.keys()))
            aid = options[selected]
            appt = next((a for a in appts_all if a["appointment_id"] == aid), None)

            if appt:
                patients = Patient.get_all(active_only=True)
                doctors  = Doctor.get_all()
                p_opts = {f"{p['patient_id']} — {p['full_name']}": p["patient_id"] for p in patients}
                d_opts = {f"{d['doctor_id']} — {d['full_name']}": d["doctor_id"] for d in doctors}
                STATUSES = ["Scheduled", "Completed", "Cancelled", "No-Show"]

                with st.form("edit_appointment"):
                    c1, c2 = st.columns(2)
                    p_keys = list(p_opts.keys())
                    d_keys = list(d_opts.keys())
                    p_match = next((k for k, v in p_opts.items() if v == appt["patient_id"]), p_keys[0])
                    d_match = next((k for k, v in d_opts.items() if v == appt["doctor_id"]), d_keys[0])

                    with c1:
                        p_sel = st.selectbox("Patient", p_keys, index=p_keys.index(p_match))
                        appt_date = st.text_input("Date (YYYY-MM-DD)", value=appt["appointment_date"])
                        reason    = st.text_input("Reason", value=appt["reason"] or "")
                        status    = st.selectbox("Status", STATUSES, index=STATUSES.index(appt["status"]))
                    with c2:
                        d_sel  = st.selectbox("Doctor", d_keys, index=d_keys.index(d_match))
                        appt_time = st.text_input("Time (HH:MM)", value=appt["appointment_time"] or "")
                        notes  = st.text_area("Notes", value=appt["notes"] or "", height=68)

                    if st.form_submit_button("Save Changes", type="primary"):
                        try:
                            Appointment.update(aid, p_opts[p_sel], d_opts[d_sel], appt_date, appt_time, reason, notes, status)
                            log("EDIT_APPOINTMENT", aid)
                            show_success("Appointment updated!")
                        except Exception as e:
                            show_error(str(e))

    with tabs[3]:
        st.markdown("#### Cancel or Delete Appointment")
        appts_all = Appointment.get_all()
        if appts_all:
            options = {f"{a['appointment_id']} — {a['patient_name']} on {a['appointment_date']}": a["appointment_id"] for a in appts_all}
            selected = st.selectbox("Select Appointment", list(options.keys()))
            aid = options[selected]

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Mark as Cancelled", use_container_width=True):
                    Appointment.update_status(aid, "Cancelled")
                    log("CANCEL_APPOINTMENT", aid)
                    show_success("Appointment cancelled.")
            with c2:
                if st.button("Delete Permanently", use_container_width=True, type="primary"):
                    Appointment.delete(aid)
                    log("DELETE_APPOINTMENT", aid)
                    show_success("Appointment deleted.")
                    st.rerun()

def page_prescriptions():
    st.markdown("<div class='section-header'>Prescription Management</div>", unsafe_allow_html=True)

    tabs = st.tabs(["• All Prescriptions", "• Issue Prescription", "• Delete Prescription"])

    with tabs[0]:
        rxs = Prescription.get_all()
        if rxs:
            df = pd.DataFrame([{
                "RX ID": r["prescription_id"], "Patient": r["patient_name"],
                "Doctor": r["doctor_name"], "Diagnosis": r["diagnosis"],
                "Medicines": r["medicines"], "Follow-up": r["follow_up_date"],
                "Issued": r["issued_at"][:10]
            } for r in rxs])
            st.dataframe(df, use_container_width=True, hide_index=True)
            col_e, col_j = st.columns(2)
            with col_e: export_to_csv(rxs, "prescriptions.csv")
            with col_j: export_to_json(rxs, "prescriptions.json")
        else:
            show_info("No prescriptions found.")

    with tabs[1]:
        st.markdown("#### Issue New Prescription")
        appts = [a for a in Appointment.get_all() if a["status"] in ("Scheduled", "Completed")]
        patients = Patient.get_all(active_only=True)
        doctors  = Doctor.get_all(available_only=True)

        if not patients or not doctors:
            show_error("Need patients and doctors.")
        else:
            with st.form("issue_rx"):
                p_opts = {f"{p['patient_id']} — {p['full_name']}": p["patient_id"] for p in patients}
                d_opts = {f"{d['doctor_id']} — {d['full_name']}": d["doctor_id"] for d in doctors}
                a_opts = {"None (Walk-in)": None}
                a_opts.update({f"{a['appointment_id']} — {a['patient_name']} ({a['appointment_date']})": a["appointment_id"] for a in appts})

                c1, c2 = st.columns(2)
                with c1:
                    p_sel     = st.selectbox("Patient *", list(p_opts.keys()))
                    d_sel     = st.selectbox("Doctor *", list(d_opts.keys()))
                    a_sel     = st.selectbox("Linked Appointment", list(a_opts.keys()))
                    diagnosis = st.text_input("Diagnosis *")
                with c2:
                    medicines = st.text_area("Medicines (one per line) *", height=100)
                    instructions = st.text_area("Instructions", height=68)
                    follow_up = st.date_input("Follow-up Date", value=None)

                if st.form_submit_button("Issue Prescription", type="primary"):
                    if diagnosis and medicines:
                        try:
                            rxid = Prescription.create(
                                a_opts[a_sel], p_opts[p_sel], d_opts[d_sel],
                                diagnosis, medicines, instructions, str(follow_up) if follow_up else ""
                            )
                            log("ISSUE_PRESCRIPTION", f"Issued {rxid}")
                            show_success(f"Prescription issued! ID: **{rxid}**")
                        except Exception as e:
                            show_error(str(e))
                    else:
                        show_error("Diagnosis and Medicines are required.")

    with tabs[2]:
        rxs = Prescription.get_all()
        if rxs:
            options = {f"{r['prescription_id']} — {r['patient_name']}": r["prescription_id"] for r in rxs}
            selected = st.selectbox("Select Prescription to Delete", list(options.keys()))
            rxid = options[selected]
            if st.button("Delete Prescription", type="primary"):
                Prescription.delete(rxid)
                log("DELETE_PRESCRIPTION", rxid)
                show_success("Prescription deleted.")
                st.rerun()
        else:
            show_info("No prescriptions to delete.")

def page_billing():
    st.markdown("<div class='section-header'>Billing & Payments</div>", unsafe_allow_html=True)

    tabs = st.tabs(["• All Bills", "• Generate Bill", "• Update Payment", "• Delete Bill", "• Revenue Report"])

    with tabs[0]:
        bills = Bill.get_all()
        status_filter = st.selectbox("Filter", ["All", "Paid", "Pending", "Partially Paid"])
        if status_filter != "All":
            bills = [b for b in bills if b["payment_status"] == status_filter]

        if bills:
            df = pd.DataFrame([{
                "Bill ID": b["bill_id"], "Patient": b["patient_name"],
                "Consult Fee": f"₨{b['consultation_fee']:,.0f}",
                "Medicine": f"₨{b['medicine_charge']:,.0f}",
                "Lab": f"₨{b['lab_charge']:,.0f}",
                "Total": f"₨{b['total_amount']:,.0f}",
                "Method": b["payment_method"], "Status": b["payment_status"],
                "Date": b["billed_at"][:10]
            } for b in bills])
            st.dataframe(df, use_container_width=True, hide_index=True)
            total = sum(b["total_amount"] for b in bills)
            st.markdown(f"**Total: ₨{total:,.0f}**")
            col_e, col_j = st.columns(2)
            with col_e: export_to_csv(bills, "bills.csv")
            with col_j: export_to_json(bills, "bills.json")
        else:
            show_info("No bills found.")

    with tabs[1]:
        st.markdown("#### Generate New Bill")
        patients = Patient.get_all(active_only=True)
        if patients:
            with st.form("gen_bill"):
                p_opts = {f"{p['patient_id']} — {p['full_name']}": p["patient_id"] for p in patients}
                appts  = Appointment.get_all()
                a_opts = {"None": None}
                a_opts.update({f"{a['appointment_id']} ({a['appointment_date']})": a["appointment_id"] for a in appts})

                c1, c2 = st.columns(2)
                with c1:
                    p_sel   = st.selectbox("Patient *", list(p_opts.keys()))
                    a_sel   = st.selectbox("Appointment", list(a_opts.keys()))
                    consult = st.number_input("Consultation Fee (₨)", 0.0, step=100.0)
                    medicine= st.number_input("Medicine Charges (₨)", 0.0, step=50.0)
                with c2:
                    lab     = st.number_input("Lab Charges (₨)", 0.0, step=50.0)
                    other   = st.number_input("Other Charges (₨)", 0.0, step=50.0)
                    method  = st.selectbox("Payment Method", ["Cash", "Card", "Bank Transfer", "Insurance"])
                    total   = consult + medicine + lab + other
                    st.metric("Total Amount", f"₨{total:,.0f}")

                if st.form_submit_button("Generate Bill", type="primary"):
                    try:
                        bid, total_amt = Bill.create(p_opts[p_sel], a_opts[a_sel], consult, medicine, lab, other, method)
                        log("GENERATE_BILL", f"Bill {bid} = ₨{total_amt}")
                        show_success(f"Bill generated! ID: **{bid}** | Total: ₨{total_amt:,.0f}")
                    except Exception as e:
                        show_error(str(e))

    with tabs[2]:
        st.markdown("#### Update Payment Status")
        bills = Bill.get_all()
        if bills:
            options = {f"{b['bill_id']} — {b['patient_name']} (₨{b['total_amount']:,.0f})": b["bill_id"] for b in bills}
            selected = st.selectbox("Select Bill", list(options.keys()))
            bid = options[selected]
            new_status = st.selectbox("New Status", ["Paid", "Pending", "Partially Paid"])
            if st.button("Update Status", type="primary"):
                Bill.update_status(bid, new_status)
                log("UPDATE_BILL_STATUS", f"{bid} → {new_status}")
                show_success(f"Bill {bid} status updated to {new_status}.")

    with tabs[3]:
        bills = Bill.get_all()
        if bills:
            options = {f"{b['bill_id']} — {b['patient_name']}": b["bill_id"] for b in bills}
            selected = st.selectbox("Select Bill to Delete", list(options.keys()))
            bid = options[selected]
            if st.button("Delete Bill", type="primary"):
                Bill.delete(bid)
                log("DELETE_BILL", bid)
                show_success("Bill deleted.")
                st.rerun()

    with tabs[4]:
        st.markdown("#### Revenue Report")
        bills = Bill.get_all()
        if bills:
            paid       = [b for b in bills if b["payment_status"] == "Paid"]
            pending    = [b for b in bills if b["payment_status"] == "Pending"]
            partial    = [b for b in bills if b["payment_status"] == "Partially Paid"]

            c1, c2, c3 = st.columns(3)
            with c1: st.metric("Total Collected", f"₨{sum(b['total_amount'] for b in paid):,.0f}")
            with c2: st.metric("Pending", f"₨{sum(b['total_amount'] for b in pending):,.0f}")
            with c3: st.metric("Total Bills", len(bills))

            df_revenue = pd.DataFrame([{"Date": b["billed_at"][:10], "Amount": b["total_amount"]} for b in paid])
            if not df_revenue.empty:
                df_revenue = df_revenue.groupby("Date")["Amount"].sum().reset_index()
                st.markdown("**Daily Revenue (Paid Bills)**")
                st.bar_chart(df_revenue.set_index("Date"))

def page_activity_log():
    st.markdown("<div class='section-header'>Activity Log</div>", unsafe_allow_html=True)

    db = Database().get_connection()
    logs = db.execute("SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT 200").fetchall()

    if logs:
        df = pd.DataFrame([{
            "Time": l["timestamp"], "User": l["user"],
            "Action": l["action"], "Details": l["details"]
        } for l in logs])
        st.dataframe(df, use_container_width=True, hide_index=True)
        export_to_csv(logs, "activity_log.csv")
    else:
        show_info("No activity recorded yet.")

def page_users():
    if st.session_state.user.role != "admin":
        show_error("Access denied. Admin only.")
        return

    st.markdown("<div class='section-header'>User Management</div>", unsafe_allow_html=True)

    tabs = st.tabs(["• All Users", "• Add User", "• Delete User", "• Change Password"])

    with tabs[0]:
        users = User.get_all()
        if users:
            df = pd.DataFrame([{
                "ID": u["id"], "Username": u["username"],
                "Full Name": u["full_name"], "Role": u["role"],
                "Created": u["created_at"][:10] if u["created_at"] else ""
            } for u in users])
            st.dataframe(df, use_container_width=True, hide_index=True)

    with tabs[1]:
        with st.form("add_user"):
            c1, c2 = st.columns(2)
            with c1:
                uname  = st.text_input("Username *")
                role   = st.selectbox("Role *", ["admin", "doctor", "receptionist"])
            with c2:
                fname  = st.text_input("Full Name *")
                pwd    = st.text_input("Password *", type="password")
                cpwd   = st.text_input("Confirm Password *", type="password")

            if st.form_submit_button("Add User", type="primary"):
                if uname and fname and pwd:
                    if pwd != cpwd:
                        show_error("Passwords do not match.")
                    else:
                        try:
                            User.create(uname, pwd, role, fname)
                            log("ADD_USER", f"Added {uname} as {role}")
                            show_success(f"User '{uname}' created!")
                        except Exception as e:
                            show_error(f"Error: {e}")
                else:
                    show_error("All fields required.")

    with tabs[2]:
        users = User.get_all()
        current_id = st.session_state.user.id
        deletable  = [u for u in users if u["id"] != current_id]
        if deletable:
            options = {f"{u['username']} ({u['role']})": u["id"] for u in deletable}
            selected = st.selectbox("Select User to Delete", list(options.keys()))
            uid = options[selected]
            if st.button("Delete User", type="primary"):
                User.delete(uid)
                log("DELETE_USER", f"Deleted user ID {uid}")
                show_success("User deleted.")
                st.rerun()
        else:
            show_info("No other users to delete.")

    with tabs[3]:
        users = User.get_all()
        options = {f"{u['username']} ({u['role']})": u["id"] for u in users}
        selected = st.selectbox("Select User", list(options.keys()))
        uid = options[selected]
        new_pwd  = st.text_input("New Password", type="password")
        cnf_pwd  = st.text_input("Confirm New Password", type="password")
        if st.button("Change Password", type="primary"):
            if new_pwd and new_pwd == cnf_pwd:
                User.change_password(uid, new_pwd)
                log("CHANGE_PASSWORD", f"Changed password for user ID {uid}")
                show_success("Password changed successfully.")
            else:
                show_error("Passwords don't match or empty.")

def main():
    if not st.session_state.logged_in:
        login_page()
        return

    sidebar()

    page = st.session_state.page
    if   page == "Dashboard":    page_dashboard()
    elif page == "Patients":     page_patients()
    elif page == "Doctors":      page_doctors()
    elif page == "Appointments": page_appointments()
    elif page == "Prescriptions":page_prescriptions()
    elif page == "Billing":      page_billing()
    elif page == "Activity Log": page_activity_log()
    elif page == "Users":        page_users()

if __name__ == "__main__":
    main()
