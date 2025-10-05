# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Memories AI Hackathon project that integrates with the Memories.ai API - a next-generation video understanding platform leveraging LLMs and multimodal processing to enable human-like comprehension of videos.

## API Information

**Base URL**: `https://api.memories.ai/v1.2`

**Authentication**: Bearer token in Authorization header
```
Authorization: Bearer YOUR_API_KEY
```

API key is stored in `.env` as `MEM_AI_API_KEY`. Create your key at https://memories.ai/docs/Create%20your%20key/

## Core Architecture Concepts

**Memory Augmented Generation (MAG)**: The platform retrieves from unlimited visual memory to generate context-aware outputs grounded in persistent visual context and past experiences.

**Multimodal Encoding**: Processes visual, audio, text, and metadata sources simultaneously to build a knowledge graph for comprehensive video understanding.

**Asynchronous Processing**: Video encoding/indexing is time-consuming. Use callback URLs to receive notifications when processing completes rather than polling.

**Video Status Lifecycle**:
- `UNPARSE` - Just uploaded, not yet processed
- `PARSE` - Processing complete, ready for search/chat
- `FAIL` - Processing failed (usually due to unsupported codec)

## Key API Parameters

**unique_id**: Multi-tenant namespace identifier. Groups videos by user/workspace/folder. Defaults to "default".

**callback**: Public URL to receive POST notifications when video processing completes. Returns `{"videoNo": "...", "status": "PARSE"}`.

**videoNo**: Unique identifier returned from upload endpoints, required for search/chat operations.

**session_id**: Chat session identifier for multi-turn conversations.

## API Endpoints by Category

### Upload API
- Local file: `POST /serve/api/v1/upload` (multipart/form-data with file)
- Direct URL: `POST /serve/api/v1/upload_url` (streamable video URL)
- Platform URL: `POST /serve/api/v1/scraper_url` (TikTok/YouTube/Instagram)
- Public platform: `POST /serve/api/v1/scraper_url_public` (contributes to shared library)
- Images: `POST /serve/api/v1/upload_img` (supports multiple files)

**Video Requirements**: h264, h265, vp9, or hevc codec. Include audio track for transcription features.

**Metadata Support**: datetime_taken, camera_model, latitude, longitude

### Search API
- Private library: `POST /serve/api/v1/search`
- Public videos: `POST /serve/api/v1/search_public` (TikTok/YouTube/Instagram)
- Audio transcripts: `POST /v1/search_audio_transcripts`
- Similar images: `POST /v1/search_similar_images`
- Similar public images: `POST /v1/search_public_similar_images`

**Search Modes**: `BY_VIDEO`, `BY_AUDIO`, `BY_IMAGE`

**Parameters**: search_param (natural language, English only), top_k, filtering_level (low/medium/high)

### Chat API
- Video chat: `POST /serve/api/v1/chat` (non-streaming)
- Video chat stream: `POST /serve/api/v1/chat_stream` (SSE)
- Video marketer: `POST /serve/api/v1/marketer_chat` (1M+ indexed TikTok videos)
- Marketer stream: `POST /serve/api/v1/marketer_chat_stream`
- Personal media: `POST /v1/chat_personal`
- Personal stream: `POST /v1/chat_personal_stream`

**Response Types**:
- `thinking`: AI reasoning process
- `ref`: Reference timestamps and video segments
- `content`: Generated response text

**Common Use Cases**: Summaries, highlights with timestamps, chapter divisions, editing suggestions, hashtag generation, TikTok optimization, audience analysis

**Marketer Features**: Use "@creator" or "#hashtag" to filter public video pool

### Transcription API
- Video visual transcription (BY_VIDEO)
- Audio transcription (BY_AUDIO) with speaker recognition
- Summary generation by chapter or topic

### Utils API
- List videos: Get all videos under a unique_id
- List sessions: Get chat sessions
- Delete videos: Remove from library
- Get task status: Check scraper/upload task progress

### Caption & Human ReID
**Host**: `https://security.memories.ai` (requires special API key)

- Video caption: `POST /v1/understand/upload`
- Image caption: `POST /v1/understand/uploadFile`

**Human Re-identification**: Track specific people across frames by providing reference images in `persons` parameter (max 5 reference images)

## Rate Limits

- Search API: 10 QPS
- Chat API: 1 QPS
- Exceeding limits returns HTTP 429

## Free Credits

New users receive 100 free credits. Pricing is pay-as-you-go per 1,000 minutes, 1,000 queries, or per GB storage.

## Documentation

`memories_ai_api_docs/` contains detailed API documentation:
- 00_Introduction.md - Platform overview
- 01_Getting_Started.md - Authentication
- 02_Upload_API.md - Upload methods
- 03_Search_API.md - Search capabilities
- 04_Chat_API.md - Chat examples
- 05_Transcription_API.md - Transcription features
- 06_Utils_API.md - Management utilities
- 07_Caption_API.md - Caption & ReID
- 08_Code_Examples.md - Implementation samples
- 09_Pricing_and_Rate_Limits.md - Pricing details

## Development Guidelines

**Python Dependencies**: Use `requests` library for HTTP calls

**Error Handling**:
- Check video status before search/chat (must be "PARSE")
- Handle 429 rate limit errors with backoff
- Use callbacks for async workflows

**Streaming Responses**: Set `Accept: text/event-stream` header, iterate lines, stop when receiving "done" or "[DONE]"

**Testing**: Use tools like Beeceptor for callback URL testing during development
