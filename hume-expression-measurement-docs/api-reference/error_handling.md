# Error Handling

Understanding how to handle errors is crucial for building robust applications with the Hume Expression Measurement API.

## HTTP Status Codes

The API uses standard HTTP status codes to indicate the success or failure of requests:

| Status Code | Meaning | Description |
|---|---|---|
| 200 | OK | The request was successful |
| 400 | Bad Request | The request was malformed or invalid |
| 401 | Unauthorized | Authentication failed or API key is invalid |
| 404 | Not Found | The requested resource does not exist |
| 408 | Request Timeout | The request took too long to complete |
| 409 | Conflict | The request conflicts with the current state |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | An error occurred on the server |
| 503 | Service Unavailable | The service is temporarily unavailable |

## Retries

Both the Python and TypeScript SDKs implement automatic retry logic for certain types of errors:

- **408 (Request Timeout)**
- **409 (Conflict)**
- **429 (Too Many Requests)**
- **5XX (Server Errors)**

The SDKs use exponential backoff to avoid overwhelming the server with repeated requests.

### Configuring Retries

You can configure the retry behavior when making requests:

**Python:**
```python
from hume.core import RequestOptions

client.expression_measurement.batch.get_job_predictions(
    id="job-id",
    request_options=RequestOptions(max_retries=5)
)
```

**TypeScript:**
```typescript
await hume.expressionMeasurement.batch.getJobPredictions("job-id", {
    maxRetries: 5
});
```

## Exception Handling

### Python SDK

All errors in the Python SDK are subclasses of `hume.core.ApiError`:

```python
import hume.core

try:
    predictions = client.expression_measurement.batch.get_job_predictions(id="job-id")
except hume.core.ApiError as e:
    print(f"API Error: {e.status_code}")
    print(f"Message: {e.body}")
```

### TypeScript SDK

The TypeScript SDK provides specific error classes:

```typescript
import { HumeError, HumeTimeoutError } from "hume";

try {
    const job = await hume.expressionMeasurement.batch.startInferenceJob(...);
} catch (err) {
    if (err instanceof HumeTimeoutError) {
        console.log("Request timed out", err);
    } else if (err instanceof HumeError) {
        console.log(`Error ${err.statusCode}: ${err.message}`);
        console.log(err.body);
    }
}
```

## Common Errors and Solutions

### Invalid API Key (401)

**Problem**: Your API key is missing, invalid, or has been revoked.

**Solution**: Verify that you are using the correct API key and that it has not been revoked. Generate a new key if necessary.

### Rate Limit Exceeded (429)

**Problem**: You have made too many requests in a short period.

**Solution**: Implement rate limiting in your application. The SDKs will automatically retry after a delay, but you should also consider spacing out your requests.

### Job Not Found (404)

**Problem**: The job ID you provided does not exist.

**Solution**: Verify that you are using the correct job ID. Jobs may also be automatically deleted after a certain period.

### Internal Server Error (500)

**Problem**: An error occurred on the Hume AI servers.

**Solution**: The SDKs will automatically retry the request. If the problem persists, contact Hume AI support.
