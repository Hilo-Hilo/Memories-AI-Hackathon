import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('MEM_AI_API_KEY')
VIDEO_PATH = os.getenv('PATH_TO_TEST_VIDEO')
BASE_URL = "https://api.memories.ai"

headers = {
    "Authorization": API_KEY
}

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_upload_video():
    """Test 1: Upload a video from local file"""
    print_section("TEST 1: Upload Video")

    url = f"{BASE_URL}/serve/api/v1/upload"

    with open(VIDEO_PATH, 'rb') as video_file:
        files = {
            "file": (os.path.basename(VIDEO_PATH), video_file, "video/mp4")
        }
        data = {
            "unique_id": "test_berkeley_walk"
        }

        response = requests.post(url, headers=headers, files=files, data=data)
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(json.dumps(result, indent=2))

        if result.get('code') == '0000':
            video_no = result['data']['videoNo']
            print(f"\nVideo uploaded successfully! VideoNo: {video_no}")
            return video_no
        else:
            print("Upload failed!")
            return None

def wait_for_video_processing(video_no, max_wait=300):
    """Wait for video to reach PARSE status"""
    print_section("Waiting for Video Processing")

    url = f"{BASE_URL}/serve/api/v1/list_videos"
    params = {"unique_id": "test_berkeley_walk"}

    elapsed = 0
    while elapsed < max_wait:
        response = requests.get(url, headers=headers, params=params)
        result = response.json()

        if result.get('code') == '0000':
            videos = result.get('data', {}).get('videos', [])
            for video in videos:
                if video['videoNo'] == video_no:
                    status = video['videoStatus']
                    print(f"Current status: {status} (waited {elapsed}s)")

                    if status == 'PARSE':
                        print("Video processing complete!")
                        return True
                    elif status == 'FAIL':
                        print("Video processing failed!")
                        return False

        time.sleep(10)
        elapsed += 10

    print("Timeout waiting for video processing")
    return False

def test_list_videos():
    """Test 2: List all videos"""
    print_section("TEST 2: List Videos")

    url = f"{BASE_URL}/serve/api/v1/list_videos"
    params = {"unique_id": "test_berkeley_walk"}

    response = requests.get(url, headers=headers, params=params)
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2))

def test_search_video(video_no):
    """Test 3: Search for content in the video"""
    print_section("TEST 3: Search Video Content")

    url = f"{BASE_URL}/serve/api/v1/search"

    search_queries = [
        "walking on campus",
        "trees and buildings",
        "outdoor pathway"
    ]

    for query in search_queries:
        print(f"\nSearching for: '{query}'")
        payload = {
            "search_param": query,
            "search_type": "BY_VIDEO",
            "unique_id": "test_berkeley_walk",
            "top_k": 3,
            "filtering_level": "medium"
        }

        response = requests.post(url, headers=headers, json=payload)
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(json.dumps(result, indent=2))

def test_chat_with_video(video_no):
    """Test 4: Chat with the video (non-streaming)"""
    print_section("TEST 4: Chat with Video")

    url = f"{BASE_URL}/serve/api/v1/chat"

    prompts = [
        "Summarize what happens in this video",
        "Describe the environment and setting",
        "What landmarks or notable features can you see?"
    ]

    for prompt in prompts:
        print(f"\nPrompt: '{prompt}'")
        payload = {
            "video_nos": [video_no],
            "prompt": prompt,
            "unique_id": "test_berkeley_walk"
        }

        response = requests.post(url, headers=headers, json=payload)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            # Handle streaming response
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    print(line)
        else:
            print(response.text)
        print("\n" + "-"*60)

def test_chat_stream(video_no):
    """Test 5: Chat with video (streaming)"""
    print_section("TEST 5: Chat with Video (Streaming)")

    url = f"{BASE_URL}/serve/api/v1/chat_stream"

    headers_stream = headers.copy()
    headers_stream["Accept"] = "text/event-stream"

    payload = {
        "video_nos": [video_no],
        "prompt": "Find the highlights of this walk and give timestamps",
        "unique_id": "test_berkeley_walk"
    }

    response = requests.post(url, headers=headers_stream, json=payload, stream=True)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        print("\nStreaming response:")
        for line in response.iter_lines(decode_unicode=True):
            if line:
                if line.strip().lower() in ('data:"done"', 'data:[done]', 'data:done'):
                    print("\n[Stream complete]")
                    break
                if line.startswith("data:"):
                    data = line.replace("data:", "", 1).strip()
                    try:
                        obj = json.loads(data)
                        if obj.get('type') == 'content':
                            print(obj.get('content', ''), end='', flush=True)
                    except:
                        print(data, end='', flush=True)
    else:
        print(response.text)

def test_transcription(video_no):
    """Test 6: Get video transcription"""
    print_section("TEST 6: Video Transcription")

    # Note: Actual transcription endpoint may vary
    # This is a placeholder based on documentation
    print("Note: Transcription API endpoint varies by implementation")
    print(f"Would transcribe video: {video_no}")

def test_search_public():
    """Test 7: Search public videos"""
    print_section("TEST 7: Search Public Videos")

    url = f"{BASE_URL}/serve/api/v1/search_public"

    payload = {
        "search_param": "walking on college campus tour",
        "search_type": "BY_VIDEO",
        "type": "TIKTOK",
        "top_k": 3,
        "filtering_level": "high"
    }

    response = requests.post(url, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2))

def test_marketer_chat():
    """Test 8: Video Marketer Chat"""
    print_section("TEST 8: Video Marketer Chat")

    url = f"{BASE_URL}/serve/api/v1/marketer_chat"

    payload = {
        "prompt": "What are popular campus tour videos on TikTok?",
        "unique_id": "test_berkeley_walk",
        "type": "TIKTOK"
    }

    response = requests.post(url, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(json.dumps(result, indent=2))
    else:
        print(response.text)

def test_list_sessions():
    """Test 9: List chat sessions"""
    print_section("TEST 9: List Chat Sessions")

    url = f"{BASE_URL}/serve/api/v1/list_sessions"
    params = {
        "unique_id": "test_berkeley_walk",
        "page": 1,
        "page_size": 20
    }

    response = requests.get(url, headers=headers, params=params)
    print(f"Status Code: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2))

def run_all_tests():
    """Run all API capability tests"""
    print("\n" + "="*60)
    print("  MEMORIES.AI API - COMPREHENSIVE TEST SUITE")
    print("  Testing with Berkeley Campus POV Walk Video")
    print("="*60)

    # Test 1: Upload video
    video_no = test_upload_video()

    if not video_no:
        print("\nFailed to upload video. Stopping tests.")
        return

    # Wait for processing
    if not wait_for_video_processing(video_no):
        print("\nVideo processing failed or timed out. Some tests may fail.")

    # Test 2: List videos
    test_list_videos()

    # Test 3: Search video content
    test_search_video(video_no)

    # Test 4: Chat with video
    test_chat_with_video(video_no)

    # Test 5: Chat streaming
    test_chat_stream(video_no)

    # Test 6: Transcription
    test_transcription(video_no)

    # Test 7: Search public videos
    test_search_public()

    # Test 8: Video marketer chat
    test_marketer_chat()

    # Test 9: List sessions
    test_list_sessions()

    print_section("ALL TESTS COMPLETE")
    print(f"Uploaded VideoNo: {video_no}")
    print("Note: Video remains in your library under unique_id 'test_berkeley_walk'")

if __name__ == "__main__":
    run_all_tests()
