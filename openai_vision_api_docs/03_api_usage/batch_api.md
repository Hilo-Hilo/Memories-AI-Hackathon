# OpenAI Batch API

## Overview

The Batch API allows for asynchronous processing of large volumes of requests at a discounted price. It is ideal for non-time-sensitive tasks.

### Key Features

- **Asynchronous Processing:** Jobs are processed in the background.
- **Cost Savings:** Approximately 50% cheaper than standard API calls.
- **High Rate Limits:** Allows for a larger number of requests compared to synchronous APIs.
- **24-Hour Completion Window:** Batches are guaranteed to be completed within 24 hours.

## Use Cases

- Bulk content generation (e.g., summaries, translations)
- Large-scale data analysis (e.g., sentiment analysis)
- Image captioning and analysis
- Offline data enrichment

## Workflow

1.  **Create a Batch File:** Prepare a `.jsonl` file where each line is a separate API request.
2.  **Upload the Batch File:** Upload the file to OpenAI's servers.
3.  **Create a Batch Job:** Initiate the batch job with the uploaded file's ID.
4.  **Check Batch Status:** Periodically check the status of the job until it is 'completed'.
5.  **Retrieve Results:** Download the output file containing the results.

## Request Format

Each line in the batch file must be a JSON object with the following structure:

```json
{
    "custom_id": "<UNIQUE_REQUEST_ID>",
    "method": "POST",
    "url": "/v1/chat/completions",
    "body": {
        "model": "<MODEL_NAME>",
        "messages": <MESSAGES_ARRAY>
    }
}
```

### Image Input with Batch API

To process images, include them in the `messages` array:

```json
{
    "custom_id": "image-request-1",
    "method": "POST",
    "url": "/v1/chat/completions",
    "body": {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What's in this image?"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://example.com/image.jpg"
                        }
                    }
                ]
            }
        ]
    }
}
```

