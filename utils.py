import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pypdf import PdfReader
from PIL import Image

try:
    import pytesseract
    _tesseract_cmd = os.environ.get('TESSERACT_CMD', r'C:\Program Files\Tesseract-OCR\tesseract.exe')
    pytesseract.pytesseract.tesseract_cmd = _tesseract_cmd
    TESSERACT_OK = True
except Exception:
    pytesseract = None
    TESSERACT_OK = False


# --- OCR & Text Extraction ---

def extract_text_from_pdf(file_path):
    """Extract text from PDF using pypdf. Scanned PDFs return empty string on Render (no Tesseract)."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
        if len(text.strip()) > 50:
            return text.strip()
    except Exception as e:
        print(f"pypdf failed: {e}")
    return ""


def extract_text_from_image(file_path):
    """Extract text from image using Tesseract OCR. Falls back gracefully if not available."""
    if not TESSERACT_OK:
        print("Tesseract not available on this server.")
        return ""
    try:
        img = Image.open(file_path)
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')
        text = pytesseract.image_to_string(img, config='--psm 6 --oem 3')
        if text.strip():
            print(f"Image OCR successful: {len(text)} chars.")
            return text.strip()
    except Exception as e:
        print(f"Image OCR failed: {e}")
    return ""


# --- Suggestion Engine ---

SUGGESTIONS = {
    "Hemoglobin": {
        "Low":     "Increase iron-rich foods (spinach, lentils, red meat). Take iron + Vitamin C supplements. Consult a hematologist.",
        "Critical": "Urgent: Visit a doctor immediately. Severe anemia may require iron infusion or blood transfusion.",
        "High":    "Stay well hydrated. Rule out polycythemia. Consult a physician."
    },
    "Glucose": {
        "Low":     "Eat small frequent meals. Carry glucose tablets. Avoid skipping meals. Consult doctor if recurring.",
        "High":    "Reduce sugar and refined carbs. Exercise 30 min daily. Monitor fasting glucose. Consult an endocrinologist.",
        "Critical": "Urgent: Consult a diabetologist immediately. Fasting sugar in diabetic range requires medical treatment."
    },
    "Vitamin D": {
        "Low":     "Take Vitamin D3 supplements (1000-2000 IU/day). Get 15-20 min of sunlight daily. Eat fatty fish and eggs.",
        "Critical": "Severe deficiency — start high-dose Vitamin D3 (60,000 IU/week) under doctor supervision."
    },
    "Vitamin B12": {
        "Low":     "Take B12 supplements or B12 injections. Eat eggs, dairy, and meat. Vegetarians are at higher risk — supplement regularly."
    },
    "Cholesterol": {
        "High":    "Avoid fried foods and trans fats. Eat oats, nuts, and olive oil. Exercise regularly. Recheck in 3 months.",
        "Critical": "Very high cholesterol — consult a cardiologist. Statin medication may be required."
    },
    "HDL": {
        "Low":     "Exercise regularly (aerobic activity). Quit smoking. Eat healthy fats (avocado, nuts). HDL should be above 40 mg/dL."
    },
    "LDL": {
        "High":    "Reduce saturated fats and processed foods. Add soluble fiber to diet. Consult doctor about statin therapy.",
        "Critical": "Very high LDL — cardiovascular risk is elevated. Consult cardiologist for medication."
    },
    "Triglycerides": {
        "High":    "Avoid sugar, alcohol, and refined carbs. Eat omega-3 rich foods (fish oil). Exercise 5 days/week."
    },
    "TSH": {
        "Low":     "Low TSH may indicate hyperthyroidism. Consult an endocrinologist for thyroid function tests (T3/T4).",
        "High":    "High TSH may indicate hypothyroidism. Consult endocrinologist. Thyroxine (T4) medication may be needed."
    },
    "Platelets": {
        "Low":     "Avoid aspirin and NSAIDs. Rest and monitor for unusual bruising/bleeding. Consult a hematologist.",
        "Critical": "Critically low platelets — risk of internal bleeding. Seek emergency care immediately.",
        "High":    "High platelets can increase clot risk. Stay hydrated. Consult physician."
    },
    "RBC": {
        "Low":     "May indicate anemia. Increase iron and B12 intake. Consult hematologist for further workup.",
        "High":    "High RBC can thicken blood. Stay hydrated. Rule out polycythemia with doctor."
    },
    "WBC": {
        "Low":     "Low WBC reduces immunity. Avoid crowded places. Consult doctor — could indicate bone marrow issue.",
        "High":    "Elevated WBC suggests infection or inflammation. Consult doctor for differential count.",
        "Critical": "Critically abnormal WBC — urgent medical evaluation needed. May indicate serious infection or blood disorder."
    },
    "Creatinine": {
        "High":    "Increase water intake. Reduce high-protein diet. Consult a nephrologist for kidney function assessment.",
        "Critical": "Critically high creatinine — kidney function is impaired. Urgent nephrology consultation required."
    },
    "ALT": {
        "High":    "Avoid alcohol and fatty foods. Reduce medications that stress the liver. Consult a gastroenterologist.",
        "Critical": "Severely elevated ALT — liver may be inflamed or damaged. Urgent hepatology consultation required."
    },
    "AST": {
        "High":    "Avoid alcohol. Rest and reduce strenuous exercise. Follow up with liver function test panel.",
        "Critical": "Critically elevated AST — urgent liver evaluation needed."
    },
    "Bilirubin": {
        "High":    "Monitor for jaundice symptoms (yellow eyes/skin). Avoid alcohol. Consult gastroenterologist.",
        "Critical": "Very high bilirubin — seek immediate medical attention. May indicate liver or bile duct obstruction."
    },
    "BUN": {
        "High":    "Increase water intake. Reduce excessive protein consumption. Consult nephrologist if persistently elevated.",
        "Low":     "Low BUN may indicate malnutrition or liver disease. Ensure adequate protein intake. Consult doctor."
    }
}

DEFICIENCY_PHRASES = {
    "Hemoglobin": "suggests anemia or low iron levels",
    "Vitamin D": "indicates Vitamin D deficiency",
    "Vitamin B12": "indicates Vitamin B12 deficiency",
    "HDL": "suggests low protective cholesterol (HDL)",
    "RBC": "suggests anemia or low red blood cell count",
    "WBC": "may indicate immune weakness or infection risk",
    "Platelets": "suggests low platelet count and bleeding risk",
    "BUN": "suggests possible protein deficiency or malnutrition"
}


# --- AI Rule-Based Analyzer ---

def analyze_medical_text(text):
    """
    Analyzes extracted medical report text using strong regex patterns.
    Returns accurate findings, alerts, severity, summary, and suggestions
    based ONLY on values present in the actual report.
    """
    findings = {}
    alerts = []
    summaries = []
    suggestions = []
    deficiencies = []

    def get_suggestion(name, status):
        s = SUGGESTIONS.get(name, {})
        return s.get(status, s.get("High", ""))

    def add_finding(name, val, unit, status, ref_range):
        suggestion_text = get_suggestion(name, status)
        findings[name] = {
            "value": val,
            "unit": unit,
            "status": status,
            "reference_range": ref_range,
            "suggestion": suggestion_text
        }
        if status in {"Low", "High", "Critical"}:
            alerts.append(f"⚠ {status} {name} detected.")
        if suggestion_text:
            suggestions.append(suggestion_text)
        if status in {"Low", "Critical"} and name in DEFICIENCY_PHRASES:
            deficiencies.append(DEFICIENCY_PHRASES[name])

    def parse(pattern, text):
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except:
                pass
        return None

    # Hemoglobin
    val = parse(r'(?:hemoglobin|hb|haemoglobin)\s*[:\-]?\s*(\d+(?:\.\d+)?)', text)
    if val:
        if val <= 9.0:     s = "Critical"
        elif val < 12.0:   s = "Low"
        elif val > 17.5:   s = "High"
        else:              s = "Normal"
        summaries.append(f"Hemoglobin is {val} g/dL — {s}.")
        add_finding("Hemoglobin", val, "g/dL", s, "12.0 - 17.5 g/dL")

    # Glucose / Blood Sugar
    val = parse(r'(?:fasting\s+(?:blood\s+)?(?:sugar|glucose)|blood\s+sugar|glucose|sugar)\s*[:\-]?\s*(\d+(?:\.\d+)?)', text)
    if val:
        if val >= 126:     s = "Critical"
        elif val >= 100:   s = "High"
        elif val < 70:     s = "Low"
        else:              s = "Normal"
        summaries.append(f"Blood Glucose is {val} mg/dL — {s}.")
        add_finding("Glucose", val, "mg/dL", s, "70 - 100 mg/dL (Fasting)")

    # Vitamin D
    val = parse(r'(?:vitamin\s*d[23]?|vit\s*d[23]?|25[\s\-]?(?:oh|hydroxy)[\s\-]?(?:vitamin\s*d)?)\s*[:\-]?\s*(\d+(?:\.\d+)?)', text)
    if val:
        if val < 10:       s = "Critical"
        elif val < 30:     s = "Low"
        elif val > 100:    s = "High"
        else:              s = "Normal"
        summaries.append(f"Vitamin D is {val} ng/mL — {s}.")
        add_finding("Vitamin D", val, "ng/mL", s, "30 - 100 ng/mL")

    # Vitamin B12
    val = parse(r'(?:vitamin\s*b[\s\-]?12|vit\s*b12|cobalamin|b12)\s*[:\-]?\s*(\d+(?:\.\d+)?)', text)
    if val:
        if val < 200:      s = "Low"
        elif val > 900:    s = "High"
        else:              s = "Normal"
        summaries.append(f"Vitamin B12 is {val} pg/mL — {s}.")
        add_finding("Vitamin B12", val, "pg/mL", s, "200 - 900 pg/mL")

    # Total Cholesterol
    val = parse(r'(?:total\s+)?cholesterol\s*[:\-]?\s*(\d+(?:\.\d+)?)', text)
    if val:
        if val >= 240:     s = "Critical"
        elif val >= 200:   s = "High"
        else:              s = "Normal"
        summaries.append(f"Cholesterol is {val} mg/dL — {s}.")
        add_finding("Cholesterol", val, "mg/dL", s, "< 200 mg/dL")

    # HDL
    val = parse(r'hdl(?:\s+cholesterol)?\s*[:\-]?\s*(\d+(?:\.\d+)?)', text)
    if val:
        if val < 40:       s = "Low"
        else:              s = "Normal"
        summaries.append(f"HDL is {val} mg/dL — {s}.")
        add_finding("HDL", val, "mg/dL", s, "> 40 mg/dL")

    # LDL
    val = parse(r'ldl(?:\s+cholesterol)?\s*[:\-]?\s*(\d+(?:\.\d+)?)', text)
    if val:
        if val >= 160:     s = "Critical"
        elif val >= 100:   s = "High"
        else:              s = "Normal"
        summaries.append(f"LDL is {val} mg/dL — {s}.")
        add_finding("LDL", val, "mg/dL", s, "< 100 mg/dL")

    # Triglycerides
    val = parse(r'triglycerides?\s*[:\-]?\s*(\d+(?:\.\d+)?)', text)
    if val:
        if val >= 500:     s = "Critical"
        elif val >= 150:   s = "High"
        else:              s = "Normal"
        summaries.append(f"Triglycerides is {val} mg/dL — {s}.")
        add_finding("Triglycerides", val, "mg/dL", s, "< 150 mg/dL")

    # TSH
    val = parse(r'tsh\s*[:\-]?\s*(\d+(?:\.\d+)?)', text)
    if val:
        if val < 0.4:      s = "Low"
        elif val > 4.5:    s = "High"
        else:              s = "Normal"
        summaries.append(f"TSH is {val} uIU/mL — {s}.")
        add_finding("TSH", val, "uIU/mL", s, "0.4 - 4.5 uIU/mL")

    # Platelets
    val = parse(r'(?:platelet\s*count|platelets?)\s*[:\-]?\s*(\d[\d,]*)', text)
    if val:
        if val < 1000:
            val = val * 1000
        if val < 100000:   s = "Critical"
        elif val < 150000: s = "Low"
        elif val > 450000: s = "High"
        else:              s = "Normal"
        summaries.append(f"Platelets is {val:,.0f} /uL — {s}.")
        add_finding("Platelets", int(val), "/uL", s, "150,000 - 450,000 /uL")

    # RBC
    val = parse(r'(?:rbc|red\s+blood\s+cells?|erythrocytes?)\s*[:\-]?\s*(\d+(?:\.\d+)?)', text)
    if val:
        if val < 4.0:      s = "Low"
        elif val > 5.9:    s = "High"
        else:              s = "Normal"
        summaries.append(f"RBC is {val} million/uL — {s}.")
        add_finding("RBC", val, "million/uL", s, "4.0 - 5.9 million/uL")

    # WBC
    val = parse(r'(?:wbc|white\s+blood\s+cells?|leucocytes?|leukocytes?)\s*[:\-]?\s*(\d[\d,]*(?:\.\d+)?)', text)
    if val:
        if val < 100:
            val = val * 1000
        if val < 3000 or val > 15000: s = "Critical"
        elif val > 11000:              s = "High"
        elif val < 4500:               s = "Low"
        else:                          s = "Normal"
        summaries.append(f"WBC is {val:,.0f} /uL — {s}.")
        add_finding("WBC", int(val), "/uL", s, "4,500 - 11,000 /uL")

    # Creatinine
    val = parse(r'(?:creatinine|creatinin|s\.?creatinine)\s*[:\-]?\s*(\d+(?:\.\d+)?)', text)
    if val:
        if val >= 2.0:     s = "Critical"
        elif val > 1.2:    s = "High"
        elif val < 0.6:    s = "Low"
        else:              s = "Normal"
        summaries.append(f"Creatinine is {val} mg/dL — {s}.")
        add_finding("Creatinine", val, "mg/dL", s, "0.6 - 1.2 mg/dL")

    # ALT / SGPT
    val = parse(r'(?:alt|sgpt|alanine\s+(?:amino)?transferase)\s*[:\-]?\s*(\d+(?:\.\d+)?)', text)
    if val:
        if val > 100:      s = "Critical"
        elif val > 56:     s = "High"
        else:              s = "Normal"
        summaries.append(f"ALT is {val} U/L — {s}.")
        add_finding("ALT", val, "U/L", s, "< 56 U/L")

    # AST / SGOT
    val = parse(r'(?:ast|sgot|aspartate\s+(?:amino)?transferase)\s*[:\-]?\s*(\d+(?:\.\d+)?)', text)
    if val:
        if val > 80:       s = "Critical"
        elif val > 40:     s = "High"
        else:              s = "Normal"
        summaries.append(f"AST is {val} U/L — {s}.")
        add_finding("AST", val, "U/L", s, "< 40 U/L")

    # Bilirubin
    val = parse(r'(?:total\s+)?bilirubin\s*[:\-]?\s*(\d+(?:\.\d+)?)', text)
    if val:
        if val > 2.0:      s = "Critical"
        elif val > 1.2:    s = "High"
        else:              s = "Normal"
        summaries.append(f"Bilirubin is {val} mg/dL — {s}.")
        add_finding("Bilirubin", val, "mg/dL", s, "0.1 - 1.2 mg/dL")

    # BUN
    val = parse(r'(?:bun|blood\s+urea\s+nitrogen|urea\s+nitrogen)\s*[:\-]?\s*(\d+(?:\.\d+)?)', text)
    if val:
        if val > 20:       s = "High"
        elif val < 7:      s = "Low"
        else:              s = "Normal"
        summaries.append(f"BUN is {val} mg/dL — {s}.")
        add_finding("BUN", val, "mg/dL", s, "7 - 20 mg/dL")

    # Determine severity
    if not findings:
        summaries.append("No standard biomarkers could be parsed from this report. Please review manually.")
        findings["General Report"] = {"value": "Manual Review", "unit": "N/A", "status": "Normal", "reference_range": "N/A", "suggestion": ""}
        severity = "Normal"
        deficiency_summary = "No deficiency summary available; no standard biomarkers were parsed."
    else:
        statuses = [f["status"] for f in findings.values()]
        if "Critical" in statuses:
            severity = "Critical"
        elif "High" in statuses or "Low" in statuses:
            severity = "Moderate"
        else:
            severity = "Normal"

        if deficiencies:
            deficiency_summary = "Deficiency Summary: " + "; ".join(deficiencies) + "."
        else:
            deficiency_summary = "No deficiency patterns detected in the parsed biomarkers."

    summary_text = " ".join(summaries)
    suggestions = list(dict.fromkeys(suggestions))

    abnormal_count = len([status for status in [f["status"] for f in findings.values()] if status != "Normal"])
    critical_count = len([status for status in [f["status"] for f in findings.values()] if status == "Critical"])

    if not findings:
        short_summary = "No standard biomarkers could be parsed from this report. Please review the report manually."
    else:
        if critical_count > 0:
            short_summary = f"This report contains {abnormal_count} abnormal biomarker(s), including {critical_count} critical finding(s). Overall severity is {severity}."
        elif abnormal_count > 0:
            short_summary = f"This report contains {abnormal_count} abnormal biomarker(s) and shows {severity} severity overall."
        else:
            short_summary = "All parsed biomarkers are within expected ranges and no abnormalities were detected."

    detailed_summary = short_summary
    if summary_text:
        detailed_summary += " " + summary_text
    if deficiency_summary:
        detailed_summary += " " + deficiency_summary

    return {
        "summary": short_summary,
        "detailed_summary": detailed_summary.strip(),
        "deficiency_summary": deficiency_summary,
        "key_findings": findings,
        "severity": severity,
        "alerts": alerts,
        "suggestions": suggestions
    }


# --- PDF Generation ---

def generate_pdf_report(report, patient_name, output_path):
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        doc = SimpleDocTemplate(output_path, pagesize=letter,
                                rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
        story = []

        primary_color = colors.HexColor("#e0295a")
        text_color = colors.HexColor("#374151")
        accent_color = colors.HexColor("#c01f49")

        severity_color = colors.HexColor("#10B981")
        if report['severity'] == 'Moderate':
            severity_color = colors.HexColor("#F59E0B")
        elif report['severity'] == 'Critical':
            severity_color = colors.HexColor("#EF4444")

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('ReportTitle', parent=styles['Heading1'],
                                     fontName='Helvetica-Bold', fontSize=22,
                                     textColor=primary_color, spaceAfter=10)
        subtitle_style = ParagraphStyle('ReportSubtitle', parent=styles['Normal'],
                                        fontName='Helvetica-Bold', fontSize=11,
                                        textColor=accent_color, spaceAfter=8)
        heading2_style = ParagraphStyle('SectionHeader', parent=styles['Heading2'],
                                        fontName='Helvetica-Bold', fontSize=13,
                                        textColor=primary_color, spaceBefore=12,
                                        spaceAfter=6, keepWithNext=True)
        body_style = ParagraphStyle('ReportBody', parent=styles['BodyText'],
                                    fontName='Helvetica', fontSize=10,
                                    textColor=text_color, leading=14, spaceAfter=8)
        alert_style = ParagraphStyle('AlertText', parent=body_style,
                                     textColor=colors.HexColor("#B91C1C"),
                                     fontName='Helvetica-Bold')
        header_style = ParagraphStyle('HeaderStyle', parent=body_style,
                                      textColor=colors.white, fontName='Helvetica-Bold')

        story.append(Paragraph("AI MEDICAL REPORT ANALYSIS", title_style))
        story.append(Paragraph("Powered by Dooper Analyzer System", subtitle_style))
        story.append(Spacer(1, 8))

        meta_data = [
            [Paragraph("<b>Patient Name:</b>", body_style), Paragraph(patient_name, body_style),
             Paragraph("<b>Severity:</b>", body_style),
             Paragraph(f"<font color='{severity_color.hexval()}'><b>{report['severity'].upper()}</b></font>", body_style)],
            [Paragraph("<b>Report Name:</b>", body_style), Paragraph(report['report_name'], body_style),
             Paragraph("<b>Date:</b>", body_style), Paragraph(report.get('upload_date', 'N/A')[:10], body_style)]
        ]
        meta_table = Table(meta_data, colWidths=[100, 180, 80, 140])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 12))

        story.append(Paragraph("Clinical Summary", heading2_style))
        story.append(Paragraph(report['summary'], body_style))

        if report.get('deficiency_summary'):
            story.append(Paragraph("Deficiency Summary", heading2_style))
            story.append(Paragraph(report['deficiency_summary'], body_style))

        if report['alerts']:
            story.append(Paragraph("Warnings & Critical Flags", heading2_style))
            for alert in report['alerts']:
                story.append(Paragraph(f"• {alert}", alert_style))
            story.append(Spacer(1, 8))

        story.append(Paragraph("Biomarker Key Findings", heading2_style))

        findings_data = [[
            Paragraph("Biomarker", header_style),
            Paragraph("Value", header_style),
            Paragraph("Reference Range", header_style),
            Paragraph("Status", header_style),
            Paragraph("Suggestion", header_style)
        ]]

        for k, v in report['key_findings'].items():
            st = v['status']
            if st == 'Critical':
                sc = "#EF4444"
            elif st in ['High', 'Low']:
                sc = "#F59E0B"
            else:
                sc = "#10B981"

            findings_data.append([
                Paragraph(f"<b>{k}</b>", body_style),
                Paragraph(f"{v['value']} {v['unit']}", body_style),
                Paragraph(v.get('reference_range', 'N/A'), body_style),
                Paragraph(f"<font color='{sc}'><b>{st}</b></font>", body_style),
                Paragraph(v.get('suggestion', '—'), ParagraphStyle('s', parent=body_style, fontSize=8, leading=11))
            ])

        findings_table = Table(findings_data, colWidths=[90, 80, 100, 60, 170])
        findings_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), primary_color),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ]))
        story.append(findings_table)
        story.append(Spacer(1, 16))

        if report.get('suggestions'):
            story.append(Paragraph("Doctor Recommendations", heading2_style))
            for s in report['suggestions']:
                story.append(Paragraph(f"• {s}", body_style))
            story.append(Spacer(1, 12))

        story.append(Paragraph(
            "<b>Disclaimer:</b> This is an AI-generated analysis for educational purposes only. "
            "It does NOT constitute medical advice. Consult a qualified doctor for diagnosis and treatment.",
            ParagraphStyle('Disc', parent=body_style, fontSize=8, leading=11,
                           textColor=colors.HexColor("#9CA3AF"))))

        doc.build(story)
        print("PDF generated successfully.")
        return True
    except Exception as e:
        print(f"PDF generation error: {e}")
        return False


# --- Email Alerts ---

def send_critical_email(user_email, user_fullname, report_name, alerts):
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = os.environ.get("SMTP_PORT")
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    sender_email = os.environ.get("SENDER_EMAIL", "alerts@dooper-reports.com")

    subject = f"CRITICAL ALERTS: Medical Report - {report_name}"
    body = f"""Hello {user_fullname},

Your medical report '{report_name}' has been analyzed. Critical findings detected:

{chr(10).join(alerts)}

Please consult a medical professional immediately.

Regards,
Dooper Health Support Team"""

    if not (smtp_server and smtp_port and smtp_user and smtp_pass):
        print("\n" + "="*60)
        print("CRITICAL EMAIL NOTIFICATION (SMTP not configured):")
        print(f"To: {user_fullname} <{user_email}>")
        print(f"Subject: {subject}")
        print(f"Body:\n{body}")
        print("="*60 + "\n")
        return True

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = user_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(sender_email, user_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Email failed: {e}")
        return False
