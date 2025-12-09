# How to Get an OpenAI API Key

## Step-by-Step Guide

### Step 1: Create an OpenAI Account

1. Go to [https://platform.openai.com](https://platform.openai.com)
2. Click **"Sign Up"** or **"Log In"** if you already have an account
3. Complete the registration process (email verification required)

### Step 2: Add Payment Method

**Important:** OpenAI requires a payment method to use the API, even for free tier.

1. Go to [https://platform.openai.com/account/billing](https://platform.openai.com/account/billing)
2. Click **"Add payment method"**
3. Add a credit/debit card
4. Set up billing (you'll get $5 free credit to start)

### Step 3: Generate API Key

1. Go to [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Click **"Create new secret key"**
3. Give it a name (e.g., "InteractiveBook")
4. **Copy the key immediately** - you won't be able to see it again!
5. The key will look like: `sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Step 4: Add API Key to Your Project

1. Open your `.env` file at: `src/assets/.env`
2. Add or update this line:
   ```env
   OPENAI_API_KEY=sk-proj-your-actual-key-here
   ```
3. **Important:** 
   - No spaces around the `=`
   - No quotes around the key
   - Replace `sk-proj-your-actual-key-here` with your actual key

### Step 5: Restart Your Server

After adding the API key, restart your FastAPI server:

```bash
# Stop the current server (Ctrl+C)
# Then restart:
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```

## Cost Information

- **GPT-3.5-turbo**: ~$0.0015 per 1K tokens (very cheap)
- **Free credits**: $5 free when you add payment method
- **Typical query**: 100-500 tokens = $0.00015 - $0.00075 per query
- **1000 queries**: ~$0.15 - $0.75

## Testing Your API Key

You can test if your API key works by running:

```python
from openai import OpenAI

client = OpenAI(api_key="your-key-here")
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

## Troubleshooting

### "Invalid API key" Error
- Check that you copied the full key (starts with `sk-`)
- Make sure there are no extra spaces in your `.env` file
- Restart your server after updating `.env`

### "Insufficient quota" Error
- Check your billing at [https://platform.openai.com/account/billing](https://platform.openai.com/account/billing)
- Add credits if needed

### "Rate limit" Error
- You're making too many requests too quickly
- Wait a few seconds and try again
- Consider upgrading your plan for higher rate limits

## Security Notes

⚠️ **NEVER commit your API key to Git!**

- The `.env` file should be in `.gitignore`
- Don't share your API key publicly
- If you accidentally commit it, regenerate it immediately

## Alternative: Use Environment Variable

Instead of `.env` file, you can set it as an environment variable:

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="sk-proj-your-key-here"
```

**Mac/Linux:**
```bash
export OPENAI_API_KEY="sk-proj-your-key-here"
```

Then run your server.

