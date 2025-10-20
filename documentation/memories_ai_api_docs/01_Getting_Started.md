# Getting Started

**Version:** v1.2

This section covers the essential information you need to begin using the Memories.ai API, including authentication, basic concepts, and your first API calls.

---

## Contents

1. [API Overview | Memories.ai](#api-overview--memoriesai)
2. [Quick Start | Memories.ai](#quick-start--memoriesai)
3. [Create your key | Memories.ai](#create-your-key--memoriesai)

---

# Quick Start | Memories.ai

Version: v1.2

This guide shows how to use the memories.ai API to build your own personal video management and understanding assistant.

1.  Sign up for your memories.ai account.
2.  Upload your video for encoding.
3.  [search]() highlights from videos!
4.  Start [chatting]() with videos!

The diagram below demonstrates the steps:

You can interact with the platform using any HTTP client to send requests and receive responses.

*   After signing up, navigate to the [API settings]() page to create your personal API key.
*   Videos you upload must meet the following requirements:
    *   **Video and audio formats**: The video must be encoded in a format supported by [FFmpeg]().
    *   **Audio track**: If you intend to use the [audio transcription]() feature, the uploaded video should include an audio track.

*   Use this example Jupyter notebook as a starting point to explore the Memories.ai API and to build your own application. [Example jupyter notebook]()

*   If you encounter an "Exceeding limit" error, please refer to [Rate Limit]() for more information.


# Create your key | Memories.ai

Version: v1.2

This guide walks you through how to access memories.ai APIs securely using your API key.

*   A valid **memories.ai account**
*   An API key (generated after registration)

To use the memories.ai API, you’ll first need to create an account:

1.  Go to the [memories.ai Login Page]().
2.  Sign in using Google to complete your registration.
3.  Follow the developer onboarding steps outlined below.

Once logged in, navigate to the **API Settings** page:

Click the **Create API Key** button:

Store your API key securely. You’ll need to include it in the headers or parameters of all API requests.

> If you prefer, you can continue using the legacy V1.0 authentication method by clicking the **Accredit** button. This method uses a callback URL to obtain a code and exchange it for a token. For more details, refer to the V1.0 authentication guide.


