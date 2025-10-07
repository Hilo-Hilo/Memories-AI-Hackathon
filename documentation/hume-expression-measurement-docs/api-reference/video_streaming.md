# Video Streaming Support

Yes, **Hume Expression Measurement API fully supports video streaming** through its WebSocket API for real-time analysis.

## Overview

The WebSocket API enables real-time streaming and analysis of video data, allowing applications to process live video feeds from sources like webcams and capture immediate emotional expression measurements. This is particularly useful for applications requiring instant feedback, such as live customer service tools, interactive platforms, and real-time monitoring systems.

## Supported Streaming Types

The WebSocket API supports streaming for multiple data types:

- **Video streams** (for facial expression analysis)
- **Audio streams** (for speech prosody and vocal burst analysis)
- **Text streams** (for emotional language analysis)
- **Combined video+audio streams** (for comprehensive multi-modal analysis)

## How Video Streaming Works

### Connection Method

Video streaming uses WebSocket connections to maintain persistent, two-way communication between your application and Hume's models. This allows for continuous data flow and immediate analysis results.

### Data Format

Video data must be encoded in **base64 format** before being sent through the WebSocket connection. The API processes individual video frames as images for facial expression analysis.

### Example: Base64 Encoding for Video Frames

```python
import base64
from pathlib import Path

def encode_video_frame(filepath: Path) -> str:
    with Path(filepath).open('rb') as fp:
        bytes_data = base64.b64encode(fp.read())
        encoded_data = bytes_data.decode("utf-8")
    return encoded_data

# Encode a video frame
frame_path = "path/to/video_frame.jpg"
encoded_frame = encode_video_frame(frame_path)
```

## WebSocket Streaming Features

### Real-time Data Processing

The WebSocket API leverages persistent connections to enable instant analysis and response. This is ideal for applications requiring immediate processing, such as:

- Live video conferencing with emotion detection
- Real-time customer service sentiment analysis
- Interactive gaming experiences
- Live educational platforms with student engagement monitoring

### Persistent Two-Way Communication

Unlike traditional request-response models, WebSocket streaming maintains an open connection for continuous data exchange. This facilitates ongoing analysis of video streams without the overhead of repeatedly establishing new connections.

### High Throughput and Low Latency

The API is optimized for high-performance streaming, supporting high-volume video data with minimal delay. This ensures smooth real-time analysis without sacrificing speed or responsiveness.

## Implementation Example: Facial Expression from Video Stream

```python
import asyncio
from hume import AsyncHumeClient
from hume.expression_measurement.stream import Config
from hume.expression_measurement.stream.socket_client import StreamConnectOptions
from hume.expression_measurement.stream.types import StreamFace

async def stream_video_analysis():
    client = AsyncHumeClient(api_key="YOUR_API_KEY")
    
    # Configure for facial expression analysis
    model_config = Config(face=StreamFace())
    
    stream_options = StreamConnectOptions(config=model_config)
    
    async with client.expression_measurement.stream.connect(
        options=stream_options
    ) as socket:
        # Send base64-encoded video frames
        result = await socket.send_file("path/to/video_frame.jpg")
        print(result)

asyncio.run(stream_video_analysis())
```

## Video + Audio Streaming

For comprehensive analysis, you can stream both video and audio simultaneously:

```python
import asyncio
from hume import AsyncHumeClient
from hume.expression_measurement.stream import Config
from hume.expression_measurement.stream.types import StreamFace, StreamProsody

async def stream_multimodal_analysis():
    client = AsyncHumeClient(api_key="YOUR_API_KEY")
    
    # Configure for both face and prosody analysis
    model_config = Config(
        face=StreamFace(),
        prosody=StreamProsody()
    )
    
    async with client.expression_measurement.stream.connect(
        options={"config": model_config}
    ) as socket:
        # Send video file with audio
        result = await socket.send_file("path/to/video_with_audio.mp4")
        print(result)

asyncio.run(stream_multimodal_analysis())
```

## Performance Considerations

### Frame Rate

For optimal performance and cost efficiency, consider the frame rate at which you process video:

- **Standard analysis**: 3 frames per second (default)
- **High-detail analysis**: 5-10 frames per second
- **Real-time monitoring**: 1-2 frames per second may be sufficient

The `fps_pred` parameter in the face model configuration controls how many frames per second are analyzed.

### Recommended Approach

According to Hume's documentation, **for best performance, it is recommended to pass individual frames of video as images rather than full video files** when using the streaming API. This gives you more control over frame rate and reduces processing overhead.

## Use Cases for Video Streaming

### Live Customer Service

Analyze customer facial expressions during video support calls to detect frustration, confusion, or satisfaction in real-time, allowing agents to adjust their approach dynamically.

### Interactive Education

Monitor student facial expressions during online learning sessions to detect confusion, boredom, or engagement, enabling adaptive learning experiences.

### Telehealth Applications

Support mental health professionals by providing real-time emotional expression analysis during video therapy sessions.

### Entertainment and Gaming

Create immersive experiences that respond to player emotions detected through webcam feeds.

### Video Conferencing Enhancement

Add emotional intelligence to video conferencing platforms to improve communication and collaboration.

## Pricing for Video Streaming

Video streaming through the WebSocket API uses the **same pricing as batch processing**:

- **Video with audio**: $0.0276 per minute
- **Video only**: $0.015 per minute

There is no additional cost for using the real-time WebSocket API versus the batch REST API.

## Important Notes

### Frame Processing

- Video frames are processed individually as images
- Each frame analyzed counts toward your usage
- Control costs by adjusting frame rate (`fps_pred` parameter)

### Latency

- WebSocket streaming provides low latency for real-time applications
- Actual latency depends on network conditions and video quality
- Optimize by sending appropriately sized frames

### Connection Management

- WebSocket connections should be properly managed and closed when not in use
- Implement reconnection logic for production applications
- Handle network interruptions gracefully

## Summary

Hume's Expression Measurement API provides robust support for video streaming through its WebSocket API. Whether you need to analyze live webcam feeds, process video conference streams, or build interactive applications with real-time emotion detection, the streaming API offers the performance and flexibility required for production applications. The same pricing applies to both streaming and batch processing, so your choice should be based on your technical requirements rather than cost considerations.
