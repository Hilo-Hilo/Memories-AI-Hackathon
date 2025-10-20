import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('MEM_AI_API_KEY')
BASE_URL = "https://api.memories.ai"

headers = {
    "Authorization": API_KEY
}

VIDEO_NO = "VI630141902287491072"  # Your uploaded Berkeley walk video

def test_list_sessions():
    """Test 9A: List chat sessions"""
    print("="*60)
    print("  TEST 9A: List Chat Sessions")
    print("="*60 + "\n")

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

def test_chat_chapterize():
    """Test 9B: Chat with video to divide into chapters"""
    print("\n" + "="*60)
    print("  TEST 9B: Chapterize Video - Divide into Chapters")
    print("="*60 + "\n")

    url = f"{BASE_URL}/serve/api/v1/chat"

    payload = {
        "video_nos": [VIDEO_NO],
        "prompt": "Divide this video into chapters with timestamps and descriptions. For each chapter, provide the time range and describe what happens.",
        "unique_id": "test_berkeley_walk"
    }

    response = requests.post(url, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()

        if result.get('code') == '0000' and result.get('success'):
            data = result['data']

            # Print thinking process
            if 'thinkings' in data and data['thinkings']:
                print("\n--- AI Thinking Process ---")
                for i, thought in enumerate(data['thinkings'], 1):
                    print(f"\n{i}. {thought.get('title', 'Thinking')}")
                    print(f"   {thought.get('content', '')[:200]}...")

            # Print main content (chapters)
            print("\n" + "="*60)
            print("CHAPTERS")
            print("="*60)
            print(data.get('content', ''))

            # Print session info
            print("\n" + "-"*60)
            print(f"Session ID: {data.get('session_id', 'N/A')}")
        else:
            print(f"Error: {result.get('msg', 'Unknown error')}")
            print(json.dumps(result, indent=2))
    else:
        print(response.text)

if __name__ == "__main__":
    test_list_sessions()
    test_chat_chapterize()
