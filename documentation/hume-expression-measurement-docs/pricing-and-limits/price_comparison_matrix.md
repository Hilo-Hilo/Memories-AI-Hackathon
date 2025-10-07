# Price Comparison Matrix

This document provides a detailed comparison of pricing for different input types and processing methods for the Hume Expression Measurement API.

## Expression Measurement API Pricing

The Expression Measurement API uses a **pay-as-you-go** model with pricing based on the type of media being processed. Both **Batch API (REST)** and **WebSocket API (real-time streaming)** use the same pricing structure.

### Pricing by Input Type

| Input Type | Features Included | Price per Unit | Notes |
|------------|------------------|----------------|-------|
| **Video with Audio** | Facial expression, Speech prosody, Vocal burst, Emotional language, Facemesh, Transcription | **$0.0276/minute** | Most comprehensive analysis |
| **Audio Only** | Speech prosody, Vocal burst, Emotional language, Transcription | **$0.0213/minute** | Voice-only analysis |
| **Video Only** | Facial expression, Facemesh | **$0.015/minute** | Visual analysis without audio |
| **Images** | Facial expression, Facemesh | **$0.00068/image** | Static image analysis |
| **Text Only** | Emotional language | **$0.00008/word** | Text-based emotion analysis |

## Detailed Price Breakdown

### Video Analysis Comparison

| Duration | Video + Audio | Video Only | Savings (Video Only) |
|----------|---------------|------------|---------------------|
| 1 minute | $0.0276 | $0.0150 | $0.0126 (45.7%) |
| 10 minutes | $0.276 | $0.150 | $0.126 (45.7%) |
| 1 hour | $1.656 | $0.900 | $0.756 (45.7%) |
| 10 hours | $16.56 | $9.00 | $7.56 (45.7%) |
| 100 hours | $165.60 | $90.00 | $75.60 (45.7%) |

### Audio Analysis Comparison

| Duration | Video + Audio | Audio Only | Savings (Audio Only) |
|----------|---------------|------------|---------------------|
| 1 minute | $0.0276 | $0.0213 | $0.0063 (22.8%) |
| 10 minutes | $0.276 | $0.213 | $0.063 (22.8%) |
| 1 hour | $1.656 | $1.278 | $0.378 (22.8%) |
| 10 hours | $16.56 | $12.78 | $3.78 (22.8%) |
| 100 hours | $165.60 | $127.80 | $37.80 (22.8%) |

### Image Analysis

| Quantity | Price | Cost per Image |
|----------|-------|----------------|
| 1 image | $0.00068 | $0.00068 |
| 100 images | $0.068 | $0.00068 |
| 1,000 images | $0.68 | $0.00068 |
| 10,000 images | $6.80 | $0.00068 |
| 100,000 images | $68.00 | $0.00068 |

### Text Analysis

| Word Count | Price | Example |
|------------|-------|---------|
| 100 words | $0.008 | Short paragraph |
| 1,000 words | $0.08 | Article |
| 10,000 words | $0.80 | Long document |
| 100,000 words | $8.00 | Book |
| 1,000,000 words | $80.00 | Large corpus |

## API Method Comparison

### Batch API vs WebSocket API

| Feature | Batch API (REST) | WebSocket API (Real-time) |
|---------|------------------|---------------------------|
| **Pricing** | Same rates as above | Same rates as above |
| **Use Case** | Large-scale processing | Real-time streaming |
| **Processing** | Asynchronous | Synchronous |
| **Input Method** | URLs or file upload | Streaming data |
| **Best For** | Archives, bulk files | Live video/audio streams |
| **Latency** | Higher (batch processing) | Lower (immediate results) |

**Important Note**: Both the Batch API and WebSocket API use the **same pricing structure**. The choice between them should be based on your use case requirements (bulk processing vs. real-time analysis) rather than cost considerations.

## Cost Optimization Strategies

### Select Only Required Models

You can reduce costs by running only the models you need:

| Configuration | Price (per minute of video+audio) | Savings |
|---------------|-----------------------------------|---------|
| All models (default) | $0.0276 | Baseline |
| Face + Language only | ~$0.0200 | ~27% |
| Prosody + Burst only | ~$0.0213 | ~23% |
| Face only (video) | $0.0150 | 45.7% |
| Language only (text from transcript) | Variable | Depends on word count |

### Choose Appropriate Input Type

Select the most appropriate input type for your needs:

- **Need facial and vocal analysis?** → Video with Audio ($0.0276/min)
- **Need only vocal analysis?** → Audio Only ($0.0213/min)
- **Need only facial analysis?** → Video Only ($0.0150/min)
- **Analyzing static images?** → Images ($0.00068/image)
- **Analyzing text transcripts?** → Text Only ($0.00008/word)

## Enterprise Pricing

For high-volume users, **Enterprise plans** offer:

- Volume discounts
- Custom pricing
- Higher rate limits
- Priority support
- Dedicated infrastructure

Contact the Hume AI sales team for enterprise pricing details.

## Example Cost Calculations

### Example 1: Customer Service Call Analysis
- **Input**: 1,000 audio calls, 5 minutes each
- **Total duration**: 5,000 minutes
- **Input type**: Audio Only
- **Cost**: 5,000 × $0.0213 = **$106.50**

### Example 2: Video Interview Analysis
- **Input**: 50 video interviews, 30 minutes each
- **Total duration**: 1,500 minutes
- **Input type**: Video with Audio
- **Cost**: 1,500 × $0.0276 = **$41.40**

### Example 3: Social Media Image Analysis
- **Input**: 10,000 images
- **Input type**: Images
- **Cost**: 10,000 × $0.00068 = **$6.80**

### Example 4: Document Sentiment Analysis
- **Input**: 500 documents, 2,000 words each
- **Total words**: 1,000,000 words
- **Input type**: Text Only
- **Cost**: 1,000,000 × $0.00008 = **$80.00**

### Example 5: Real-time Webcam Analysis (WebSocket)
- **Input**: 8 hours of streaming per day for 30 days
- **Total duration**: 240 hours = 14,400 minutes
- **Input type**: Video with Audio (streaming)
- **Cost**: 14,400 × $0.0276 = **$397.44/month**

## Summary

The Hume Expression Measurement API offers flexible pricing based on your specific needs. The key factors affecting cost are:

1. **Input Type**: Video+Audio is most expensive, text is least expensive
2. **Duration/Quantity**: Longer videos or more items cost more
3. **Model Selection**: Running fewer models can reduce costs
4. **Volume**: Enterprise discounts available for high-volume usage

Both Batch and WebSocket APIs use the same pricing, so choose based on your technical requirements rather than cost.
