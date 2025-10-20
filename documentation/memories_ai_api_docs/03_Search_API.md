# Search API

**Version:** v1.2

The Search API enables powerful semantic search capabilities across your video library. Search by text, audio, or images to find relevant video segments with high accuracy.

---

## Contents

1. [Search | Memories.ai](#search--memoriesai)
2. [Search from private library | Memories.ai](#search-from-private-library--memoriesai)
3. [Search from public video sources | Memories.ai](#search-from-public-video-sources--memoriesai)
4. [Search from audio | Memories.ai](#search-from-audio--memoriesai)
5. [Search for similar images | Memories.ai](#search-for-similar-images--memoriesai)
6. [Search Clips by Image | Memories.ai](#search-clips-by-image--memoriesai)

---

# Search | Memories.ai

Version: v1.2

Memories.ai stores videos like human memory by pre-indexing uploaded content. When needed, this stored context is retrieved intelligently and automatically, allowing the vision-language model to reason effectively. By integrating all available information, such as visual content, audio, text, and metadata, memories.ai builds a knowledge graph to enable comprehensive, deep understanding of videos.

*   [Search video]() – Perform semantic search across all videos or a specified set to find the most relevant ones

*   Currently, search supports **prompts in English only**.
*   Prompts in other languages (e.g., Chinese, French, Spanish) are not yet supported.


# Search from private library

Version: v1.2

Using a natural language query, this API searches through all processed videos & images and ranks the most relevant clips or items within milliseconds. Memories.ai retrieves and ranks results based on visual, audio, or image information in a way similar to human perception. With this API, developers can access the most relevant items from their entire private library.

Searching from `BY_AUDIO`, `BY_VIDEO`, and `BY_IMAGE` is supported. The most relevant clips or items will be retrieved and ranked according to the specified parameters.

*   You have created a memories.ai API key.
*   At least one video/image has been uploaded to memories.ai and is currently in `PARSE` status.

*   `https://api.memories.ai`

**POST** `/serve/api/v1/search`

    import requestsheaders = {"Authorization": "<API_KEY>"}  # API keyjson_body = {    "search_param": "<YOUR_PROMPT>",  # The search query    "search_type": "BY_VIDEO",  # 'BY_AUDIO' or 'BY_VIDEO' or 'BY_IMAGE'    "unique_id": "1",  # optional    "top_k": 3,    "filtering_level": "high"  # low/medium/high}response = requests.post(    "https://api.memories.ai/serve/api/v1/search",    headers=headers,    json=json_body)print(response.json())

Replace `API_KEY` in the code above with your actual API key and `YOUR_PROMPT` with your search query.

## Request Body[​]()

    {  "search_param": "boat in the ocean",  "search_type": "BY_VIDEO",  "unique_id": "1",  "top_k": 3,  "filtering_level": "medium"}

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| Authorization | header | string | Yes | API key used for authorization |
| search\_param | body | string | Yes | Natural language search query |
| search\_type | body | string | Yes | `BY_AUDIO`: search by audio; `BY_VIDEO`: search by video clips; `BY_IMAGE`: search from uploaded images |
| unique\_id | body | string | No | A client-defined identifier to differentiate requests. Default: `default`. |
| top\_k | body | int | No | Maximum number of top results to return. Default: system-defined. |
| filtering\_level | body | string | No | Level of filtering applied to results. Options: `low`, `medium`, `high`. |

    {  "code": "0000",  "msg": "success",  "data": [    {      "videoNo": "VI576925607808602112",      "videoName": "1920447021987282945",      "startTime": "13",      "endTime": "18",      "score": 0.5221236659362116    }  ]}

    {  "code": "0000",  "msg": "success",  "data": {    "item": [      {        "latitude": 39.9042,        "longitude": 116.4074,        "id": "619915496901337088",        "name": "OIX_ZOOM",        "img_url": "https://storage.googleapis.com/.../OIX_ZOOM.jpg?...",        "datetime_taken": "1757285520000",        "camera_model": "Canon EOS 5D"      },      {        "latitude": 39.9042,        "longitude": 116.4074,        "id": "619915496901337089",        "name": "youtube head",        "img_url": "https://storage.googleapis.com/.../youtube%20head.png?...",        "datetime_taken": "1757285520000",        "camera_model": "Canon EOS 5D"      }    ],    "current_page": 0,    "page_size": 20,    "total_count": "5"  }}

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| code | string | Yes | Response code |
| msg | string | Yes | Message with response code |
| data | object | Yes | JSON data |
| » videoNo | string | Yes | Video identifier |
| » videoName | string | No | Video name |
| » videoStatus | string | No | Current video processing status |
| » uploadTime | string | No | Upload timestamp (ms) |
| » score | float | Yes | Relevance score of the search result |
| Name | Type | Description |
| --- | --- | --- |
| code | string | Response status code |
| msg | string | Human-readable status message |
| data | object | Paginated search result object |
| » item | array | List of matching image entries |
| »» id | string | Unique image identifier |
| »» name | string | Image name |
| »» img\_url | string | Public URL to access the image |
| »» latitude | float | GPS latitude where the image was taken |
| »» longitude | float | GPS longitude where the image was taken |
| »» datetime\_taken | string | Timestamp when the image was captured (ms) |
| »» camera\_model | string | Camera model used to capture the image |
| current\_page | int | Current page number |
| page\_size | int | Number of results per page |
| total\_count | string | Total number of images matching the query |
| success | boolean | Indicates if the request was successful |
| failed | boolean | Indicates if the request failed |

*   **Use `top_k`:** Limit results to the most relevant items for efficiency.
*   **Filter tuning:** Adjust `filtering_level` to balance recall and precision (`low` = broad, `high` = strict).
*   **Prompt clarity:** Make search queries concise and descriptive for optimal ranking.


# Search from public video sources

Version: v1.2

Using a natural language query, this API searches through videos from public video platforms such as TikTok (YouTube and Instagram coming soon). Memories.ai indexes these videos and allows you to search and interact with them. You can specify the platform with the `type` parameter (`TIKTOK`, `YOUTUBE`, `INSTAGRAM`).

Searching by `BY_AUDIO` and `BY_VIDEO` is supported. The most relevant clips will be retrieved from the selected platform.

*   You have created a memories.ai API key.

*   `https://api.memories.ai`

**POST** `/serve/api/v1/search_public`

    import requestsheaders = {"Authorization": "<API_KEY>"}  # API keyjson_body = {    "search_param": "<YOUR_PROMPT>",  # The search query    "search_type": "BY_VIDEO",  # \'BY_AUDIO\' or \'BY_VIDEO\'    "type": "TIKTOK",  # \'TIKTOK\' by default, options: \'TIKTOK\', \'YOUTUBE\', \'INSTAGRAM\'    "top_k": 3,    "filtering_level": "high"  # low/medium/high}response = requests.post(    "https://api.memories.ai/serve/api/v1/search_public",    headers=headers,    json=json_body)print(response.json())

Replace `API_KEY` in the code above with your actual API key and `YOUR_PROMPT` with your search query.

## Request Body[​]()

    {  "search_param": "Find sprint race with Usain Bolt",  "search_type": "BY_VIDEO",  "type": "TIKTOK",  "top_k": 3,  "filtering_level": "medium"}

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| Authorization | header | string | Yes | API key used for authorization |
| search\_param | body | string | Yes | Natural language search query |
| search\_type | body | string | Yes | `BY_AUDIO`: search by audio; `BY_VIDEO`: search by video and return clips |
| type | body | string | No | Platform to search. Options: `TIKTOK` (default), `YOUTUBE`, `INSTAGRAM`. |
| top\_k | body | int | No | Maximum number of top results to return. |
| filtering\_level | body | string | No | Level of filtering applied to results. Options: `low`, `medium`, `high`. |

Status code **200**

    {  "code": "0000",  "msg": "success",  "data": [    {      "videoNo": "PI-600947902470296459",      "videoName": "They played in their OPPONENTS jerseys?!?",      "startTime": "23",      "endTime": "27",      "score": 0.7350679636001586    }  ]}

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| code | string | Yes | Response code |
| msg | string | Yes | Message with response code |
| data | array | Yes | List of search results |
| » videoNo | string | Yes | Video identifier |
| » videoName | string | Yes | Video name/title |
| » startTime | string | No | Start timestamp (seconds) |
| » endTime | string | No | End timestamp (seconds) |
| » score | float | Yes | Relevance score of the search result |

*   **Platform selection:** Use the `type` parameter to specify the desired dataset (TikTok, YouTube, Instagram).
*   **Use `top_k`:** Limit results to the most relevant items for efficiency.
*   **Filter tuning:** Adjust `filtering_level` to balance recall and precision (`low` = broad, `high` = strict).
*   **Prompt clarity:** Make queries concise and descriptive for optimal retrieval.


# Search from audio

Version: v1.2

The **Search from Audio** API provides a way to perform accurate text-match searches over audio transcripts stored in the system.  
You can query both **private transcripts** (associated with your account via `search_audio_transcripts`) and **public transcripts** (shared, via `search_public_audio_transcripts`).

These endpoints help you find relevant transcript snippets by keyword or natural language queries, enabling quick navigation within large audio datasets.

*   `https://api.memories.ai`

**POST** `/v1/search_audio_transcripts`

**POST** `/v1/search_public_audio_transcripts`

All requests must include the API key in the `Authorization` header.

    Authorization: <your_key>

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `page` | int | No | Page number (default: 1). |
| `page_size` | int | No | Number of results per page (default: 50, max: 100). |
| `query` | string | Yes | The search string or natural language query. |
| `unique_id` | string | No\* | A client-defined identifier to differentiate requests (private search only). |

    import requestsurl = "https://api.memories.ai/serve/api/v1/search_audio_transcripts"params = {    "page": 1,    "page_size": 100,    "unique_id": "test",    "query": "where is the love"}headers = {  "Authorization": "<your_key>"}response = requests.get(url, headers=headers, params=params)print(response.text)

    import requestsurl = "https://api.memories.ai/serve/api/v1/search_public_audio_transcripts"params = {    "page": 1,    "page_size": 100,    "query": "I don\'t know what is"}headers = {  "Authorization": "<your_key>"}response = requests.get(url, headers=headers, params=params)print(response.text)

The response is returned in JSON format with pagination support.  
Typical fields include:

    {  "results": [    {      "id": "abc123",      "audio_id": "xyz789",      "snippet": "relevant text from transcript...",      "timestamp": "00:05:23"    }  ],  "page": 1,  "page_size": 100,  "total": 250}

| Field | Type | Description |
| --- | --- | --- |
| `results` | array | A list of matching transcript snippets. Each item contains details below. |
| ├─ `id` | string | Unique identifier for the transcript snippet. |
| ├─ `audio_id` | string | Identifier of the audio file the snippet belongs to. |
| ├─ `snippet` | string | Extract of the transcript text relevant to the query. |
| ├─ `timestamp` | string | Timestamp in the audio where the snippet occurs (HH:MM:SS). |
| `page` | int | Current page number of the result set. |
| `page_size` | int | Number of results per page. |
| `total` | int | Total number of results available. |


# Search for similar images

Version: v1.2

The **Search Similar Images** API allows you to upload an image and search for visually similar images or videos within the system. Two endpoints are available:

*   **Public Similar Image Search** (`search_public_similar_images`) — compares the uploaded image with public datasets (TikTok, YouTube, Instagram).
*   **Private Similar Image Search** (`search_similar_images`) — compares the uploaded image with your own private library.

*   `https://api.memories.ai`

**POST** `/v1/search_public_similar_images`

**POST** `/v1/search_similar_images`

All requests must include the API key in the `Authorization` header.

    Authorization: <your_key>

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `type` | string | No | The dataset to search against. Options: `TIKTOK`, `YOUTUBE`, `INSTAGRAM`. Default: `TIKTOK`. |
| `file` | file | Yes | The image file to upload and compare. |
| `similarity` | int | No | The threshold (0-1) for filtering out results. |
| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `unique_id` | string | No | A client-defined identifier to differentiate requests. |
| `file` | file | Yes | The image file to upload and compare. |
| `similarity` | int | No | The threshold (0-1) for filtering out results. |

    import requestsurl = "https://api.memories.ai/serve/api/v1/search_public_similar_images"payload = {"type": "","similarity": 0.8}  # default TIKTOK (options: TIKTOK, YOUTUBE, INSTAGRAM)files = [  ("file", ("<IMAGE_NAME.png>", open("<PATH_TO_YOUR_IMAGE.png>","rb"), "image/png"))]headers = {  "Authorization": "<YOUR_API_KEY>"}response = requests.post(url, headers=headers, data=payload, files=files)print(response.text)

    import requestsurl = "https://api.memories.ai/serve/api/v1/search_similar_images"payload = {"unique_id": "test", "similarity": 0.8}files = [  ("file", ("<IMAGE_NAME.png>", open("<PATH_TO_YOUR_IMAGE.png>","rb"), "image/png"))]headers = {  "Authorization": "<YOUR_API_KEY>"}response = requests.post(url, headers=headers, data=payload, files=files)print(response.text)

The response is returned in JSON format. Typical fields include:

    {  "results": [    {      "id": "abc123",      "image_url": "https://cdn.example.com/images/abc123.png",      "similarity_score": 0.92,      "source": "TIKTOK"    }  ],  "total": 50}

| Field | Type | Description |
| --- | --- | --- |
| `results` | array | A list of similar image matches. |
| ├─ `id` | string | Unique identifier of the matched image. |
| ├─ `image_url` | string | URL of the matched image. |
| ├─ `similarity_score` | float | Similarity score (0–1, higher = more similar). |
| ├─ `source` | string | Dataset source (e.g., `TIKTOK`, `YOUTUBE`, `INSTAGRAM`). |
| `total` | int | Total number of matches found. |


