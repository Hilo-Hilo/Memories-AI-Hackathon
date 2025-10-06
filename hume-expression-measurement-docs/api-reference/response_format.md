# Response Format

The Hume Expression Measurement API returns predictions in a structured JSON format. Understanding this format is essential for processing the results effectively.

## Batch API Response Structure

When you retrieve predictions from a completed batch job, the response will be an array of source predictions. Each source prediction corresponds to one of the URLs or files you submitted in the job.

### Top-Level Structure

```json
[
  {
    "source": { ... },
    "results": { ... }
  }
]
```

### Source Object

The source object identifies the origin of the predictions:

```json
{
  "type": "url",
  "url": "https://example.com/video.mp4"
}
```

### Results Object

The results object contains the predictions for all files within the source (e.g., files within a zip archive):

```json
{
  "predictions": [
    {
      "file": "video.mp4",
      "models": { ... }
    }
  ]
}
```

### Models Object

The models object contains predictions from each model that was run:

```json
{
  "face": { ... },
  "prosody": { ... },
  "language": { ... },
  "burst": { ... }
}
```

### Face Model Predictions

Face model predictions are grouped by individual faces detected in the media:

```json
{
  "grouped_predictions": [
    {
      "id": "unknown",
      "predictions": [
        {
          "frame": 0,
          "time": 0,
          "prob": 0.999,
          "box": {
            "x": 100,
            "y": 150,
            "w": 200,
            "h": 250
          },
          "emotions": [
            {
              "name": "Joy",
              "score": 0.85
            },
            {
              "name": "Amusement",
              "score": 0.72
            }
          ]
        }
      ]
    }
  ]
}
```

### Emotion Scores

Each emotion prediction includes:

- **name**: The name of the emotion (e.g., "Joy", "Sadness")
- **score**: A numerical score indicating the intensity of the expression (typically between 0 and 1)

The score represents the degree to which a human rater would assign that emotion label to the given expression.

## WebSocket API Response

The WebSocket API returns predictions in a similar format, but adapted for streaming data. The exact structure may vary depending on the type of data being sent (text, audio, video).

## Important Notes

- **Scores are not probabilities**: The scores represent the intensity of expression, not the probability that a person is experiencing that emotion.
- **Multiple emotions**: It is normal for multiple emotions to have high scores simultaneously, reflecting the complex and multifaceted nature of emotional expression.
- **Context matters**: The interpretation of emotion scores should always consider the context in which the expression occurred.
