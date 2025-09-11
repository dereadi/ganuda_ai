#!/usr/bin/env python3
"""
ROBINHOOD API KEY GENERATOR
============================
Generates RSA public/private key pair for Robinhood API
"""

import os
import base64
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from datetime import datetime

print("🔐 ROBINHOOD API KEY GENERATOR")
print("="*50)
print()

# Generate RSA key pair
print("🔑 Generating RSA-2048 key pair...")
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)

public_key = private_key.public_key()

# Export private key
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

# Export public key
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# Also create Base64 encoded version (often required by APIs)
public_key_base64 = base64.b64encode(public_pem).decode('utf-8')

# Save keys to files
private_key_file = os.path.expanduser("~/.robinhood_private_key.pem")
public_key_file = os.path.expanduser("~/.robinhood_public_key.pem")

print("\n💾 Saving keys...")

# Save private key (secure it!)
with open(private_key_file, 'wb') as f:
    f.write(private_pem)
os.chmod(private_key_file, 0o600)  # Only owner can read

# Save public key
with open(public_key_file, 'wb') as f:
    f.write(public_pem)

print(f"✅ Private key saved to: {private_key_file}")
print(f"✅ Public key saved to: {public_key_file}")

print("\n" + "="*50)
print("📋 YOUR PUBLIC KEY (Copy this to Robinhood):")
print("="*50)
print()

# Display the public key in the format Robinhood expects
public_key_str = public_pem.decode('utf-8')

# Remove the PEM headers for cleaner display
clean_public_key = public_key_str.replace('-----BEGIN PUBLIC KEY-----\n', '')
clean_public_key = clean_public_key.replace('\n-----END PUBLIC KEY-----\n', '')
clean_public_key = clean_public_key.replace('\n', '')

print("Standard Format (PEM):")
print("-"*30)
print(public_key_str)

print("\n📋 Base64 Format (if needed):")
print("-"*30)
print(clean_public_key)
print()

print("="*50)
print("\n🔧 HOW TO USE:")
print("1. Log into Robinhood.com")
print("2. Go to Account → Settings → API Access")
print("3. Click 'Generate API Key'")
print("4. When prompted for public key, paste the key above")
print("5. Robinhood will return your API credentials")
print()

print("⚠️  IMPORTANT SECURITY NOTES:")
print(f"• Private key is stored securely at: {private_key_file}")
print("• NEVER share your private key with anyone")
print("• NEVER commit private key to git")
print("• Keep the public key for API registration")
print()

# Create a configuration file with the public key
config = {
    "public_key": clean_public_key,
    "public_key_file": public_key_file,
    "private_key_file": private_key_file,
    "generated": datetime.now().isoformat(),
    "algorithm": "RSA-2048"
}

import json
config_file = os.path.expanduser("~/.robinhood_keys_config.json")
with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)

print(f"📁 Configuration saved to: {config_file}")
print("\n✅ Keys generated successfully!")
print("🦀 Ready for Robinhood API registration!"