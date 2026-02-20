#!/usr/bin/env python3
"""
Send VetAssist Features Email to Erika and Dr Joe
Cherokee AI Federation - January 21, 2026

Pulls email addresses from Gmail contacts/history, then sends features overview.
"""
import pickle
import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

TOKEN_PATH = os.path.expanduser('~/.gmail_credentials/token.pickle')

def get_gmail_service():
    """Connect to Gmail API"""
    if not os.path.exists(TOKEN_PATH):
        raise FileNotFoundError(f'Token not found at {TOKEN_PATH}')

    with open(TOKEN_PATH, 'rb') as token:
        creds = pickle.load(token)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)

def find_email_address(service, search_name):
    """Search Gmail for emails from/to a person and extract their email"""
    # Search for emails from this person
    query = f'from:{search_name} OR to:{search_name}'
    results = service.users().messages().list(userId='me', q=query, maxResults=5).execute()

    messages = results.get('messages', [])
    if not messages:
        print(f"No emails found for: {search_name}")
        return None

    # Get the first message and extract the email
    msg = service.users().messages().get(userId='me', id=messages[0]['id'], format='metadata',
                                          metadataHeaders=['From', 'To']).execute()

    headers = {h['name']: h['value'] for h in msg['payload']['headers']}

    # Check From and To headers for the email
    for header in ['From', 'To']:
        if header in headers:
            value = headers[header]
            # Extract email from "Name <email>" format
            if '<' in value and '>' in value:
                email = value.split('<')[1].split('>')[0]
            else:
                email = value

            # Check if this matches our search
            if search_name.lower() in value.lower():
                print(f"Found {search_name}: {email}")
                return email

    return None

def create_features_email():
    """Create the VetAssist features email content"""
    subject = "VetAssist Platform - Features Overview (January 2026)"

    html_content = """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">

<h1 style="color: #1a365d;">VetAssist Platform - Features Overview</h1>
<p style="color: #666; font-style: italic;">Cherokee AI Federation - January 21, 2026</p>

<hr style="border: 1px solid #e2e8f0;">

<h2 style="color: #2c5282;">Executive Summary</h2>
<p>VetAssist is a comprehensive VA disability claims assistance platform built on the Cherokee AI Federation infrastructure. The platform helps veterans navigate the complex VA claims process with AI-powered guidance, document processing, and accurate rating calculations.</p>

<p><strong>Current Status:</strong> Production deployment on redfin cluster, 18/18 integration tests passing.</p>

<hr style="border: 1px solid #e2e8f0;">

<h2 style="color: #2c5282;">Core Features</h2>

<h3 style="color: #4a5568;">🔐 Authentication & Security</h3>
<ul>
<li><strong>User Registration/Login</strong> - Secure JWT-based authentication</li>
<li><strong>VA OAuth Integration</strong> - Connect directly to VA.gov accounts</li>
<li><strong>PII Protection</strong> - Presidio-based automatic PII filtering</li>
<li><strong>Token Encryption</strong> - All sensitive tokens encrypted at rest</li>
</ul>

<h3 style="color: #4a5568;">📋 VA Claims Wizard</h3>
<ul>
<li><strong>Multi-Step Guided Process</strong> - Walks veterans through claim filing step-by-step</li>
<li><strong>Session Persistence</strong> - Save progress and resume anytime</li>
<li><strong>Form Selection</strong> - Supports VA Form 526EZ and related forms</li>
<li><strong>Evidence Checklist</strong> - Personalized list of required documents per condition</li>
<li><strong>PDF Export</strong> - Generate complete claim packages for submission</li>
<li><strong>Direct VA Submission</strong> - Submit claims directly through VA API</li>
</ul>

<h3 style="color: #4a5568;">🏥 CFR Condition Mapping (Sprint 3 - NEW)</h3>
<ul>
<li><strong>Intelligent Search</strong> - Veterans describe conditions in plain language, system maps to official 38 CFR diagnostic codes</li>
<li><strong>Rating Criteria Display</strong> - Shows exact percentage criteria (0% to 100%) from VA schedule</li>
<li><strong>Evidence Requirements</strong> - Lists specific evidence needed for each condition</li>
<li><strong>DBQ Form References</strong> - Links to correct Disability Benefits Questionnaire forms</li>
<li><strong>ICD-10 Mapping</strong> - Cross-references medical diagnosis codes</li>
<li><em>Database expanding from 9 to 800+ conditions (in progress)</em></li>
</ul>

<h3 style="color: #4a5568;">📄 Document Processing (Sprint 3 - NEW)</h3>
<ul>
<li><strong>Multi-Format Support</strong> - Accepts PDF, JPG, PNG, TIFF (up to 25MB)</li>
<li><strong>OCR Text Extraction</strong> - Extracts text from scanned documents</li>
<li><strong>AI-Powered Analysis</strong> - Identifies diagnoses, treatments, and ICD codes</li>
<li><strong>Nexus Detection</strong> - Finds service connection language ("at least as likely as not")</li>
<li><strong>Document Classification</strong> - Automatically identifies DD-214, medical records, nexus letters, DBQs</li>
<li><strong>Security Validated</strong> - Blocks malicious files, enforces size limits</li>
</ul>

<h3 style="color: #4a5568;">🧮 Rating Calculator</h3>
<ul>
<li><strong>Combined Rating Math</strong> - Accurate VA combined rating calculation per 38 CFR 4.25</li>
<li><strong>Bilateral Factor</strong> - Correctly applies 10% bilateral factor for paired extremities</li>
<li><strong>What-If Analysis</strong> - Model hypothetical rating scenarios</li>
<li><strong>Individual Breakdowns</strong> - See how each condition contributes to total</li>
</ul>

<h3 style="color: #4a5568;">💬 AI Chat Assistant</h3>
<ul>
<li><strong>Veteran Assistance Chat</strong> - Answer questions about VA claims process</li>
<li><strong>Council Validation</strong> - Responses validated by 7-Specialist AI Council</li>
<li><strong>Crisis Detection</strong> - Mental health safety monitoring with appropriate resources</li>
<li><strong>RAG Knowledge Base</strong> - Answers grounded in actual VA regulations</li>
</ul>

<h3 style="color: #4a5568;">📊 Dashboard & Tracking</h3>
<ul>
<li><strong>Claim Status Overview</strong> - Visual progress tracking</li>
<li><strong>Evidence Status</strong> - See what's uploaded vs. what's still needed</li>
<li><strong>Timeline View</strong> - Track claim milestones and dates</li>
</ul>

<hr style="border: 1px solid #e2e8f0;">

<h2 style="color: #2c5282;">Technical Infrastructure</h2>

<table style="border-collapse: collapse; width: 100%;">
<tr style="background-color: #edf2f7;">
<td style="padding: 8px; border: 1px solid #e2e8f0;"><strong>API Endpoints</strong></td>
<td style="padding: 8px; border: 1px solid #e2e8f0;">19 modules, 60+ endpoints</td>
</tr>
<tr>
<td style="padding: 8px; border: 1px solid #e2e8f0;"><strong>Backend Services</strong></td>
<td style="padding: 8px; border: 1px solid #e2e8f0;">20 Python services</td>
</tr>
<tr style="background-color: #edf2f7;">
<td style="padding: 8px; border: 1px solid #e2e8f0;"><strong>Database Tables</strong></td>
<td style="padding: 8px; border: 1px solid #e2e8f0;">15 PostgreSQL tables</td>
</tr>
<tr>
<td style="padding: 8px; border: 1px solid #e2e8f0;"><strong>Integration Tests</strong></td>
<td style="padding: 8px; border: 1px solid #e2e8f0;">18/18 passing (100%)</td>
</tr>
<tr style="background-color: #edf2f7;">
<td style="padding: 8px; border: 1px solid #e2e8f0;"><strong>Performance</strong></td>
<td style="padding: 8px; border: 1px solid #e2e8f0;">Condition mapping: 20ms avg</td>
</tr>
</table>

<hr style="border: 1px solid #e2e8f0;">

<h2 style="color: #2c5282;">Roadmap</h2>
<ul>
<li>✅ <strong>Sprint 1-2</strong>: Core platform, wizard, calculator</li>
<li>✅ <strong>Sprint 3</strong>: Document processing, CFR mapping, evidence checklists</li>
<li>🔄 <strong>In Progress</strong>: CFR database expansion (9 → 800+ conditions)</li>
<li>📋 <strong>Planned</strong>: ML-based rating prediction, VSO dashboard, mobile optimization</li>
</ul>

<hr style="border: 1px solid #e2e8f0;">

<p style="text-align: center; color: #718096; font-style: italic;">
<strong>For Seven Generations</strong><br>
Cherokee AI Federation
</p>

</body>
</html>
"""

    return subject, html_content

def send_email(service, to_addresses, subject, html_content):
    """Send email via Gmail API"""
    message = MIMEMultipart('alternative')
    message['Subject'] = subject
    message['From'] = 'me'
    message['To'] = ', '.join(to_addresses)

    # Add HTML content
    html_part = MIMEText(html_content, 'html')
    message.attach(html_part)

    # Encode and send
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    result = service.users().messages().send(
        userId='me',
        body={'raw': raw}
    ).execute()

    print(f"Email sent! Message ID: {result['id']}")
    return result

def main():
    print("=" * 60)
    print("VetAssist Features Email Sender")
    print("Cherokee AI Federation")
    print("=" * 60)

    # Connect to Gmail
    print("\nConnecting to Gmail API...")
    service = get_gmail_service()
    print("Connected!")

    # Find email addresses
    print("\nSearching for email addresses...")

    erika_email = find_email_address(service, "Erika Hammontree")
    joe_email = find_email_address(service, "Joe Dorn")

    # Also try alternate searches
    if not erika_email:
        erika_email = find_email_address(service, "Hammontree")
    if not joe_email:
        joe_email = find_email_address(service, "Dorn")
        if not joe_email:
            joe_email = find_email_address(service, "Dr Joe")

    recipients = []
    if erika_email:
        recipients.append(erika_email)
    if joe_email:
        recipients.append(joe_email)

    if not recipients:
        print("\nERROR: Could not find email addresses for Erika or Joe")
        print("Please provide email addresses manually.")
        return

    print(f"\nRecipients: {recipients}")

    # Create and send email
    print("\nCreating email content...")
    subject, html_content = create_features_email()

    print(f"\nSending email: {subject}")
    result = send_email(service, recipients, subject, html_content)

    print("\n" + "=" * 60)
    print("EMAIL SENT SUCCESSFULLY")
    print(f"To: {', '.join(recipients)}")
    print(f"Subject: {subject}")
    print("=" * 60)

if __name__ == "__main__":
    main()
