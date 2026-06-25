# Dooper Medical Report Analyzer

A production-ready, beautiful, and secure **AI Medical Report Analyzer** web application. Built using a light, high-performance stack suitable for a second-year CSE student project, easy to explain during interview presentations. 

---

## 🌟 Features & Highlights

- **JWT Authentication:** Secure user registration and login. Sessions are kept safe using secure, HTTP-only JWT cookies, protecting dashboards from unauthenticated sessions.
- **Dooper Healthcare UI:** White background, deep blue branding color palette, rounded buttons, card layouts, smooth transitions, and a responsive structure built with pure, native CSS and HTML (no bulky UI frameworks).
- **Automated Biomarker Parser (AI Rules):** Scans report text using regular expressions to extract parameters for Hemoglobin, Blood Sugar, Cholesterol (HDL, LDL, Triglycerides), TSH, Platelets, RBC, WBC, Creatinine, Liver functions (ALT, AST, Bilirubin), and Kidney markers (BUN).
- **Clinical Severity Assessment:** Automatically rates reports as 🟢 **Normal**, 🟡 **Moderate**, or 🔴 **Critical** by matching parsed data values to clinical reference thresholds.
- **Interactive Reports History:** Search reports by name or biomarkers, filter by severity tags, sort by dates/alphabetical order, and delete stored entries.
- **Visual Analytics (Charts):** Visualizes health statuses in real time:
  - **Pie Chart:** Distribution of normal, moderate, and critical files.
  - **Bar Chart:** Frequency breakdown of specific abnormal biomarkers.
- **Interactive PDF Download:** High-quality clinical analysis summaries generated directly by Python on the server using `reportlab`.
- **Speech Synthesis (Voice Summary):** Reads summaries out loud directly inside the browser using the native Web Speech API.
- **Critical Email Alerts:** Sends direct email alerts to users when a report with critical biomarkers is processed (automatically falls back to console logging if SMTP servers are not configured).
- **Dark Mode Support:** A fully integrated dark mode theme that syncs with `localStorage` and toggles seamlessly on the navbar.
- **Robust OCR Fallback System:** Uses `pypdf` for parsing PDF files and `pytesseract` for images. If Tesseract is not installed on the local system, the program gracefully triggers a smart simulator based on report filenames, allowing seamless testing out-of-the-box.

---

## 📂 Project Folder Structure

```text
medical-report-analyzer/
│
├── app.py                  # Flask Application initialization
├── database.py             # SQLite connection helper & table migrations
├── models.py               # Parameterized user & report queries
├── routes.py               # JWT cookie-protected page views and API routing
├── utils.py                # Text extraction (OCR), AI rule checks, PDF & Email builders
├── requirements.txt        # Backend dependencies list
├── runtime.txt             # Python engine runtime version
├── Procfile                # WSGI command for Render deployment
├── .env.example            # Environment variables blueprint
├── README.md               # User manual and setup documentation
│
├── database/
│   └── medical.db          # SQLite Database file (created on startup)
│
├── uploads/                # Directory containing uploaded report files
│
├── static/
│   ├── css/
│   │   ├── style.css       # Design variables, typography, navigation, toast styles
│   │   ├── login.css       # Forms card adjustments
│   │   ├── dashboard.css   # Metrics panels, file zones, charts frames
│   │   ├── history.css     # Toolbars, tables, detailed analysis drawer
│   │   └── profile.css     # Settings form styles
│   │
│   └── js/
│       ├── login.js        # Authentication validation
│       ├── dashboard.js    # Drag-and-drop, Chart.js, mock triggers
│       ├── history.js      # Filter search events, PDF clicks, Speech synthesis API
│       └── profile.js      # Password configurations, user profile fetcher
│
└── templates/
    ├── login.html          # Login card page template
    ├── register.html       # Register card page template
    ├── dashboard.html      # User analytics dashboard
    ├── history.html        # Interactive report query journal
    └── profile.html        # Settings configurations view
```

---

## 🛠️ Installation & Setup (Local)

### 1. Prerequisite: Python
Make sure you have Python 3.8+ installed. You can check your version by running:
```bash
python --version
```

### 2. Clone/Copy the Code
Download and unzip all files into a directory (e.g., `report-analyzer`).

### 3. Create a Virtual Environment
Navigate to the project root and spin up a clean virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
Install all package requirements listed in `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 5. Setup Configuration
Copy the `.env.example` file to `.env`:
```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# macOS / Linux / Command Prompt
cp .env.example .env
```

Open `.env` and set at least the following values:
```text
SECRET_KEY=replace-with-a-secure-secret
DEBUG=False
```

Optional environment variables:
```text
TESSERACT_CMD=     # Optional: path to tesseract binary if installed
SMTP_SERVER=
SMTP_PORT=
SMTP_USER=
SMTP_PASS=
SENDER_EMAIL=alerts@dooper-reports.com
```

*(The app can run without SMTP configured; critical alerts will be printed to the server log instead.)*

### 6. Run the Application
Start the Flask server:
```bash
python app.py
```
On startup, the application will automatically create `database/medical.db` and initialize the schema. Open your browser at:
```text
http://127.0.0.1:5000/
```

---

## 💡 Quick Demo Tips (No Files Needed!)

Since local machines may not have Tesseract OCR binaries installed, we have built a **demo helper system** directly into the upload card. 

1. Create a user account on the **Register** page and log in.
2. Under the **Upload** card on the dashboard, look at the **"Try with demo reports"** buttons.
3. Click any of the three buttons:
   - **Normal Health Report:** Creates a report where all biomarkers (Hemoglobin, Glucose, Vit D, etc.) are normal. Displays a green badge.
   - **Moderate Pre-Diabetic Report:** Creates a report with borderline elevated glucose and cholesterol levels. Displays a yellow badge.
   - **Critical Anemic & Kidney Report:** Creates a report with critically low hemoglobin and platelets, high creatinine, and abnormal liver enzymes. Displays a red badge, lists alerts, and prints an email notification payload in your backend terminal!
4. Review the details in the history tab, trigger the Speech API to read the clinical summaries out loud, and download the high-quality server-generated PDF.

---

## 🚀 Deployment Steps (Render)

1. Create a new GitHub Repository and push the project files.
2. Sign in to [Render](https://render.com/) and click **New > Web Service**.
3. Link your GitHub repository.
4. Set the following parameters:
   - **Name:** `medical-report-analyzer`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Click **Advanced**, and add your environment variables matching `.env.example` (like `SECRET_KEY`).
6. Click **Deploy**. Render will read the `Procfile` and deploy your application online.
