# ==========================================
# PREDICTX AI - FINAL STABLE VERSION
# ==========================================

import gradio as gr
import numpy as np
import pandas as pd
import joblib
import random
import plotly.graph_objects as go
import shap
import sqlite3
import smtplib

from datetime import datetime
from email.mime.text import MIMEText

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet

# ==========================================
# LOAD MODEL & SCALER
# ==========================================

model = joblib.load("models/best_model.pkl")
scaler = joblib.load("models/scaler.pkl")

# ==========================================
# SHAP EXPLAINER
# ==========================================

explainer = shap.Explainer(model)

# ==========================================
# DATABASE CONNECTION
# ==========================================

conn = sqlite3.connect(
    "machine_data.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""

CREATE TABLE IF NOT EXISTS predictions (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    timestamp TEXT,

    machine_type REAL,

    air_temp REAL,

    process_temp REAL,

    rpm REAL,

    torque REAL,

    tool_wear REAL,

    failure_probability REAL,

    risk_level TEXT,

    prediction TEXT

)

""")

conn.commit()

# ==========================================
# EMAIL CONFIG
# ==========================================

SENDER_EMAIL = "Sagarjam321@gmail.com"

APP_PASSWORD = "cioz qklv sefy txgi"

RECEIVER_EMAIL = "Sagarjam321@gmail.com"

# ==========================================
# USER DATABASE
# ==========================================

users_db = {
    "admin": "predictx123"
}

# ==========================================
# LOGIN FUNCTION
# ==========================================

def login(username, password):

    if username in users_db and users_db[username] == password:

        return (
            gr.update(visible=False),
            gr.update(visible=True),
            "✅ Login Successful"
        )

    else:

        return (
            gr.update(visible=True),
            gr.update(visible=False),
            "❌ Invalid Username or Password"
        )

# ==========================================
# SIGNUP FUNCTION
# ==========================================

def signup(username, password):

    if username in users_db:

        return "❌ Username already exists"

    if len(username) < 3:

        return "❌ Username too short"

    if len(password) < 4:

        return "❌ Password too short"

    users_db[username] = password

    return "✅ Signup Successful! Please Login."

# ==========================================
# GAUGE FUNCTION
# ==========================================

def create_gauge(value, title, min_val, max_val):

    fig = go.Figure(go.Indicator(

        mode="gauge+number",

        value=value,

        title={'text': title},

        gauge={

            'axis': {'range': [min_val, max_val]},

            'bar': {'color': "cyan"},

            'steps': [

                {
                    'range': [min_val, max_val * 0.5],
                    'color': "#22c55e"
                },

                {
                    'range': [max_val * 0.5, max_val * 0.8],
                    'color': "#facc15"
                },

                {
                    'range': [max_val * 0.8, max_val],
                    'color': "#ef4444"
                }
            ]
        }
    ))

    fig.update_layout(
        paper_bgcolor="#0f172a",
        font={'color': "white"},
        height=280
    )

    return fig

# ==========================================
# RANDOM SENSOR DATA
# ==========================================

def generate_live_data():

    return (
        random.randint(0, 2),
        random.randint(295, 320),
        random.randint(305, 340),
        random.randint(1200, 1800),
        random.randint(20, 70),
        random.randint(0, 250),
        random.randint(0, 1),
        random.randint(0, 1),
        random.randint(0, 1),
        random.randint(0, 1),
        random.randint(0, 1)
    )

# ==========================================
# SHAP EXPLANATION
# ==========================================

def generate_shap_explanation(input_scaled):

    shap_values = explainer(input_scaled)

    feature_names = [
        'Type',
        'Air Temp',
        'Process Temp',
        'RPM',
        'Torque',
        'Tool Wear',
        'TWF',
        'HDF',
        'PWF',
        'OSF',
        'RNF'
    ]

    impacts = shap_values.values[0]

    explanation = []

    for feature, impact in zip(feature_names, impacts):

        if abs(impact) > 0.1:

            if impact > 0:

                explanation.append(
                    f"🔺 {feature} increased failure risk"
                )

            else:

                explanation.append(
                    f"🔻 {feature} reduced failure risk"
                )

    if len(explanation) == 0:

        explanation.append(
            "✅ No major risk factors detected."
        )

    return "\n".join(explanation)

# ==========================================
# LOAD DATABASE DATA
# ==========================================

def load_database_data():

    df = pd.read_sql_query(
        "SELECT * FROM predictions ORDER BY id DESC LIMIT 10",
        conn
    )

    return df

# ==========================================
# EMAIL ALERT FUNCTION
# ==========================================

def send_alert_email(probability, rpm, torque):

    try:

        subject = "⚠️ PredictX AI Alert"

        body = f"""

ALERT: High Machine Failure Risk Detected

Failure Probability: {probability:.2%}

RPM: {rpm}

Torque: {torque}

Immediate maintenance recommended.

"""

        msg = MIMEText(body)

        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL

        server = smtplib.SMTP(
            'smtp.gmail.com',
            587
        )

        server.starttls()

        server.login(
            SENDER_EMAIL,
            APP_PASSWORD
        )

        server.send_message(msg)

        server.quit()

    except Exception as e:

        print("Email Error:", e)

# ==========================================
# PDF REPORT GENERATOR
# ==========================================

def generate_pdf_report(
    status,
    probability,
    risk,
    rpm,
    torque,
    air_temp,
    process_temp
):

    file_name = "PredictX_AI_Report.pdf"

    doc = SimpleDocTemplate(file_name)

    styles = getSampleStyleSheet()

    elements = []

    title = Paragraph(
        "PredictX AI Report",
        styles['Title']
    )

    elements.append(title)

    elements.append(Spacer(1, 20))

    report_data = f"""

    <b>Machine Status:</b> {status}<br/><br/>

    <b>Failure Probability:</b> {probability}<br/><br/>

    <b>Risk Level:</b> {risk}<br/><br/>

    <b>RPM:</b> {rpm}<br/><br/>

    <b>Torque:</b> {torque}<br/><br/>

    <b>Air Temperature:</b> {air_temp}<br/><br/>

    <b>Process Temperature:</b> {process_temp}<br/><br/>

    <b>Generated Time:</b> {datetime.now()}

    """

    paragraph = Paragraph(
        report_data,
        styles['BodyText']
    )

    elements.append(paragraph)

    doc.build(elements)

    return file_name

# ==========================================
# MAIN PREDICTION FUNCTION
# ==========================================

def predict_failure(
    machine_type,
    air_temp,
    process_temp,
    rpm,
    torque,
    tool_wear,
    twf,
    hdf,
    pwf,
    osf,
    rnf
):

    try:

        input_data = np.array([[
            float(machine_type),
            float(air_temp),
            float(process_temp),
            float(rpm),
            float(torque),
            float(tool_wear),
            float(twf),
            float(hdf),
            float(pwf),
            float(osf),
            float(rnf)
        ]])

        input_scaled = scaler.transform(input_data)

        prediction = model.predict(input_scaled)[0]

        probability = model.predict_proba(input_scaled)[0][1]

        if probability > 0.80:

            send_alert_email(
                probability,
                rpm,
                torque
            )

        if prediction == 1:
            status = "⚠️ MACHINE FAILURE LIKELY"
        else:
            status = "✅ MACHINE OPERATING NORMALLY"

        if probability < 0.30:
            risk = "🟢 LOW RISK"

        elif probability < 0.70:
            risk = "🟠 MEDIUM RISK"

        else:
            risk = "🔴 HIGH RISK"

        shap_text = generate_shap_explanation(input_scaled)

        sensor_df = pd.DataFrame({

            "Sensor": [
                "Air Temp",
                "Process Temp",
                "RPM",
                "Torque",
                "Tool Wear"
            ],

            "Value": [
                air_temp,
                process_temp,
                rpm,
                torque,
                tool_wear
            ]
        })

        current_time = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        cursor.execute("""

        INSERT INTO predictions (

            timestamp,
            machine_type,
            air_temp,
            process_temp,
            rpm,
            torque,
            tool_wear,
            failure_probability,
            risk_level,
            prediction

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

        """, (

            current_time,
            float(machine_type),
            float(air_temp),
            float(process_temp),
            float(rpm),
            float(torque),
            float(tool_wear),
            float(probability),
            risk,
            status

        ))

        conn.commit()

        db_data = load_database_data()

        rpm_fig = create_gauge(
            float(rpm),
            "RPM",
            0,
            2000
        )

        temp_fig = create_gauge(
            float(process_temp),
            "Temperature",
            250,
            400
        )

        torque_fig = create_gauge(
            float(torque),
            "Torque",
            0,
            100
        )

        probability_fig = create_gauge(
            probability * 100,
            "Failure Probability %",
            0,
            100
        )

        return (
            status,
            f"{probability:.2%}",
            risk,
            shap_text,
            sensor_df,
            db_data,
            rpm_fig,
            temp_fig,
            torque_fig,
            probability_fig
        )

    except Exception as e:

        error_message = f"Error: {str(e)}"

        empty_df = pd.DataFrame()

        empty_fig = go.Figure()

        return (
            error_message,
            error_message,
            error_message,
            error_message,
            empty_df,
            empty_df,
            empty_fig,
            empty_fig,
            empty_fig,
            empty_fig
        )

# ==========================================
# CUSTOM CSS
# ==========================================

custom_css = """

body {
    background-color: #020617;
}

.gradio-container {
    background: linear-gradient(135deg, #020617, #0f172a);
    color: white;
    max-width: 95% !important;
}

h1 {
    text-align: center;
    color: #38bdf8;
    font-size: 50px;
    font-weight: bold;
}

h3 {
    text-align: center;
    color: #94a3b8;
}

button {
    border-radius: 15px !important;
    height: 55px !important;
    font-size: 18px !important;
}

"""

# ==========================================
# UI
# ==========================================

with gr.Blocks(
    css=custom_css,
    theme=gr.themes.Soft()
) as demo:

    with gr.Column(visible=True) as login_page:

        gr.Markdown("""

# 🔐 PredictX AI Login

### Secure Industrial Monitoring Access

""")

        username_input = gr.Textbox(label="Username")

        password_input = gr.Textbox(
            label="Password",
            type="password"
        )

        login_button = gr.Button("🔓 Login")

        signup_button = gr.Button("📝 Sign Up")

        login_status = gr.Textbox(
            label="Login Status"
        )

        signup_status = gr.Textbox(
            label="Signup Status"
        )

    with gr.Column(visible=False) as dashboard:

        gr.Markdown("""

# ⚡ PredictX AI

### 🚀 Intelligent Predictive Maintenance & Industrial Monitoring Platform

""")

        with gr.Row():

            with gr.Column():

                machine_type = gr.Textbox(value="1", label="Machine Type")
                air_temp = gr.Textbox(value="300", label="🌡️ Air Temperature")
                process_temp = gr.Textbox(value="310", label="🔥 Process Temperature")
                rpm = gr.Textbox(value="1500", label="⚙️ RPM")
                torque = gr.Textbox(value="40", label="🔩 Torque")
                tool_wear = gr.Textbox(value="10", label="🛠️ Tool Wear")

            with gr.Column():

                twf = gr.Textbox(value="0", label="TWF")
                hdf = gr.Textbox(value="0", label="HDF")
                pwf = gr.Textbox(value="0", label="PWF")
                osf = gr.Textbox(value="0", label="OSF")
                rnf = gr.Textbox(value="0", label="RNF")

                random_btn = gr.Button("🎲 Generate Live Sensor Data")

                predict_btn = gr.Button(
                    "🚀 Predict Machine Status",
                    variant="primary"
                )

                download_btn = gr.Button("📄 Download AI Report")

                pdf_output = gr.File(label="Download PDF")

        gr.Markdown("---")

        with gr.Row():

            status_output = gr.Textbox(label="Machine Status")
            probability_output = gr.Textbox(label="Failure Probability")
            risk_output = gr.Textbox(label="Risk Level")

        with gr.Tabs():

            with gr.Tab("🧠 AI Explainability"):

                shap_output = gr.Textbox(
                    label="AI Explainability",
                    lines=10
                )

            with gr.Tab("📊 Sensor Overview"):

                sensor_output = gr.Dataframe(
                    label="Sensor Data"
                )

            with gr.Tab("🗄️ Prediction History"):

                database_output = gr.Dataframe(
                    label="Stored Predictions"
                )

            with gr.Tab("📈 Live Gauges"):

                with gr.Row():

                    rpm_gauge = gr.Plot(label="RPM Gauge")
                    temp_gauge = gr.Plot(label="Temperature Gauge")

                with gr.Row():

                    torque_gauge = gr.Plot(label="Torque Gauge")
                    probability_gauge = gr.Plot(label="Failure Probability Gauge")

        random_btn.click(
            fn=generate_live_data,
            inputs=[],
            outputs=[
                machine_type,
                air_temp,
                process_temp,
                rpm,
                torque,
                tool_wear,
                twf,
                hdf,
                pwf,
                osf,
                rnf
            ]
        )

        predict_btn.click(
            fn=predict_failure,
            inputs=[
                machine_type,
                air_temp,
                process_temp,
                rpm,
                torque,
                tool_wear,
                twf,
                hdf,
                pwf,
                osf,
                rnf
            ],
            outputs=[
                status_output,
                probability_output,
                risk_output,
                shap_output,
                sensor_output,
                database_output,
                rpm_gauge,
                temp_gauge,
                torque_gauge,
                probability_gauge
            ]
        )

        download_btn.click(
            fn=generate_pdf_report,
            inputs=[
                status_output,
                probability_output,
                risk_output,
                rpm,
                torque,
                air_temp,
                process_temp
            ],
            outputs=[pdf_output]
        )

    login_button.click(
        fn=login,
        inputs=[
            username_input,
            password_input
        ],
        outputs=[
            login_page,
            dashboard,
            login_status
        ]
    )

    signup_button.click(
        fn=signup,
        inputs=[
            username_input,
            password_input
        ],
        outputs=[
            signup_status
        ]
    )

# ==========================================
# RUN APP
# ==========================================

demo.launch(
    server_name="0.0.0.0",
    server_port=7860
)