#!/usr/bin/env python3
"""
Reset VetAssist test account passwords to defaults.
Run this during testing when you need to reset test accounts.

Usage: python3 reset_vetassist_test_accounts.py
"""

from passlib.context import CryptContext
import psycopg2

def reset_test_accounts():
    pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

    conn = psycopg2.connect(
        host='192.168.132.222',
        dbname='triad_federation',
        user='claude',
        password='jawaseatlasers2'
    )
    cur = conn.cursor()

    print("Resetting VetAssist test account passwords...")

    for i in range(1, 6):
        email = f'test{i}@vetassist.test'
        password = f'password{i}'
        password_hash = pwd_context.hash(password)
        cur.execute(
            'UPDATE users SET password_hash = %s WHERE email = %s RETURNING email',
            (password_hash, email)
        )
        result = cur.fetchone()
        if result:
            print(f'  ✓ {email} -> {password}')
        else:
            print(f'  ✗ Account not found: {email}')

    conn.commit()
    cur.close()
    conn.close()
    print("\nDone. Test accounts ready for use.")

if __name__ == '__main__':
    reset_test_accounts()
