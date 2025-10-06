# TypeScript Batch API Example

This example demonstrates how to use the TypeScript SDK to submit a batch job, wait for it to complete, and retrieve the predictions.

## Code Example

```typescript
import { HumeClient } from "hume";

async function runBatchJob() {
    // Initialize the client with your API key
    const hume = new HumeClient({
        apiKey: "YOUR_API_KEY",
    });

    // Start a batch inference job
    const job = await hume.expressionMeasurement.batch.startInferenceJob({
        models: {
            face: {},
            prosody: {},
            language: {}
        },
        urls: ["https://hume-tutorials.s3.amazonaws.com/faces.zip"],
    });

    console.log(`Job started with ID: ${job.jobId}`);

    // Wait for job completion
    console.log("Waiting for job to complete...");
    await job.awaitCompletion();

    console.log("Job completed!");

    // Retrieve predictions
    const predictions = await hume.expressionMeasurement.batch.getJobPredictions(job.jobId);

    // Process predictions
    for (const sourcePrediction of predictions) {
        console.log(`Source: ${sourcePrediction.source.url}`);
        
        for (const filePrediction of sourcePrediction.results.predictions) {
            console.log(`  File: ${filePrediction.file}`);
            
            // Process face predictions
            if (filePrediction.models.face) {
                for (const group of filePrediction.models.face.grouped_predictions) {
                    for (const pred of group.predictions) {
                        console.log(`    Frame ${pred.frame}:`);
                        // Print top 5 emotions
                        const sortedEmotions = pred.emotions
                            .sort((a, b) => b.score - a.score)
                            .slice(0, 5);
                        
                        for (const emotion of sortedEmotions) {
                            console.log(`      ${emotion.name}: ${emotion.score.toFixed(3)}`);
                        }
                    }
                }
            }
        }
    }
}

runBatchJob().catch(console.error);
```

## Explanation

This example performs the following steps:

1. **Initialize the client**: Create a `HumeClient` instance with your API key.
2. **Start a job**: Call `startInferenceJob` with the desired models and URLs.
3. **Wait for completion**: Use the `awaitCompletion` method to wait for the job to finish.
4. **Retrieve predictions**: Once the job is completed, retrieve the predictions using `getJobPredictions`.
5. **Process predictions**: Iterate through the predictions and print the top emotions for each frame.

The TypeScript SDK provides a convenient `awaitCompletion` method that handles polling for you, making it easier to work with batch jobs.
