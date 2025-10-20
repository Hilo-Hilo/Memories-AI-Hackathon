"""
Debug script to investigate why Hume AI returns 0 frames.

This will upload a video, wait for processing, and inspect the raw API response structure.
"""

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from focus_guardian.core.config import Config
from focus_guardian.integrations.hume_client import HumeExpressionClient

# Use the session the user specified
SESSION_ID = "bb581b1b-bc22-43e8-abc8-606c8d87e59d"
CAM_VIDEO = Path(f"data/sessions/{SESSION_ID}/cam.mp4")

def debug_hume_predictions():
    """Upload video and inspect raw predictions structure."""

    print("=" * 70)
    print("HUME AI PREDICTIONS DEBUG")
    print("=" * 70)

    # Initialize client
    config = Config()
    api_key = config.get_config_value("hume_api_key")

    if not api_key:
        print("ERROR: HUME_API_KEY not found")
        return

    client = HumeExpressionClient(api_key=api_key)

    if not client.client:
        print("ERROR: Hume client not initialized")
        return

    print(f"\n✓ Client initialized")
    print(f"✓ Video: {CAM_VIDEO}")
    print(f"✓ Size: {CAM_VIDEO.stat().st_size / (1024*1024):.1f} MB")

    # Upload video
    print("\n[1/3] Uploading video...")
    job_id = client.analyze_video(
        video_path=CAM_VIDEO,
        include_face=True,
        include_prosody=False,
        include_language=False
    )

    if not job_id:
        print("ERROR: Upload failed")
        return

    print(f"✓ Uploaded - Job ID: {job_id}")

    # Poll for completion
    print("\n[2/3] Waiting for processing (5-10 minutes)...")
    status = client.poll_job(job_id, timeout=600)

    if status != "COMPLETED":
        print(f"ERROR: Job status: {status}")
        return

    print(f"✓ Processing complete")

    # Fetch raw predictions
    print("\n[3/3] Fetching predictions...")

    try:
        predictions = client.client.expression_measurement.batch.get_job_predictions(id=job_id)

        print("\n" + "=" * 70)
        print("RAW PREDICTIONS STRUCTURE")
        print("=" * 70)

        # Inspect predictions object
        print(f"\nType: {type(predictions)}")
        print(f"Length: {len(predictions)}")

        # Iterate through predictions
        for i, source_pred in enumerate(predictions):
            print(f"\n--- Source Prediction {i} ---")
            print(f"Type: {type(source_pred)}")
            print(f"Attributes: {dir(source_pred)}")

            # Check results
            if hasattr(source_pred, 'results'):
                print(f"\nResults type: {type(source_pred.results)}")
                print(f"Results attributes: {dir(source_pred.results)}")

                # Check predictions
                if hasattr(source_pred.results, 'predictions'):
                    print(f"\nPredictions count: {len(source_pred.results.predictions)}")

                    for j, file_pred in enumerate(source_pred.results.predictions):
                        print(f"\n  --- File Prediction {j} ---")
                        print(f"  Type: {type(file_pred)}")
                        print(f"  Attributes: {dir(file_pred)}")

                        # Check models
                        if hasattr(file_pred, 'models'):
                            print(f"\n  Models type: {type(file_pred.models)}")
                            print(f"  Models attributes: {dir(file_pred.models)}")

                            # Check face model
                            if hasattr(file_pred.models, 'face'):
                                face = file_pred.models.face
                                print(f"\n  Face model: {face}")
                                print(f"  Face type: {type(face)}")

                                if face:
                                    print(f"  Face attributes: {dir(face)}")

                                    # Check grouped predictions
                                    if hasattr(face, 'grouped_predictions'):
                                        groups = face.grouped_predictions
                                        print(f"\n  Grouped predictions count: {len(groups)}")

                                        for k, group in enumerate(groups):
                                            print(f"\n    --- Group {k} ---")
                                            print(f"    Type: {type(group)}")
                                            print(f"    Attributes: {dir(group)}")

                                            if hasattr(group, 'predictions'):
                                                print(f"    Predictions in group: {len(group.predictions)}")

                                                # Show first prediction
                                                if len(group.predictions) > 0:
                                                    pred = group.predictions[0]
                                                    print(f"\n    First prediction:")
                                                    print(f"    - Type: {type(pred)}")
                                                    print(f"    - Frame: {pred.frame if hasattr(pred, 'frame') else 'N/A'}")
                                                    print(f"    - Time: {pred.time if hasattr(pred, 'time') else 'N/A'}")

                                                    if hasattr(pred, 'emotions'):
                                                        print(f"    - Emotions count: {len(pred.emotions)}")
                                                        if len(pred.emotions) > 0:
                                                            emo = pred.emotions[0]
                                                            print(f"    - First emotion: {emo.name} = {emo.score}")
                                            else:
                                                print(f"    ⚠️  No predictions in group!")
                                    else:
                                        print(f"  ⚠️  Face model has no grouped_predictions attribute!")
                                else:
                                    print(f"  ⚠️  Face model is None/empty!")
                            else:
                                print(f"  ⚠️  Models has no face attribute!")
                        else:
                            print(f"  ⚠️  File prediction has no models attribute!")

        # Now parse with our method
        print("\n" + "=" * 70)
        print("PARSING WITH OUR METHOD")
        print("=" * 70)

        results = client._parse_predictions(predictions, job_id)

        print(f"\nTimeline frames: {len(results['timeline'])}")
        print(f"Frame count: {results['frame_count']}")
        print(f"Summary keys: {list(results['summary'].keys())}")

        if results['frame_count'] == 0:
            print("\n⚠️  PROBLEM: 0 frames detected!")
            print("This indicates the parsing logic is not finding face predictions.")
        else:
            print("\n✓ Frames successfully extracted")

            # Show sample
            if len(results['timeline']) > 0:
                print("\nFirst frame:")
                print(json.dumps(results['timeline'][0], indent=2))

        # Save raw response for inspection
        debug_file = Path("data/hume_debug_response.json")

        # Convert predictions to dict for JSON serialization
        debug_data = {
            "job_id": job_id,
            "num_source_predictions": len(predictions),
            "parsed_frame_count": results['frame_count'],
            "parsed_timeline_length": len(results['timeline']),
            "summary": results['summary']
        }

        with open(debug_file, 'w') as f:
            json.dump(debug_data, f, indent=2)

        print(f"\n✓ Debug data saved to: {debug_file}")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_hume_predictions()
