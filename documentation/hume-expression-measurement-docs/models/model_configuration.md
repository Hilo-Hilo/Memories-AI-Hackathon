# Model Configuration

When submitting a job to the Batch API, you can configure the models to use and their parameters. If no models are specified, all models will be run with default settings.

## Available Models

The following models are available for use with the Expression Measurement API:

*   `face`: Facial Expression model
*   `burst`: Vocal Burst model
*   `prosody`: Speech Prosody model
*   `language`: Emotional Language model
*   `ner`: Named Entity Recognition model
*   `facemesh`: Facemesh model

## Configuration Parameters

Each model has its own set of configuration parameters. Here are some examples:

### Face Model

| Parameter | Type | Description | Default |
|---|---|---|---|
| `fps_pred` | integer | The number of frames per second to analyze | 3 |
| `prob_threshold` | float | The minimum probability threshold for face detection | 0.99 |
| `identify_faces` | boolean | Whether to identify individual faces | false |
| `min_face_size` | integer | The minimum size of a face to detect (in pixels) | 60 |
| `save_faces` | boolean | Whether to save detected faces as artifacts | false |

### Language Model

| Parameter | Type | Description | Default |
|---|---|---|---|
| `granularity` | string | The level of granularity for analysis (e.g., "word", "sentence") | "word" |
| `identify_speakers` | boolean | Whether to identify individual speakers | false |

### Prosody Model

| Parameter | Type | Description | Default |
|---|---|---|---|
| `granularity` | string | The level of granularity for analysis (e.g., "utterance") | "utterance" |
| `identify_speakers` | boolean | Whether to identify individual speakers | false |

## Example Configuration

Here is an example of how to configure models when starting a batch job:

```json
{
  "models": {
    "face": {
      "fps_pred": 3,
      "prob_threshold": 0.99,
      "identify_faces": false,
      "min_face_size": 60,
      "save_faces": false
    },
    "language": {
      "granularity": "word",
      "identify_speakers": false
    },
    "prosody": {
      "granularity": "utterance",
      "identify_speakers": false
    }
  },
  "urls": ["https://example.com/video.mp4"]
}
```

This configuration will run the face, language, and prosody models with the specified parameters on the video file at the given URL.
