# KB: Credential Migration Guide

## Created: 2026-02-02
## Related Task: SECURITY-PHASE1-CRED-ROTATION
## Status: Active

---

## Overview

The Cherokee AI Federation is migrating away from hardcoded database credentials.
This guide explains how to update existing files to use the centralized secrets loader.

## The Problem

The password `jawaseatlasers2` appears in approximately 1,874 files across the federation codebase.
The Telegram bot token and LLM Gateway API key are similarly hardcoded.

## The Solution

A centralized secrets loader at `/ganuda/lib/secrets_loader.py` provides a three-tier
secret resolution chain:

1. **File-based** (`/ganuda/config/secrets.env`) -- primary, used in production
2. **Environment variables** -- for containerized deployments
3. **FreeIPA vault** (`/ganuda/scripts/get-vault-secret.sh`) -- last resort

## How to Migrate a File

### Database Connections (Most Common)

**Before (hardcoded):**