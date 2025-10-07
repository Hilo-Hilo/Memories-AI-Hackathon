# Python Batch API Example

This example demonstrates how to use the Python SDK to submit a batch job, wait for it to complete, and retrieve the predictions.

## Code Example

```python
from hume.client import HumeClient
import time

# Initialize the client with your API key
client = HumeClient(api_key="YOUR_API_KEY")

# Start a batch inference job
response = client.expression_measurement.batch.start_inference_job(
    models={
        "face": {},
        "prosody": {},
        "language": {}
    },
    urls=["https://hume-tutorials.s3.amazonaws.com/faces.zip"],
    notify=True
)

job_id = response.job_id
print(f"Job started with ID: {job_id}")

# Poll for job completion
while True:
    job_details = client.expression_measurement.batch.get_job_details(id=job_id)
    status = job_details.state.status
    
    print(f"Job status: {status}")
    
    if status == "COMPLETED":
        break
    elif status == "FAILED":
        print("Job failed!")
        exit(1)
    
    time.sleep(5)  # Wait 5 seconds before checking again

# Retrieve predictions
predictions = client.expression_measurement.batch.get_job_predictions(id=job_id)

# Process predictions
for source_prediction in predictions:
    print(f"Source: {source_prediction.source.url}")
    
    for file_prediction in source_prediction.results.predictions:
        print(f"  File: {file_prediction.file}")
        
        # Process face predictions
        if hasattr(file_prediction.models, 'face'):
            for group in file_prediction.models.face.grouped_predictions:
                for pred in group.predictions:
                    print(f"    Frame {pred.frame}:")
                    # Print top 5 emotions
                    sorted_emotions = sorted(pred.emotions, key=lambda x: x.score, reverse=True)
                    for emotion in sorted_emotions[:5]:
                        print(f"      {emotion.name}: {emotion.score:.3f}")
```

## Explanation

This example performs the following steps:

1. **Initialize the client**: Create a `HumeClient` instance with your API key.
2. **Start a job**: Call `start_inference_job` with the desired models and URLs.
3. **Poll for completion**: Repeatedly check the job status until it is completed or failed.
4. **Retrieve predictions**: Once the job is completed, retrieve the predictions using `get_job_predictions`.
5. **Process predictions**: Iterate through the predictions and print the top emotions for each frame.

This is a basic example to get you started. You can customize it to fit your specific needs.
