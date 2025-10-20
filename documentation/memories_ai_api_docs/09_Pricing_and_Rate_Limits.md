# Pricing and Rate Limits

**Version:** v1.2

Information about pricing plans, free trial policies, and API rate limits to help you understand usage constraints and costs.

---

## Contents

1. [Pricing and Free Trial Policy](#pricing-and-free-trial-policy)
2. [Rate Limits | Memories.ai](#rate-limits--memoriesai)

---

# Pricing and Free Trial Policy

Version: v1.2

Memories.ai API is built to help developers seamlessly integrate powerful **AI video understanding** and **interactive features**. To help you get started quickly, we offer a **100 free credit**, allowing you to **explore the core capabilities of the API with zero barriers**.

*   Every newly registered user receives 100 credits.
*   The free credit can be used across all memories.ai API endpoints, with no limitations.
*   No credit card is required to start using the platform.

*   Once your 100 credits are exhausted\*\*, your API access will be paused. You’ll need to recharge your account to continue using the service.
    
*   After recharging, your usage will be billed according to the standard API pricing.  
    For full details, visit our [Pricing]() page.
    

*   Log in to your memories.ai account and navigate to the **API Usage** page to view your current balance and recharge options.
    
*   After recharging, your balance will be updated automatically, and you can continue using the API without interruption.
    

*   **100 free trial credits** — get started instantly, no credit card required.
*   **Flexible pay-as-you-go pricing** — scale as you grow, without hidden costs.
*   **Advanced video understanding capabilities** — empower your applications with state-of-the-art AI.

| Service Component | Unit Description | Price | Rate Limit |
| --- | --- | --- | --- |
| 1\. Index to search | Per 1,000 minutes | Free | 1 QPS (Max 2 hours) |
| 2\. Index to chat | Per 1,000 minutes | Free | 1 QPS |
| 2.1 Video Transcription | Per 1,000 queries | Free | 5 QPS |
| 2.2 Audio Transcription | Per 1,000 queries | Free | 5 QPS |
| 2.3 Update Video Transcription | Per 1,000 queries | Free | 5 QPS |
| 3\. Search | Per 1,000 search queries | Free | 10 QPS |
| 4\. Storage | Per 10 GB per month | Free | N/A (Max 10 GB) |
| 5\. Video Creator(TBD) | Per 1,000 minutes input | Free | 1 QPM |
| 6.1 Video Marketer | Per 1,000 minutes scraped | Free | N/A (Max 100 minutes) |
| 6.2 Video Marketer | Per 1 query | Free | 1 QPS |
| 6.3 Video Chat | Per 1 query | Free | 1 QPS |
| 7\. Creator Insight(TBD) | Per Creator | Free | 1 QPS |
| 8\. Video Scriptor | Per minute | Free | 3 episodes (Max 5 minutes each) |
| Service Component | Unit Description | Price |
| --- | --- | --- |
| 1\. Index to search | Per 1,000 minutes | $0.5 |
| 2\. Index to chat | Per 1,000 minutes | $5 |
| 2.1 Video Transcription | Per 1,000 queries | $0.1 |
| 2.2 Audio Transcription | Per 1,000 queries | $0.1 |
| 2.3 Update Video Transcription | Per 1,000 seconds | ~$0.1 (exact price will based on token usage) |
| 3\. Search | Per 1,000 search queries | $0.1 |
| 4\. Storage | Per 10 GB per month | $0.3 / month |
| 5\. Video Creator(TBD) | Per 1,000 minutes input | $92 |
| 6.1 Video Marketer | Per 1,000 minutes scraped | $40 |
| 6.2 Video Marketer | Per 1M tokens | $1.6 |
| 6.3 Video Chat | Per 1M tokens | $0.3 |
| 7\. Creator Insight(TBD) | Per Creator | $0.6 |
| 8\. Video Scriptor | Per minute | $0.6 |
| 9\. Video Download | Per GB | $0.12 |


# Rate Limits | Memories.ai

Version: v1.2

Rate limiting helps ensure optimal performance and smooth operation for all users by allocating resources efficiently.

The following are the throttling limits for each interface, defined by per-minute and daily (24-hour) usage caps:

| Interface | Query Per Second/Minute |
| --- | --- |
| Upload from local/streaming url | 1 QPS |
| Upload from platform/creator url | 1 QPM |
| Search | 10 QPS |
| Chat | 1 QPS |
| Video Marketer | 1 QPS |
| Video Transcription | 5 QPS |
| Audio Transcription | 5 QPS |
| Summary | 5 QPS |
| List Videos | 5 QPS |
| List Sessions | 5 QPS |
| Delete Videos | 5 QPS |
| Download Videos | 12 QPM |
| Caption Videos | 1 QPS |
| Caption Images | 5 QPS |
| Human Reid | 1 QPS |

If you exceed a rate limit, the API will return a `0429` error response. For example:

    {  "code": "0429",  "msg": "Request has exceeded the limit."}

Each newly registered user receives 100 API credit. Once this credit is used up, your service will be paused. To continue using the API, simply recharge your account — service will automatically resume upon successful payment.


