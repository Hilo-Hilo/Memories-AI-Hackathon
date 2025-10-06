# Authentication

All requests to the Hume Expression Measurement API must be authenticated using an API key.

## Obtaining an API Key

To obtain an API key:

1. Sign up for an account at [https://www.hume.ai](https://www.hume.ai)
2. Navigate to the developer platform
3. Generate a new API key from your account settings

Keep your API key secure and do not share it publicly. Anyone with access to your API key can make requests on your behalf and incur charges to your account.

## Using Your API Key

### REST API

For REST API requests, include your API key in the `X-Hume-Api-Key` header:

```bash
curl -X GET https://api.hume.ai/v0/batch/jobs \
  -H "X-Hume-Api-Key: YOUR_API_KEY"
```

### Python SDK

When using the Python SDK, provide your API key when creating the client:

```python
from hume.client import HumeClient

client = HumeClient(api_key="YOUR_API_KEY")
```

### TypeScript SDK

When using the TypeScript SDK, provide your API key in the client configuration:

```typescript
import { HumeClient } from "hume";

const hume = new HumeClient({
    apiKey: "YOUR_API_KEY",
});
```

## Environment Variables

It is recommended to store your API key in an environment variable rather than hardcoding it in your application:

```bash
export HUME_API_KEY="YOUR_API_KEY"
```

Then, in your code:

```python
import os
from hume.client import HumeClient

client = HumeClient(api_key=os.getenv("HUME_API_KEY"))
```

## Security Best Practices

- **Never commit API keys to version control**: Use environment variables or secure secret management systems
- **Rotate keys regularly**: Generate new API keys periodically and revoke old ones
- **Use separate keys for different environments**: Have different API keys for development, staging, and production
- **Monitor usage**: Regularly check your API usage to detect any unauthorized access
