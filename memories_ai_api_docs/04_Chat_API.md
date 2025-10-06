# Chat API

**Version:** v1.2

The Chat API provides interactive conversational interfaces for video content. Engage in multi-turn dialogues about videos, get insights, and leverage AI-powered video marketing assistance.

---

## Contents

1. [Chat | Memories.ai](#chat--memoriesai)
2. [Video Chat | Memories.ai](#video-chat--memoriesai)
3. [Video Marketer | Memories.ai](#video-marketer--memoriesai)
4. [Chat with personal media entities | Memories.ai](#chat-with-personal-media-entities--memoriesai)

---

# Chat | Memories.ai

Version: v1.2

The Video Chat API lets developers build rich, LLM-powered interactions grounded in video content. By supplying one or more `videoNos`, you can enable Memories.ai to analyze, summarize, annotate, or perform complex reasoning across your uploaded videos. Typical use cases include generating highlights, creating chapters, suggesting edits, and providing tailored insights.

To help developers better understand how to interact with the memories.ai Chat API, we’ve provided several example questions. You can refer to the examples below to structure your own prompts and get high-quality responses.

Below are sample questions and responses for testing the memories.ai Chat API. Use them as templates to guide your own queries.

**Q: Summary – Generate summaries of these videos**

**A:**  
Here are the summaries of the videos:  
**Video 1:** This video features the men's 400-meter race, highlighting top athletes like Van Dijk, Matthew Hudson-Smith, Karani James, and LeSean Merritt. Van Dijk wins with a record-breaking time of 43.03, setting a new world record. Karani James and LeSean Merritt secure silver and bronze, respectively. The victory is celebrated as a historic moment for South Africa, with commentators praising Van Dijk's performance and Usain Bolt congratulating him.

**Q: Editing Suggestions – Give me editing suggestions for these videos, from content structure, screenshots, rhythm, and audience experience, in detail**

**A:**  
Here are some editing suggestions for the video:

**Content Structure:**

*   **Opening Hook:** Start with the exciting moment of Van Dijk breaking away from the pack (around 0:03:05). Then rewind to the beginning to build context.
*   **Athlete Introductions:** Condense introductions. Focus on Van Dijk, Karani James, and LeSean Merritt.
*   **Emphasize the Record:** Use graphics to show the previous world record and how Van Dijk surpassed it.
*   **Bolt's Recognition:** Expand on Usain Bolt’s reaction. Include slow-motion replays and sound bites.

**Screenshots:**

*   **Close-ups:** Show athlete expressions mid-race.
*   **Wide Shots:** Capture the stadium’s atmosphere.
*   **Slow Motion:** Use it for race start and Van Dijk’s final push.
*   **Reactions:** Show crowd and athlete responses.

**Rhythm:**

*   **Build-up:** Increase tempo and cut frequency toward race climax.
*   **Dramatic Pause:** Use silence or slow fade after the record is broken.
*   **Variation:** Alternate between fast-paced and reflective segments.

**Audience Experience:**

*   **Context:** Briefly explain the race’s significance.
*   **Emotion:** Emphasize the joy, disappointment, and energy.
*   **Sound Design:** Layer in crowd noise, footsteps, and finish buzzer.
*   **Call to Action:** End with a prompt for comments or shares.

**Q: Highlights – Find the highlights of these videos and give timestamps**

**A:**  
Here are the highlights of the video:

*   **Athlete Introductions:** 00:00:31–00:00:37, 00:00:50–00:01:26
*   **The Start:** 00:02:31–00:02:35
*   **Van Dijk Takes the Lead:** 00:02:58–00:03:00
*   **Van Dijk Wins & Breaks Record:** 00:03:05–00:03:19
*   **Bolt Congratulates Van Dijk:** 00:06:08–00:06:19
*   **Commentary Moments:** 00:03:34–00:03:42, 00:04:48–00:04:52, 00:05:15–00:05:21, 00:05:58–00:06:06

**Q: Chapterize – Divide these videos into chapters with timestamps and descriptions**

**A:**  
Here's a breakdown of the video:

**Chapter 1: Introduction (0:00:00 – 0:00:31)**  
Sets the stage for the men's 400m final, teasing the big event.

**Chapter 2: Athlete Spotlight (0:00:31 – 0:02:20)**  
Introduces the runners, their credentials, and what’s at stake.

**Chapter 3: The Race Begins (0:02:20 – 0:03:05)**  
Focus on Van Dijk’s quick start and race dynamics.

**Chapter 4: Van Dijk's Historic Victory (0:03:05 – 0:03:42)**  
Showcases the moment Van Dijk breaks the record.

**Chapter 5: Reactions & Analysis (0:03:42 – 0:04:52)**  
Commentary, reactions, and technical breakdown of the race.

**Chapter 6: The Significance (0:04:52 – 0:06:41)**  
Wrap-up, Bolt’s praise, and the race’s legacy.

**Q: Hashtags & Topics – Generate hashtags and titles for these videos**

**A:**

**Suggested Video Titles:**

*   Van Dijk SHATTERS World Record! Unbelievable 400m Olympic Victory
*   History Made: Van Dijk's Record-Breaking 400m Run
*   From South Africa to the World: Van Dijk's Golden Moment
*   Unstoppable: Van Dijk's Dominant 400m Olympic Win
*   Bolt Was Right! Van Dijk’s 400m World Record Performance

**Hashtags:**

`#Olympics` `#Athletics` `#400m` `#WorldRecord` `#VanDijk`  
`#SouthAfrica` `#UsainBolt` `#KaraniJames` `#LeSeanMerritt`  
`#OlympicGames` `#TrackAndField` `#HistoryMade` `#GoldMedal` `#Beijing`

**Q: TikTok – Write titles, descriptions, and tags for TikTok**

**A:**

**Video Title Ideas:**

*   🤯 WORLD RECORD SHATTERED! You won't BELIEVE this race!
*   UNSEEN SPEED! 400m Record BROKEN!
*   Bolt KNEW! This runner SHOCKED the world!

**Description:**  
Watch Van Dijk make history in the 400m! This race was INSANE! Usain Bolt saw this coming!

**Tags:**  
`#Olympics` `#TrackAndField` `#Running` `#VanDijk` `#RecordBreaking`  
`#Sports` `#UsainBolt` `#SouthAfrica` `#Viral` `#Inspiration` `#FYP`

**Q: What type of audience is this video suitable for?**

**A:**  
This video is ideal for:

*   Sports fans
*   Track and field followers
*   Olympic history enthusiasts
*   Viewers who enjoy athletic achievement stories
*   Audiences looking for emotional and motivational moments


# Video Chat | Memories.ai

Version: v1.2

By providing the `videoNos`, developers can ask the Memories.ai to analyze, summarize, annotate, or perform other reasoning tasks across all uploaded videos. This API also supports streaming responses to reduce latency during generation.

*   You have created a memories.ai API key.
*   You have uploaded a video via the [Upload API]() and obtained its `videoNo`.
*   The video is currently in the `PARSE` status.

*   `https://api.memories.ai`

**POST** `/serve/api/v1/chat`

**POST** `/serve/api/v1/chat_stream`

**IMPORTANT RESPONSE FORMAT DIFFERENCE:**
- `/chat` returns a **single JSON response** with all content at once
- `/chat_stream` returns **Server-Sent Events (SSE)** for incremental streaming

## Non-Streaming Chat Example (`/chat`)

    import requests
    import json

    headers = {
        "Authorization": "<API_KEY>",
        "Content-Type": "application/json"
    }

    payload = {
        "video_nos": ["<VIDEO_ID_1>", "<VIDEO_ID_2>"],
        "prompt": "Divide this video into chapters with timestamps and descriptions",
        "session_id": "<SESSION_ID>",  # Optional
        "unique_id": "<UNIQUE_ID>"
    }

    response = requests.post(
        "https://api.memories.ai/serve/api/v1/chat",
        headers=headers,
        json=payload
    )

    if response.status_code == 200:
        result = response.json()
        print(f"Content: {result['data']['content']}")
        print(f"Session ID: {result['data']['session_id']}")

        # Access thinking process
        if 'thinkings' in result['data']:
            for thought in result['data']['thinkings']:
                print(f"Thinking: {thought['title']}")
    else:
        print(response.text)

## Streaming Chat Example (`/chat_stream`)

    import requests
    import json

    headers = {
        "Authorization": "<API_KEY>",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }

    payload = {
        "video_nos": ["<VIDEO_ID_1>", "<VIDEO_ID_2>"],
        "prompt": "Summarize the emotional moments in these videos",
        "session_id": "<SESSION_ID>",
        "unique_id": "<UNIQUE_ID>"
    }

    response = requests.post(
        "https://api.memories.ai/serve/api/v1/chat_stream",
        headers=headers,
        json=payload,
        stream=True
    )

    if response.status_code == 200:
        for line in response.iter_lines(decode_unicode=True):
            if line:
                if line.strip().lower() == 'data:"done"':
                    print("\n")
                    break
                if line.startswith("data:"):
                    print(line.replace("data:", "").strip(), end="", flush=True)
    else:
        print(response.text)

## Request Body[​]()

    {  "videoNos": [    "string"  ],  "prompt": "string",  "session_id": "123456",  "unique_id": "default",}

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| Authorization | header | string | Yes | API key used for authorization |
| Accept | header | string | No | `text/event-stream` for streaming mode |
| video\_nos | body | \[string\] | Yes | list of video numbers |
| prompt | body | string | Yes | natural language prompt |
| session\_id | body | int | No | ID of the chat session |
| unique\_id | body | string | No | `default` by default |

## Response Format

### Non-Streaming Response (`/chat`)

The `/chat` endpoint returns a **single complete JSON object**:

    {
      "code": "0000",
      "msg": "success",
      "data": {
        "role": "ASSISTANT",
        "content": "Here are proposed chapters with timestamps...",
        "thinkings": [
          {
            "title": "Based on selected videos, fetch detailed information",
            "content": "The user is asking for..."
          }
        ],
        "session_id": "630309515755999232"
      },
      "failed": false,
      "success": true
    }

**Response Fields:**
- `data.content`: The main response text with the answer
- `data.thinkings`: Array of AI reasoning steps (optional)
  - `title`: Summary of the thinking step
  - `content`: Detailed reasoning
- `data.session_id`: Session identifier for multi-turn conversations
- `data.role`: Always "ASSISTANT"

### Streaming Response (`/chat_stream`)

The `/chat_stream` endpoint returns **Server-Sent Events (SSE)** with multiple message types:

🧠 Thinking Message

    {    "type": "thinking",    "title": "Based on selected videos, fetch detailed information",     "content": "Okay, the user wants a \"Video summary.\" I\'ve been given some selected videos and need to fetch their detailed information to understand their content. This means I need to go",    "sessionId": "606120397607260160"}

🔁 Reference Message (ref)

    {	"type": "ref",	"sessionId": "606143186439766016",	"ref": [{		"video": {			"duration": "10",			"video_no": "VI606140356924534784",			"video_name": "test_video_gz_visual_understanding_fuse_s9_video_fuse_4_video_fuse_4"		},		"refItems": [{			"videoNo": "VI606140356924534784",			"startTime": 23,			"type": "keyframe"		}		{			"videoNo": "VI606140356924534784",			"startTime": 30,			"type": "visual_ts",			"endTime": 36,			"text": "A close-up view shows a collection of items on a concrete surface. To the left, two brown, round objects resembling small barrels or planters are visible. One has a blue lid or insert. Next to them, a black corrugated pipe is partially visible, along with a red flexible tube and a yellow pole with a red tip. A grey, textured wall or fence dominates the right side of the frame, with wooden planks visible at the top right."		},{			"videoNo": "VI606140356924534784",			"startTime": 30,			"type": "audio_ts",			"endTime": 36,			"text": "A close-up view shows a collection of items on a concrete surface. To the left, two brown, round objects resembling small barrels or planters are visible. One has a blue lid or insert. Next to them, a black corrugated pipe is partially visible, along with a red flexible tube and a yellow pole with a red tip. A grey, textured wall or fence dominates the right side of the frame, with wooden planks visible at the top right."		}]	}]}

💬 Content Message

    {  "type": "content",  "role": "assistant",  "content": "A\" shape, is suggested to be inspired by Eiffel\'s past",  "sessionId": "606122521255088128"}

✅ Response End Example Success Response (Status Code: 200)

    {  "code": "SUCCESS",  "data": "Done"}

⚠️ Error End Conditions Any final response where "data" is not "Done" is considered an error. Common examples include: "data": "Error" "data": "No videos found for the provided video numbers." "data": "user don\'t login" "data": "Video is not parsed:"

Status code **200**

    {  "code": "SUCCESS",  "data": "Done"}

| Name | Type | Required | Restriction | Description |
| --- | --- | --- | --- | --- |
| code | string | true | none | Response code |
| data | object or string | true | none | JSON data. `"Done"` on success; error message string or structured data otherwise |
| type | string | true | enum | Type of message, e.g., `"thinking"`, `"ref"`, `"content"` |
| title | string | false | none | Title of the thinking message (used when `type` is `"thinking"`) |
| content | string | false | none | Text content of the message (used in `"thinking"` or `"content"` types) |
| sessionId | string | true | UUID/ID | ID of the current session |
| role | string | false | enum | Role of the responder; currently used with `"assistant"` |
| ref | array | false | none | List of reference objects containing video and timestamp-based metadata |
| video | object | true | nested | Video metadata (only when `type` is `"ref"`) |
| video\_no | string | true | none | Unique video identifier |
| video\_name | string | true | none | Name of the video |
| duration | string or number | true | seconds | Duration of the video |
| refItems | array | true | none | Reference annotations such as `keyframe`, `visual_ts`, `audio_ts` |
| videoNo | string | true | none | Video identifier in `refItems` (redundant with `video_no`) |
| startTime | number | true | seconds | Start timestamp of the referenced segment |
| endTime | optional | seconds | End timestamp (if applicable, e.g., for `visual_ts` or `audio_ts`) |
| text | string | optional | none | Transcribed or described content of the referenced segment |


# Video Marketer

Version: v1.2

We have indexed over **1 million** TikTok videos for you to explore our **Large Visual Memory Model** and **Agentic QA System**.  
With this API, you can chat directly with insights from the entire 1-million-video dataset—no need to manually select videos beforehand!

1.  You could use "@xxx" or "#xxx" to filter out videos from a certain creator or hashtag when querying videos in the video marketer public vidoe pool. E.g. "What does @theshowlorios recently talk about?"

*   You have created a memories.ai API key.

*   `https://api.memories.ai`

**POST** `/serve/api/v1/marketer_chat`

**POST** `/serve/api/v1/marketer_chat_stream`

    import requestsimport jsonheaders = {    "Authorization": "<API_KEY>",    "Content-Type": "application/json",}payload = {    "prompt": "What does nike recently post?",  # User query    "session_id": "",  # Chat session ID    "unique_id": '1' # unique id for user/workspace/namespace management}response = requests.post(    "https://api.memories.ai/serve/api/v1/marketer_chat",    headers=headers,    json=payload,    stream=False)print(response.status_code)print(response.json())

    import requestsimport jsonheaders = {    "Authorization": "<API_KEY>",    "Content-Type": "application/json",    "Accept": "text/event-stream"}payload = {    "prompt": "What does nike recently post?",  # User query    "session_id": "",  # Chat session ID, Optional    "unique_id": '<UNIQUE_ID>' # Optional    "type": "TIKTOK", # 'TIKTOK' by default}response = requests.post(    "https://api.memories.ai/serve/api/v1/marketer_chat_stream",    headers=headers,    json=payload,    stream=True)if response.status_code != 200:    print(response.status_code)    print(response.text)else:    try:        full_chunks = []        for line in response.iter_lines(decode_unicode=True):            if not line:                continue            lower = line.strip().lower()            if lower in ('data:"done"', "data:[done]", "data:done", "[done]", "done"):                print("\n")                break            if line.startswith("data:"):                data = line.replace("data:", "", 1).strip()                text_piece = None                try:                    obj = json.loads(data)                    if isinstance(obj, dict):                        for k in ("content", "text", "delta", "message"):                            if isinstance(obj.get(k), str):                                text_piece = obj[k]                                break                except Exception:                    pass                if text_piece is None:                    text_piece = data                print(text_piece, end="", flush=True)                full_chunks.append(text_piece)        final_text = "".join(full_chunks)        print("\n=== FINAL ===")        print(final_text)    except Exception as e:        print(str(e))

## Request Body[​]()

    {  "prompt": "What does nike recently post?",  "session_id": "",  "unique_id": "default",  "type": "TIKTOK",}

| Name | Location | Type | Required | Description |
| --- | --- | --- | --- | --- |
| Authorization | header | string | Yes | API key used for authorization |
| Accept | header | string | No | `text/event-stream` for streaming mode |
| prompt | body | string | Yes | natural language prompt |
| session\_id | body | int | No | ID of the chat session |
| unique\_id | body | string | No | `default` by default |
| type | body | string | No | `TIKTOK` by default, `YOUTUBE`, `INSTAGRAM` |

    {  "code": "0000",  "msg": "success",  "data": {    "role": "ASSISTANT",    "content": "Opening scene: a quiet, tactile tease. Nike posted a low-key, high-significance image — two embossed logos on a dark-brown textured surface — the familiar Nike swoosh sitting to the left of the SKIMS wordmark. No captioned hashtags. The piece reads like a whisper of a collaboration rather than a full reveal.\n\nQuick facts\n- Creator: @nike  \n- Hashtags: None  \n- view count: 1,000,000  \n- like count: 59,500  \n- share count: 9,226  \n- comment count: 146\n\nWhat the post shows (what we can say with confidence)\n- Visual: embossed Nike swoosh + SKIMS logo on a dark-brown, textured material (leather-like feel).  \n- Intent: a branding-focused image that documents/announces the co-presence of both logos — effectively a teaser of a Nike × SKIMS item or capsule.  \n- Tone: minimal, premium, deliberate — designed to spark recognition and speculation rather than provide product details.\n\nEngagement and comparative context\n- Strong reach: 1M views and ~59.5K likes indicate the post cut through the noise.  \n- Share-heavy reaction: 9.2K shares with only 146 comments suggests users are forwarding/speculating more than debating — classic teaser behavior that drives earned distribution.  \n- Relative performance: the Nike post sits in the mid-to-high engagement band when compared to creator posts in this set:\n  - @pappiiq (outfit + pickups): 1,700,000 views, 115,800 likes, 1,329 shares, 700 comments — high likes and comments, lower share rate (community engagement + product show-and-tell).  \n  - @camfant (reposts reaction): 1,100,000 views, 187,400 likes, 14,300 shares, 719 comments — extremely high likes and shares (viral creator energy).  \n  Nike’s post trades off raw likes for a higher share-to-comment ratio, signaling effective intrigue and social forwarding.\n\nBroader trend signals (what this post means in context)\n- Collaboration momentum: The explicit co-branding with SKIMS signals Nike is continuing the strategy of curated partnerships with lifestyle/fashion brands to access a premium/aesthetic audience.  \n- Premium/material emphasis: The embossed logos on a textured brown surface read as a leather/upscale-material treatment — suggesting footwear, accessories, or elevated apparel rather than basic activewear.  \n- Ecosystem amplification: Nike’s logo also appears organically in creator content in this dataset (@pappiiq wearing Nike Tech pants; two @camfant clips showing Nike-branded shirts). That organic visibility plus an official brand tease creates a two-pronged approach: corporate teaser + creator-led lifestyle exposure.\n\nMarketing implications & recommended next moves\n- Teaser works — but follow up quickly: convert intrigue into product pages or hyped drops within a short window (48–72 hours) to capture share-driven interest before speculation cools.  \n- Use creators strategically: amplify the reveal via creators already wearing Nike in authentic contexts (e.g., @pappiiq’s fit and pickups) to translate buzz into purchase intent.  \n- Reveal product cues gradually: if the item is premium (leather/boot/sneaker), follow-up content should show texture, silhouette, and lifestyle shots — that matches the initial tactile cue.  \n- Encourage discussion: respond or post a follow-up that invites user questions or polls to convert shares into comments and richer audience signals.\n\nLimitations / unknowns\n- No explicit product details (name, category, release date, pricing) are visible. The material hints leather/upscale, but the post does not confirm product type.  \n- No hashtags or caption clues to indicate campaign timing or collaborators beyond SKIMS branding.\n\nBottom line\nNike’s recent post reads as a targeted teaser for a Nike × SKIMS touchpoint — minimal but effective. It’s generating shares and reach, signaling a premium collaboration and creating an opening to leverage creator partnerships already showing Nike product in lifestyle content. To capitalize fully, a timely, detail-rich follow-up and creator amplification will translate intrigue into conversions.",    "thinkings": [      {        "title": "Break down the analysis request",        "content": "The user is asking for recent posts from Nike. To answer this effectively, the first step is to determine what \"recently\" means in this context. It's likely referring to their social media presence or official annou...12938 bytes truncated...


# Chat with personal media entities

Version: v1.2

The **Chat Personal** APIs provide an interface for conversational queries.  
Two modes are supported:

*   **Streaming Mode (`chat_personal_stream`)** — responses are returned incrementally using Server-Sent Events (SSE).
*   **Standard Mode (`chat_personal`)** — responses are returned as a single JSON object.

*   `https://api.memories.ai`

**POST** `/v1/chat_personal_stream`

## **POST** `/v1/chat_personal`[​]()

All requests must include the API key in the `Authorization` header.

    Authorization: <YOUR_API__KEY>

| Header | Required | Value | Description |
| --- | --- | --- | --- |
| `Authorization` | Yes | `Bearer sk-<api_key>` | API key for authentication. |
| `Content-Type` | Yes | `application/json` | Request body format. |
| `Accept` | Yes | `text/event-stream` | Indicates the client expects a stream (SSE). |

## Request Body[​]()

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `session_id` | string | No | The chat session ID. Empty string will create a new session. |
| `prompt` | string | Yes | The user prompt (text to send to the chat model). |
| `unique_id` | string | No | A client-defined identifier to differentiate requests. |

**Example Body:**

    {  "session_id": "",  "prompt": "When did I went to the beach?",  "unique_id": "test"}

    import requestsimport jsonurl = "https://api.memories.ai/serve/api/v1/chat_personal_stream"payload = json.dumps({  "session_id": "",  "prompt": "When did I went to the beach?",  "unique_id": "test"})headers = {  'Authorization': 'sk-test',  'Content-Type': 'application/json',  'Accept': 'text/event-stream'}with requests.post(url, headers=headers, data=payload) as resp:    resp.raise_for_status()    for line in resp.iter_lines(decode_unicode=True):        if line:            print(line)

    import requestsimport jsonurl = "https://api.memories.ai/serve/api/v1/chat_personal"payload = json.dumps({  "session_id": "",  "prompt": "When did I went to the beach?",  "unique_id": "test"})headers = {  'Authorization': 'sk-test',  'Content-Type': 'application/json'}response = requests.post(url, headers=headers, data=payload)print(response.text)

The response is a stream of text events delivered as Server-Sent Events (SSE). Each line contains a chunk of the generated response until the stream ends.

    data: {"token": "This is ..."}data: {"token": "..."}data: [DONE]

    {  "session_id": "sess_12345",  "response": "This is...",  "metadata": {}}

| Field | Type | Description |
| --- | --- | --- |
| `token` | string | A chunk of text generated by the model. |
| `[DONE]` | marker | Indicates the end of the stream. |
| Field | Type | Description |
| --- | --- | --- |
| `session_id` | string | Identifier for the chat session. |
| `response` | string | The generated chat response. |
| `metadata` | object | Additional response metadata (may include search info). |


