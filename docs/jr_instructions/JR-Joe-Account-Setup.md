# Jr Instructions: Create Joe's Account on Bluefin

**Task ID**: JOE-ACCT-001
**Priority**: LOW
**Target Node**: bluefin (192.168.132.222 / 100.112.254.96)
**Requires**: sudo access on bluefin

---

## Current State

| Node | jsdorn Account | Status |
|------|----------------|--------|
| redfin | UID 1001 | EXISTS |
| bluefin | - | NEEDS CREATION |
| greenfin | UID 1001 | EXISTS |

---

## Commands to Run on Bluefin

SSH to bluefin first:
```bash
ssh dereadi@100.112.254.96
```

### Step 1: Create the user account

```bash
sudo useradd -m -s /bin/bash -c "Dr. Joe Sdorn" -u 1001 jsdorn
```

Note: Using UID 1001 for consistency across cluster.

### Step 2: Set temporary password

```bash
echo 'jsdorn:Walmart1' | sudo chpasswd
```

### Step 3: Force password change on first login

```bash
sudo chage -d 0 jsdorn
```

### Step 4: Create .ssh directory

```bash
sudo mkdir -p /home/jsdorn/.ssh
sudo chmod 700 /home/jsdorn/.ssh
sudo chown jsdorn:jsdorn /home/jsdorn/.ssh
```

### Step 5: Copy SSH keys from redfin

On redfin, as dereadi with sudo:
```bash
ssh dereadi@100.116.27.89 "sudo cat /home/jsdorn/.ssh/authorized_keys"
```

Then paste that into bluefin:
```bash
sudo tee /home/jsdorn/.ssh/authorized_keys << 'EOF'
<paste keys here>
EOF
sudo chmod 600 /home/jsdorn/.ssh/authorized_keys
sudo chown jsdorn:jsdorn /home/jsdorn/.ssh/authorized_keys
```

### Step 6: Add to sudo group (optional)

If Joe needs sudo access:
```bash
sudo usermod -aG sudo jsdorn
```

---

## Verification

```bash
# Check account exists
grep jsdorn /etc/passwd

# Check home directory
ls -la /home/jsdorn/

# Check SSH keys
sudo cat /home/jsdorn/.ssh/authorized_keys

# Test SSH from Joe's machine
# ssh jsdorn@100.112.254.96
```

---

## Note

Joe will be prompted to change his password on first login.

---

*For Seven Generations*
