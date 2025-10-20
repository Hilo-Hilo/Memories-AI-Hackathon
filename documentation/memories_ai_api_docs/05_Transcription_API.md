# Transcription API

**Version:** v1.2

The Transcription API generates accurate transcriptions and summaries of video and audio content using both audio and visual cues for enhanced accuracy.

---

## Contents

1. [Transcription video | Memories.ai](#transcription-video--memoriesai)
2. [Get Video Transcription | Memories.ai](#get-video-transcription--memoriesai)
3. [Get Audio Transcription | Memories.ai](#get-audio-transcription--memoriesai)
4. [Generate Video Summary | Memories.ai](#generate-video-summary--memoriesai)
5. [Get Video Transcription from a public video | Memories.ai](#get-video-transcription-from-a-public-video--memoriesai)
6. [Get Audio Transcription from a public video | Memories.ai](#get-audio-transcription-from-a-public-video--memoriesai)
7. [Update Video Transcription | Memories.ai](#update-video-transcription--memoriesai)

---

# Transcription video

Version: v1.2

Transcription API converts visual and autio context of the video into text representations. You could transcribe an uploaded vidoe in two ways:

*   [`VIDEO`](): Transcribing the video\'s visual content into text.
*   [`AUDIO`](): Transcribing the video\'s audio content into text.
    *   `speaker`: Recognizing each speaker in the video.
*   [`Summary`](): Get the summary of the video.
    *   `chapter`: summarize the video along the timeframe.
    *   `topic`: summarize the video by events/topics.

*   You have created a memories.ai API key.
*   At least one video has been uploaded to memories.ai and is currently in the PARSE status.

# Prerequisites

*   You have created a memories.ai API key.
*   At least one video has been uploaded to memories.ai and is currently in the PARSE status.


# Get Video Transcription

Version: v1.2

Use this API to retrieve the transcription result for a video you have uploaded.

*   You’re familiar with the concepts described on the [Platform overview]() page.
*   You have uploaded a video via the [Upload API]() and obtained its `videoNo`.
*   You have a valid memories.ai API key.

*   `https://api.memories.ai`

**GET** `/serve/api/v1/get_video_transcription`

    import requestsheaders = {"Authorization": "<API_KEY>"}params = {  "video_no": "<VIDEO_ID>",   "unique_id": "<UNIQUE_ID>"}response = requests.get("https://api.memories.ai/serve/api/v1/get_video_transcription", headers=headers, params=params)print("Status:", response.status_code)try:    print("Video Transcription Response:", response.json())except Exception:    print("Response Text:", response.text)

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| video\_no | query | string | Yes | Unique video number returned after upload |
| Authorization | header | string | Yes | Your API key for authentication |
| unique\_id | body | string | No | `default` by default |

Status code **200**

    {  "code": "0000",  "msg": "success",  "data": {    "videoNo": "VI606041694843813888",     "transcriptions": [      {        "index": 0,         "content": "Under a rocky overhang, three people are washing clothes in a shallow stream. Two individuals are seated on the pebbled ground, tending to laundry in basins, while a third person stands in the water further downstream. To the left, an open doorway reveals a room with a fireplace and a person tending to the fire. The background shows a misty, mountainous landscape with trees.",         "startTime": "0",         "endTime": "8"      }    ]  },   "success": true, "failed": false}

| Name | Type | Description |
| --- | --- | --- |
| code | string | Response status code |
| msg | string | Human-readable status message |
| data | object | Response data container |
| » videoNo | string | The unique video ID |
| » transcription | list of objects | List of transcription segments |
| »» start | float | Segment start time in seconds |
| »» end | float | Segment end time in seconds |
| »» text | string | Transcribed speech content for that time segment |

*   Ensure the video has finished processing (status: `PARSE`) before calling this API.


# Generate Video Summary

Version: v1.2

Use this API to generate a structured summary of a video, either in the form of **chapters** or **topics**.

*   You’re familiar with the concepts described on the [Platform overview]() page.
*   You have uploaded a video via the [Upload API]() and obtained its `videoNo`.
*   You have a valid memories.ai API key.
*   The video must be successfully parsed and transcribed.

*   `https://api.memories.ai`

**GET** `/serve/api/v1/generate_summary`

    import requestsheaders = {"Authorization": "<API_KEY>"}params = {    "video_no": "<VIDEO_ID>",    "type": "<TYPE>",    "unique_id": "<UNIQUE_ID>"}response = requests.get("https://api.memories.ai/serve/api/v1/generate_summary", headers=headers, params=params)print("Status:", response.status_code)try:    print("Summary Response:", response.json())except Exception:    print("Response Text:", response.text)

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| video\_no | query | string | Yes | Unique video number returned after upload |
| type | query | string | Yes | Type of summary to generate. Accepted values: `CHAPTER`, `TOPIC` |
| Authorization | header | string | Yes | Your API key for authentication |
| unique\_id | body | string | No | `default` by default |

Status code **200**

    {  "code": "0000",  "msg": "success",  "data": {    "summary": "The video seems to capture a family in a parking lot, possibly dealing with a minor emergency or preparing to leave. The audio consists of fragmented speech, mainly a child\'s voice repeating \"Mommy, you\'re going to go,\" suggesting a departure or concern. The visual content shows the family approaching their car with shopping bags and a red backpack. There is no clear indication of what\'s happening, so it\'s hard to say definitively what the video is about without additional context.",    "items": [      {        "description": "A woman, a boy, and another woman are walking towards a parked car in a parking lot. They are carrying shopping bags. The car doors are open.",        "title": "Arrival at the Car",        "start": "0"      },      {        "description": "The boy is looking at his phone near the open car door. One of the women is bending down, seemingly interacting with something on the ground near the car.",        "title": "Phone and Interaction on the Ground",        "start": "10"      },      {        "description": "Close-up view reveals objects on a concrete surface, including brown planters, a black pipe, a red tool, and a yellow broom or mop handle.",        "title": "Close-up of Objects on the Ground",        "start": "30"      }    ]  },  "success": true,  "failed": false}

| Name | Type | Description |
| --- | --- | --- |
| code | string | Response status code |
| msg | string | Human-readable status message |
| data | object | Response data container |
| » videoNo | string | The unique video ID |
| » summary\_type | string | The requested summary type (`CHAPTER` or `TOPIC`) |
| » summary | list of objects | List of structured summary segments |
| »» title | string | Title of the segment |
| »» start | float | Segment start time in seconds |
| »» end | float | Segment end time in seconds |
| »» description | string | Natural language description of the segment content |

*   Use `type=CHAPTER` for scene-based structural breakdown.
*   Use `type=TOPIC` for semantic grouping of related content.
*   Ensure the video has finished processing (status: `PARSE`) before calling this API.


# Get Audio Transcription from a public video

Version: v1.2

Use this API to retrieve the transcription result specifically from the audio track of a video from public video sources.

*   You’re familiar with the concepts described on the [Platform overview]() page.
*   You have a valid memories.ai API key.

*   `https://api.memories.ai`

**GET** `/serve/api/v1/get_public_audio_transcription`

    import requestsheaders = {"Authorization": "<API_KEY>"}params = {"video_no": "PI-594031499251159058"}response = requests.get("https://api.memories.ai/serve/api/v1/get_public_audio_transcription", headers=headers, params=params)print("Status:", response.status_code)try:    print("Audio Transcription Response:", response.json())except Exception:    print("Response Text:", response.text)

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| Authorization | header | string | Yes | Your API key for authentication |
| video\_no | query | string | Yes | Unique video number |

Status code **200**

    {  "code": "0000",  "msg": "success",  "data": {    "videoNo": "PI-594031499251159058",    "transcriptions": [      {        "index": 0,        "content": "I just got back from my friend's vintage liquidation sale.",        "startTime": "0",        "endTime": "3"      },      {        "index": 1,        "content": "Somehow I came back with two bags full of stuff.",        "startTime": "3",        "endTime": "7"      },      {        "index": 2,        "content": "Fully intended just to browse.",        "startTime": "7",        "endTime": "9"      }      ...    ]  }}

| Name | Type | Description |
| --- | --- | --- |
| code | string | Response status code |
| msg | string | Human-readable status message |
| data | object | Response data container |
| » videoNo | string | The unique video ID |
| » transcriptions | list of objects | List of transcription segments from the audio track |
| »» startTime | float | Segment start time in seconds |
| »» endTime | float | Segment end time in seconds |
| »» content | string | Transcribed speech content for that time segment |
| »» index | int | id of segment |

*   This endpoint returns only the transcription derived from the **audio track**.


