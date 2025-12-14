# Cherokee AI API Keys - December 12, 2025
## SAVE THESE KEYS - THEY WILL NOT BE SHOWN AGAIN

### Admin Key
```
ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5
```
- User: admin
- Quota: 100,000 tokens
- Rate limit: 120/min

### TPM-Claude Key
```
ck-6ba780b39522194154f40d661365c087d0f4c3aeb071094049c691c02cb92f44
```
- User: tpm-claude
- Quota: 50,000 tokens
- Rate limit: 60/min

## Usage

```bash
# Test with curl
curl -X POST http://192.168.132.223:8080/v1/chat/completions \
  -H "Authorization: Bearer ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5" \
  -H "Content-Type: application/json" \
  -d '{"model": "nemotron-9b", "messages": [{"role": "user", "content": "Hello"}]}'
```

## Create New Keys

```sql
SELECT * FROM create_api_key('username', 'description', 10000, 60);
```
