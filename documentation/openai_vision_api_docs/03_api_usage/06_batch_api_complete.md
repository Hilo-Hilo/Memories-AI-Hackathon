# Batch API - Complete Guide

## Overview

The Batch API allows asynchronous processing of large volumes of requests at **50% cost savings**. Perfect for non-time-sensitive tasks.

### Key Benefits
- **50% cheaper** than standard API
- **Higher rate limits** for bulk processing
- **24-hour completion window**
- Same parameters as Chat Completions API

## Complete Workflow

### Step 1: Create Batch Input File (JSONL)

Each line must be a valid JSON object with this structure:

```json
{
    "custom_id": "request-1",
    "method": "POST",
    "url": "/v1/chat/completions",
    "body": {
        "model": "gpt-5-nano",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"}
        ],
        "max_tokens": 100
    }
}
```

### Step 2: Upload Batch File

#### Python
```python
from openai import OpenAI

client = OpenAI()

# Upload the batch file
batch_input_file = client.files.create(
    file=open("batch_requests.jsonl", "rb"),
    purpose="batch"
)

print(f"File ID: {batch_input_file.id}")
```

#### Node.js
```javascript
import OpenAI from 'openai';
import fs from 'fs';

const openai = new OpenAI();

const batchInputFile = await openai.files.create({
  file: fs.createReadStream('batch_requests.jsonl'),
  purpose: 'batch',
});

console.log(`File ID: ${batchInputFile.id}`);
```

### Step 3: Create Batch Job

#### Python
```python
batch_job = client.batches.create(
    input_file_id=batch_input_file.id,
    endpoint="/v1/chat/completions",
    completion_window="24h"
)

print(f"Batch ID: {batch_job.id}")
print(f"Status: {batch_job.status}")
```

#### Node.js
```javascript
const batchJob = await openai.batches.create({
  input_file_id: batchInputFile.id,
  endpoint: '/v1/chat/completions',
  completion_window: '24h',
});

console.log(`Batch ID: ${batchJob.id}`);
console.log(`Status: ${batchJob.status}`);
```

### Step 4: Check Batch Status

#### Python
```python
import time

# Poll for completion
while True:
    batch_status = client.batches.retrieve(batch_job.id)
    print(f"Status: {batch_status.status}")
    
    if batch_status.status == "completed":
        print("Batch completed!")
        break
    elif batch_status.status == "failed":
        print("Batch failed!")
        print(f"Errors: {batch_status.errors}")
        break
    
    time.sleep(60)  # Check every minute
```

#### Node.js
```javascript
// Poll for completion
while (true) {
  const batchStatus = await openai.batches.retrieve(batchJob.id);
  console.log(`Status: ${batchStatus.status}`);
  
  if (batchStatus.status === 'completed') {
    console.log('Batch completed!');
    break;
  } else if (batchStatus.status === 'failed') {
    console.log('Batch failed!');
    console.log(`Errors: ${batchStatus.errors}`);
    break;
  }
  
  await new Promise(resolve => setTimeout(resolve, 60000));  // Wait 1 minute
}
```

### Step 5: Retrieve Results

#### Python
```python
import json

# Get output file ID
result_file_id = batch_status.output_file_id

# Download results
result_content = client.files.content(result_file_id)

# Save to file
with open("batch_results.jsonl", "wb") as f:
    f.write(result_content.content)

# Parse results
results = []
with open("batch_results.jsonl", "r") as f:
    for line in f:
        result = json.loads(line)
        results.append(result)

# Process results
for result in results:
    custom_id = result["custom_id"]
    response = result["response"]["body"]["choices"][0]["message"]["content"]
    print(f"{custom_id}: {response}")
```

#### Node.js
```javascript
// Get output file ID
const resultFileId = batchStatus.output_file_id;

// Download results
const resultContent = await openai.files.content(resultFileId);
const resultText = await resultContent.text();

// Parse results
const results = resultText
  .trim()
  .split('\n')
  .map(line => JSON.parse(line));

// Process results
results.forEach(result => {
  const customId = result.custom_id;
  const response = result.response.body.choices[0].message.content;
  console.log(`${customId}: ${response}`);
});
```

## Complete End-to-End Example

### Python - Text Classification
```python
import json
import time
from openai import OpenAI

client = OpenAI()

# Step 1: Prepare data
texts_to_classify = [
    "I love this product! It's amazing!",
    "Terrible experience, would not recommend.",
    "It's okay, nothing special.",
    "Best purchase I've ever made!",
    "Waste of money."
]

# Step 2: Create batch file
batch_requests = []
for i, text in enumerate(texts_to_classify):
    request = {
        "custom_id": f"request-{i}",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-5-nano",  # Cheapest option
            "messages": [
                {
                    "role": "system",
                    "content": "Classify sentiment as: positive, negative, or neutral"
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            "max_tokens": 10
        }
    }
    batch_requests.append(request)

# Save to file
with open("sentiment_batch.jsonl", "w") as f:
    for request in batch_requests:
        f.write(json.dumps(request) + "\n")

# Step 3: Upload file
print("Uploading batch file...")
batch_file = client.files.create(
    file=open("sentiment_batch.jsonl", "rb"),
    purpose="batch"
)

# Step 4: Create batch job
print("Creating batch job...")
batch_job = client.batches.create(
    input_file_id=batch_file.id,
    endpoint="/v1/chat/completions",
    completion_window="24h"
)

print(f"Batch ID: {batch_job.id}")

# Step 5: Wait for completion
print("Waiting for completion...")
while True:
    batch_status = client.batches.retrieve(batch_job.id)
    print(f"Status: {batch_status.status} - {batch_status.request_counts}")
    
    if batch_status.status == "completed":
        break
    elif batch_status.status in ["failed", "expired", "cancelled"]:
        print(f"Batch {batch_status.status}")
        exit(1)
    
    time.sleep(60)

# Step 6: Download and process results
print("Downloading results...")
result_file_id = batch_status.output_file_id
result_content = client.files.content(result_file_id)

with open("sentiment_results.jsonl", "wb") as f:
    f.write(result_content.content)

# Parse and display results
print("\nResults:")
with open("sentiment_results.jsonl", "r") as f:
    for line in f:
        result = json.loads(line)
        custom_id = result["custom_id"]
        idx = int(custom_id.split("-")[1])
        sentiment = result["response"]["body"]["choices"][0]["message"]["content"]
        
        print(f"{texts_to_classify[idx]}")
        print(f"  → {sentiment}\n")

# Calculate cost savings
total_tokens = batch_status.request_counts.completed * 100  # Estimate
standard_cost = (total_tokens / 1_000_000) * 0.05  # gpt-5-nano input
batch_cost = standard_cost * 0.5  # 50% discount
savings = standard_cost - batch_cost

print(f"Cost with Batch API: ${batch_cost:.4f}")
print(f"Standard API cost: ${standard_cost:.4f}")
print(f"Savings: ${savings:.4f} (50%)")
```

## Vision Tasks with Batch API

### Image Captioning Batch
```python
import json
from openai import OpenAI

client = OpenAI()

# Image URLs to caption
image_urls = [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg",
    "https://example.com/image3.jpg",
]

# Create batch requests
batch_requests = []
for i, url in enumerate(image_urls):
    request = {
        "custom_id": f"image-{i}",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-5-nano",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Write a brief caption for this image."
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": url}
                        }
                    ]
                }
            ],
            "max_tokens": 100
        }
    }
    batch_requests.append(request)

# Save and upload
with open("image_captions_batch.jsonl", "w") as f:
    for request in batch_requests:
        f.write(json.dumps(request) + "\n")

# Upload and process (same as above)
batch_file = client.files.create(
    file=open("image_captions_batch.jsonl", "rb"),
    purpose="batch"
)

batch_job = client.batches.create(
    input_file_id=batch_file.id,
    endpoint="/v1/chat/completions",
    completion_window="24h"
)

print(f"Batch job created: {batch_job.id}")
```

## Batch Status Values

- `validating` - Validating input file
- `in_progress` - Processing requests
- `finalizing` - Preparing output file
- `completed` - All done, results available
- `failed` - Batch failed
- `expired` - Exceeded 24-hour window
- `cancelling` - Cancellation in progress
- `cancelled` - Batch cancelled

## Cancelling a Batch

```python
# Cancel a batch job
cancelled_batch = client.batches.cancel(batch_job.id)
print(f"Status: {cancelled_batch.status}")
```

## List All Batches

```python
# List recent batches
batches = client.batches.list(limit=10)

for batch in batches.data:
    print(f"ID: {batch.id}")
    print(f"Status: {batch.status}")
    print(f"Created: {batch.created_at}")
    print()
```

## Error Handling

```python
# Check for errors in batch
if batch_status.errors:
    print("Batch had errors:")
    for error in batch_status.errors.data:
        print(f"  - {error.message}")

# Download error file if available
if batch_status.error_file_id:
    error_content = client.files.content(batch_status.error_file_id)
    with open("batch_errors.jsonl", "wb") as f:
        f.write(error_content.content)
```

## Best Practices

1. **Use unique custom_id values**
   - Results may not be in order
   - Use custom_id to match results to inputs

2. **Set appropriate max_tokens**
   - Prevents runaway costs
   - Ensures consistent response lengths

3. **Monitor batch progress**
   - Check `request_counts` for progress
   - Handle failed/expired batches

4. **Use cheapest models when possible**
   - gpt-5-nano for simple tasks
   - Combined with 50% batch discount = maximum savings

5. **Batch size considerations**
   - No strict limit on batch size
   - Larger batches = better efficiency
   - Consider splitting very large jobs (>50k requests)

## Cost Comparison

### Example: 10,000 image captions

**Standard API (gpt-5-nano):**
- Input: 500 tokens × 10,000 = 5M tokens
- Output: 50 tokens × 10,000 = 500K tokens
- Cost: (5M × $0.05) + (0.5M × $0.40) = $250 + $200 = $450

**Batch API (gpt-5-nano):**
- Same token usage
- Cost: $450 × 0.5 = **$225**
- **Savings: $225 (50%)**

## Limitations

- Maximum 24-hour completion window
- Cannot stream responses
- Results not returned in order
- Cannot modify batch after submission
- Some models may not support batch processing
