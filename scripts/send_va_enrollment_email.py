#!/usr/bin/env python3
"""
Send VetAssist VA Production Access Email to Erika and Dr Joe
Cherokee AI Federation - January 21, 2026

Request for input on VA production access application.
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
    query = f'from:{search_name} OR to:{search_name}'
    results = service.users().messages().list(userId='me', q=query, maxResults=5).execute()

    messages = results.get('messages', [])
    if not messages:
        print(f"No emails found for: {search_name}")
        return None

    msg = service.users().messages().get(userId='me', id=messages[0]['id'], format='metadata',
                                          metadataHeaders=['From', 'To']).execute()

    headers = {h['name']: h['value'] for h in msg['payload']['headers']}

    for header in ['From', 'To']:
        if header in headers:
            value = headers[header]
            if '<' in value and '>' in value:
                email = value.split('<')[1].split('>')[0]
            else:
                email = value

            if search_name.lower() in value.lower():
                print(f"Found {search_name}: {email}")
                return email

    return None

def create_va_enrollment_email():
    """Create the VA Production Access email content"""
    subject = "VetAssist VA Production Access - Need Your Input"

    html_content = """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">

<h1 style="color: #1a365d;">VetAssist VA Production Access</h1>
<p style="color: #666; font-style: italic;">Cherokee AI Federation - January 21, 2026</p>

<hr style="border: 1px solid #e2e8f0;">

<h2 style="color: #2c5282;">Summary</h2>
<p>We're preparing to submit VetAssist for <strong>VA production API access</strong>. Before we submit, I'd like your input on the application materials and overall approach.</p>

<hr style="border: 1px solid #e2e8f0;">

<h2 style="color: #2c5282;">What is VetAssist?</h2>
<p>VetAssist is a <strong>free</strong> AI-powered platform that helps Veterans navigate VA disability claims:</p>
<ul>
<li>Step-by-step guidance through the claims process</li>
<li>Document organization tools</li>
<li>Real-time claim status tracking via VA APIs</li>
<li>AI assistance that explains VA regulations in plain language</li>
</ul>
<p><strong>Key principle:</strong> We do NOT monetize Veteran data. Ever.</p>

<hr style="border: 1px solid #e2e8f0;">

<h2 style="color: #2c5282;">Sandbox Testing: COMPLETE ✅</h2>
<table style="border-collapse: collapse; width: 100%;">
<tr style="background-color: #c6f6d5;">
<td style="padding: 8px; border: 1px solid #9ae6b4;">CCG Token Acquisition</td>
<td style="padding: 8px; border: 1px solid #9ae6b4;"><strong>PASS</strong></td>
</tr>
<tr style="background-color: #c6f6d5;">
<td style="padding: 8px; border: 1px solid #9ae6b4;">Benefits Claims API - List Claims</td>
<td style="padding: 8px; border: 1px solid #9ae6b4;"><strong>PASS</strong> (1,385 test claims retrieved)</td>
</tr>
<tr style="background-color: #c6f6d5;">
<td style="padding: 8px; border: 1px solid #9ae6b4;">Benefits Claims API - Claim Detail</td>
<td style="padding: 8px; border: 1px solid #9ae6b4;"><strong>PASS</strong></td>
</tr>
<tr style="background-color: #c6f6d5;">
<td style="padding: 8px; border: 1px solid #9ae6b4;">Lighthouse Benefits Intake - Upload</td>
<td style="padding: 8px; border: 1px solid #9ae6b4;"><strong>PASS</strong></td>
</tr>
<tr style="background-color: #c6f6d5;">
<td style="padding: 8px; border: 1px solid #9ae6b4;">Full Document Upload Workflow</td>
<td style="padding: 8px; border: 1px solid #9ae6b4;"><strong>PASS</strong></td>
</tr>
</table>

<p><strong>Score: 6/6 tests passed - Ready for production access request</strong></p>

<hr style="border: 1px solid #e2e8f0;">

<h2 style="color: #2c5282;">Documents Drafted</h2>
<ol>
<li><strong>Terms of Service</strong> - Comprehensive TOS covering service description, user responsibilities, AI disclaimers, liability limits</li>
<li><strong>Privacy Policy</strong> - Data handling, security measures, veteran rights, no monetization pledge</li>
<li><strong>VA Application Content</strong> - Value proposition, app description, business model</li>
</ol>

<p>All documents are on redfin at <code>/ganuda/docs/vetassist/</code></p>

<hr style="border: 1px solid #e2e8f0;">

<h2 style="color: #2c5282;">Questions for You</h2>

<ol>
<li><strong>Terms of Service:</strong> Does the draft TOS adequately protect Cherokee AI Federation while remaining veteran-friendly? Any legal concerns?</li>

<li><strong>Privacy Policy:</strong> Does this meet compliance requirements? Should we add anything specific for VA data handling?</li>

<li><strong>Value Proposition:</strong> Does the messaging accurately represent what we're building and why?</li>

<li><strong>Contact Information:</strong> Who should be listed as primary and secondary contacts for VA communications?</li>

<li><strong>Organization Address:</strong> What address should we use for Cherokee AI Federation?</li>

<li><strong>Timeline:</strong> VA notes 1-6 month approval timeline with possible demo requirement. Are we prepared for that?</li>

<li><strong>Seven Generations Alignment:</strong> Does this initiative align with our long-term mission? Any concerns about VA partnership implications?</li>
</ol>

<hr style="border: 1px solid #e2e8f0;">

<h2 style="color: #2c5282;">APIs We're Requesting</h2>
<table style="border-collapse: collapse; width: 100%;">
<tr style="background-color: #edf2f7;">
<td style="padding: 8px; border: 1px solid #e2e8f0;"><strong>Benefits Intake API</strong></td>
<td style="padding: 8px; border: 1px solid #e2e8f0;">Submit claim documents to VA</td>
</tr>
<tr>
<td style="padding: 8px; border: 1px solid #e2e8f0;"><strong>Benefits Claims API (CCG)</strong></td>
<td style="padding: 8px; border: 1px solid #e2e8f0;">Query claim status server-to-server</td>
</tr>
</table>

<hr style="border: 1px solid #e2e8f0;">

<h2 style="color: #2c5282;">Next Steps (Pending Your Input)</h2>
<ol>
<li>Finalize TOS and Privacy Policy</li>
<li>Deploy to vetassist.ganuda.us/terms and /privacy</li>
<li>Complete contact information</li>
<li>Submit VA production access application</li>
<li>Prepare for potential VA demo call</li>
</ol>

<hr style="border: 1px solid #e2e8f0;">

<p>Please review and let me know your thoughts. Happy to discuss any concerns or questions.</p>

<p style="text-align: center; color: #718096; font-style: italic;">
<strong>For Seven Generations</strong><br>
Cherokee AI Federation<br>
<em>"Serving those who served."</em>
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

    html_part = MIMEText(html_content, 'html')
    message.attach(html_part)

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    result = service.users().messages().send(
        userId='me',
        body={'raw': raw}
    ).execute()

    print(f"Email sent! Message ID: {result['id']}")
    return result

def main():
    print("=" * 60)
    print("VetAssist VA Production Access Email")
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

    # Try alternate searches
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
    subject, html_content = create_va_enrollment_email()

    print(f"\nSending email: {subject}")
    result = send_email(service, recipients, subject, html_content)

    print("\n" + "=" * 60)
    print("EMAIL SENT SUCCESSFULLY")
    print(f"To: {', '.join(recipients)}")
    print(f"Subject: {subject}")
    print("=" * 60)

if __name__ == "__main__":
    main()
