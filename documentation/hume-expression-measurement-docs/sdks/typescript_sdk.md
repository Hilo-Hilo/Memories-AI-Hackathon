# TypeScript SDK

The Hume TypeScript SDK provides a convenient way to interact with the Hume Expression Measurement API from your TypeScript or JavaScript applications.

## Installation

You can install the SDK using npm:

```bash
npm i hume
```

## Authentication

To use the SDK, you will need to provide your API key when creating a client instance:

```typescript
import { HumeClient } from "hume";

const hume = new HumeClient({
    apiKey: "YOUR_API_KEY",
});
```

## Usage

The SDK is organized into namespaces for each of the Hume APIs. To use the Expression Measurement API, you will use the `expressionMeasurement` namespace:

```typescript
const job = await hume.expressionMeasurement.batch.startInferenceJob(...);
```

### WebSocket Support

The SDK also provides support for the WebSocket API, allowing for real-time analysis of streaming data:

```typescript
const socket = hume.expressionMeasurement.stream.connect(...);

for (const sample of samples) {
    const result = await socket.sendText({ text: sample });
    console.log(result);
}
```

### Error Handling

All errors thrown by the SDK are subclasses of `HumeError`:

```typescript
import { HumeError, HumeTimeoutError } from "hume";

try {
    await hume.expressionMeasurement.batch.startInferenceJob(...);
} catch (err) {
    if (err instanceof HumeTimeoutError) {
        console.log("Request timed out", err);
    } else if (err instanceof HumeError) {
        console.log(err.statusCode, err.message, err.body);
    }
}
```

For more detailed information and examples, please refer to the [official GitHub repository](https://github.com/HumeAI/hume-typescript-sdk).

