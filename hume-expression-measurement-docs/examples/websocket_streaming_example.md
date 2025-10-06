# WebSocket Streaming Example

This example demonstrates how to use the WebSocket API for real-time emotion analysis of streaming text data.

## TypeScript Example

```typescript
import { HumeClient } from "hume";

async function streamTextAnalysis() {
    const hume = new HumeClient({
        apiKey: "YOUR_API_KEY",
    });

    const socket = hume.expressionMeasurement.stream.connect({
        config: {
            language: {},
        },
    });

    const samples = [
        "I am so happy today!",
        "This is really frustrating.",
        "Wow, that's amazing!",
        "I'm feeling a bit sad.",
    ];

    for (const sample of samples) {
        const result = await socket.sendText({ text: sample });
        
        console.log(`\nText: "${sample}"`);
        console.log("Top emotions:");
        
        // Assuming the result has a similar structure to batch predictions
        // The actual structure may vary, so adjust accordingly
        if (result.language && result.language.predictions) {
            const emotions = result.language.predictions[0].emotions;
            const sortedEmotions = emotions
                .sort((a, b) => b.score - a.score)
                .slice(0, 5);
            
            for (const emotion of sortedEmotions) {
                console.log(`  ${emotion.name}: ${emotion.score.toFixed(3)}`);
            }
        }
    }
}

streamTextAnalysis().catch(console.error);
```

## Python Example

```python
import asyncio
from hume import AsyncHumeClient, StreamDataModels

async def stream_text_analysis():
    client = AsyncHumeClient(api_key="YOUR_API_KEY")
    
    async with client.expression_measurement.stream.connect(
        options={"config": StreamDataModels(language={})}
    ) as hume_socket:
        samples = [
            "I am so happy today!",
            "This is really frustrating.",
            "Wow, that's amazing!",
            "I'm feeling a bit sad.",
        ]
        
        for sample in samples:
            result = await hume_socket.send_text(text=sample)
            
            print(f'\nText: "{sample}"')
            print("Top emotions:")
            
            # Process the result
            # The actual structure may vary, so adjust accordingly
            if hasattr(result, 'language') and result.language.predictions:
                emotions = result.language.predictions[0].emotions
                sorted_emotions = sorted(emotions, key=lambda x: x.score, reverse=True)[:5]
                
                for emotion in sorted_emotions:
                    print(f"  {emotion.name}: {emotion.score:.3f}")

asyncio.run(stream_text_analysis())
```

## Explanation

These examples demonstrate how to use the WebSocket API for real-time emotion analysis:

1. **Initialize the client**: Create a client instance with your API key.
2. **Connect to WebSocket**: Establish a WebSocket connection with the desired configuration.
3. **Send data**: Send text samples to the API for analysis.
4. **Process results**: Receive and process the emotion predictions in real-time.

The WebSocket API is ideal for applications that require immediate feedback, such as chatbots, live transcription services, or interactive voice applications.
