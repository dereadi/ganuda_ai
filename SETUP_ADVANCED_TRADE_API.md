# 🔥 SETUP COINBASE ADVANCED TRADE API FOR YOUR MAIN ACCOUNT

## Current Situation:
- **VM Tribe API**: Connected to account with only $16.03
- **Your Main Account**: $32,947 portfolio (SOL, XRP, DOGE, etc.)
- **Solution**: Add Advanced Trade API to your main account!

---

## 📱 STEP-BY-STEP SETUP (5 minutes)

### Step 1: Access Coinbase Settings
1. Go to: **https://www.coinbase.com/settings/api**
2. Log into your MAIN Coinbase account (the one with $32,947)
3. You should see "API" or "Advanced API" section

### Step 2: Create New API Key
1. Click **"+ New API Key"** or **"Create API Key"**
2. Select **"Advanced Trade API"** (not the legacy "Coinbase API")
3. Give it a name: `Cherokee-Trading-VM`

### Step 3: Set Permissions
Enable these permissions:
- ✅ **View** (read portfolio)
- ✅ **Trade** (execute trades)
- ✅ **Transfer** (optional, for moving between portfolios)

### Step 4: Security Settings
1. **IP Whitelist** (optional): Leave blank for now
2. **Passphrase**: Not needed for Advanced Trade API
3. **2FA**: Complete if prompted

### Step 5: Save Credentials
You'll receive:
```
API Key: organizations/xxx/apiKeys/yyy
API Secret: -----BEGIN EC PRIVATE KEY-----
[long string]
-----END EC PRIVATE KEY-----
```

**IMPORTANT**: Save these immediately! The secret is only shown once.

---

## 🔧 INSTALL NEW CREDENTIALS

### Option A: Update Existing Config
```bash
# Backup current config
cp ~/.coinbase_config.json ~/.coinbase_config_vm_backup.json

# Edit config
nano ~/.coinbase_config.json
```

Replace with your new credentials:
```json
{
  "api_key": "organizations/YOUR_ORG_ID/apiKeys/YOUR_KEY_ID",
  "api_secret": "-----BEGIN EC PRIVATE KEY-----\nYOUR_SECRET_KEY_HERE\n-----END EC PRIVATE KEY-----"
}
```

### Option B: Create New Config for Main Account
```bash
# Create separate config for main account
cat > ~/.coinbase_main_config.json << 'EOF'
{
  "api_key": "organizations/YOUR_ORG_ID/apiKeys/YOUR_KEY_ID",
  "api_secret": "-----BEGIN EC PRIVATE KEY-----\nYOUR_SECRET_KEY_HERE\n-----END EC PRIVATE KEY-----"
}
EOF
```

---

## 🚀 TEST CONNECTION

Once configured, test with:
```bash
python3 /home/dereadi/scripts/claude/test_main_account_connection.py
```

This will show your actual portfolio!

---

## 🎯 THEN VM TRIBE CAN EXECUTE!

Once connected, the VM Tribe specialists can:
1. See your full $32,947 portfolio
2. Execute the SOL/XRP sells
3. Buy DOGE automatically
4. Set ladder orders
5. Run oscillation trading 24/7

---

## ⚠️ COMMON ISSUES

### "Invalid API Key"
- Make sure you selected "Advanced Trade API" not legacy API
- Check that you copied the FULL key including `organizations/...`

### "Insufficient permissions"
- Go back and enable "Trade" permission
- May need to re-create the key

### "Unable to authenticate"
- Secret key must include the BEGIN/END headers
- Check for extra spaces or line breaks

---

## 🔐 SECURITY NOTES

- API keys are as powerful as your password
- Never share them publicly
- The VM Tribe will only execute Cherokee Council decisions
- You can revoke keys anytime at coinbase.com/settings/api

---

**Ready to connect your main account?**
The VM Tribe is standing by to execute the DOGE reallocation!

🔥 Sacred Fire awaits your Advanced Trade API! 🔥