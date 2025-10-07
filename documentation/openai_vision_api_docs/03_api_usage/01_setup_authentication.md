# API Setup and Authentication

## Getting Your API Key

1. Go to [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Sign in to your OpenAI account
3. Click "Create new secret key"
4. Copy and save your API key securely (you won't be able to see it again)

## Installation

### Python
```bash
pip install openai
```

### Node.js
```bash
npm install openai
```

## Authentication

### Python Setup
```python
from openai import OpenAI

# Method 1: Direct API key
client = OpenAI(api_key="your-api-key-here")

# Method 2: Environment variable (recommended)
import os
os.environ["OPENAI_API_KEY"] = "your-api-key-here"
client = OpenAI()  # Automatically uses OPENAI_API_KEY env var
```

### Node.js Setup
```javascript
import OpenAI from 'openai';

// Method 1: Direct API key
const openai = new OpenAI({
  apiKey: 'your-api-key-here',
});

// Method 2: Environment variable (recommended)
// Set OPENAI_API_KEY in your environment
const openai = new OpenAI();  // Automatically uses OPENAI_API_KEY
```

### cURL Setup
```bash
curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "gpt-4.1-mini",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## API Base URL

**Default:** `https://api.openai.com/v1`

All API requests should be made to this base URL with the appropriate endpoint path.

## Required Headers

```
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY
```

## Optional Headers

```
OpenAI-Organization: org-xxxxx  # For organization-specific requests
OpenAI-Project: proj-xxxxx      # For project-specific requests
```

## Security Best Practices

1. **Never commit API keys to version control**
2. **Use environment variables** for API keys
3. **Rotate keys regularly**
4. **Use different keys** for development and production
5. **Set usage limits** in your OpenAI dashboard
6. **Monitor API usage** regularly

## Environment Variable Setup

### Linux/Mac
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### Windows (Command Prompt)
```cmd
set OPENAI_API_KEY=your-api-key-here
```

### Windows (PowerShell)
```powershell
$env:OPENAI_API_KEY="your-api-key-here"
```

### .env File (recommended)
```
OPENAI_API_KEY=your-api-key-here
```

Then use a library like `python-dotenv` (Python) or `dotenv` (Node.js) to load it:

**Python:**
```python
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
client = OpenAI()  # Automatically loads from .env
```

**Node.js:**
```javascript
import 'dotenv/config';
import OpenAI from 'openai';

const openai = new OpenAI();  // Automatically loads from .env
```

## Verifying Your Setup

### Python
```python
from openai import OpenAI

client = OpenAI()

try:
    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[{"role": "user", "content": "Hello!"}],
        max_tokens=10
    )
    print("✓ Authentication successful!")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"✗ Authentication failed: {e}")
```

### Node.js
```javascript
import OpenAI from 'openai';

const openai = new OpenAI();

try {
  const response = await openai.chat.completions.create({
    model: 'gpt-4.1-nano',
    messages: [{ role: 'user', content: 'Hello!' }],
    max_tokens: 10,
  });
  console.log('✓ Authentication successful!');
  console.log(response.choices[0].message.content);
} catch (error) {
  console.error('✗ Authentication failed:', error);
}
```
