# WebSocket API Reference

The WebSocket API provides a real-time interface for analyzing streaming data from sources like webcams and microphones. This allows for immediate feedback and interaction based on emotional expression.

## Connection

To connect to the WebSocket API, you will need to establish a WebSocket connection to the appropriate endpoint and provide your API key for authentication.

## Usage

Once connected, you can send data to the API in the form of audio or video frames. The API will process the data in real-time and send back predictions as they are generated. The SDKs provide convenient wrappers for interacting with the WebSocket API.

### Example (using TypeScript SDK)

```typescript
import { HumeClient } from "hume";

const hume = new HumeClient({
    apiKey: "YOUR_API_KEY",
});

const socket = hume.expressionMeasurement.stream.connect({
    config: {
        language: {},
    },
});

for (const sample of samples) {
    const result = await socket.sendText({ text: sample });
    console.log(result);
}
```

This example demonstrates how to connect to the WebSocket API and send text data for analysis. The `sendText` method sends a sample of text to the API and returns a promise that resolves with the prediction results. You can also send audio and video data using the appropriate methods.

