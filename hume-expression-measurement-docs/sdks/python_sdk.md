# Python SDK

The Hume Python SDK provides a convenient way to interact with the Hume Expression Measurement API from your Python applications.

## Installation

You can install the SDK using pip:

```bash
pip install hume
```

## Authentication

To use the SDK, you will need to provide your API key when creating a client instance:

```python
from hume.client import HumeClient

client = HumeClient(api_key="YOUR_API_KEY")
```

## Usage

The SDK is organized into namespaces for each of the Hume APIs. To use the Expression Measurement API, you will use the `expression_measurement` namespace:

```python
client.expression_measurement.batch.start_inference_job(...)
```

### Asynchronous Client

The SDK also provides an asynchronous client for use with `asyncio`:

```python
import asyncio
from hume.client import AsyncHumeClient

client = AsyncHumeClient(api_key="YOUR_API_KEY")

async def main():
    job = await client.expression_measurement.batch.start_inference_job(...)

asyncio.run(main())
```

### Exception Handling

All errors thrown by the SDK are subclasses of `hume.core.ApiError`:

```python
import hume.core

try:
    client.expression_measurement.batch.get_job_predictions(...)
except hume.core.ApiError as e:
    print(f"Error: {e.status_code} - {e.body}")
```

For more detailed information and examples, please refer to the [official GitHub repository](https://github.com/HumeAI/hume-python-sdk).

