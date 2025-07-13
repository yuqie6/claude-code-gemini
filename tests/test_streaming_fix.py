#!/usr/bin/env python3
"""
Test script to verify streaming response behavior
Tests both the proxy and direct Claude API for comparison
"""

import asyncio
import aiohttp
import json
import time
import sys
from datetime import datetime

async def test_streaming_response(url, headers, payload, name):
    """Test streaming response and measure character-by-character timing"""
    print(f"\n{'='*50}")
    print(f"Testing {name}")
    print(f"{'='*50}")
    
    start_time = time.time()
    char_count = 0
    chunk_count = 0
    last_char_time = start_time
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                print(f"Response status: {response.status}")
                print(f"Response headers: {dict(response.headers)}")
                print(f"\nStreaming content:")
                print("-" * 30)
                
                async for chunk in response.content.iter_any():
                    chunk_count += 1
                    current_time = time.time()
                    
                    if chunk:
                        chunk_str = chunk.decode('utf-8', errors='ignore')
                        
                        # Parse SSE events
                        if chunk_str.startswith('data: '):
                            try:
                                data_line = chunk_str[6:].strip()
                                if data_line and data_line != '[DONE]':
                                    event_data = json.loads(data_line)
                                    
                                    # Extract text from content_block_delta events
                                    if (event_data.get('type') == 'content_block_delta' and 
                                        event_data.get('delta', {}).get('type') == 'text_delta'):
                                        
                                        text = event_data['delta']['text']
                                        char_count += len(text)
                                        
                                        # Print character timing info
                                        time_since_last = current_time - last_char_time
                                        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] "
                                              f"Chunk #{chunk_count}: '{text}' "
                                              f"(+{time_since_last:.3f}s, {len(text)} chars)")
                                        
                                        last_char_time = current_time
                                        
                                        # Print the actual text for readability
                                        print(text, end='', flush=True)
                                        
                            except json.JSONDecodeError:
                                pass
                
                total_time = time.time() - start_time
                print(f"\n\n{'='*30}")
                print(f"Summary for {name}:")
                print(f"Total time: {total_time:.2f}s")
                print(f"Total characters: {char_count}")
                print(f"Total chunks: {chunk_count}")
                if char_count > 0:
                    print(f"Average chars per second: {char_count/total_time:.1f}")
                    print(f"Average chars per chunk: {char_count/chunk_count:.1f}")
                
    except Exception as e:
        print(f"Error testing {name}: {e}")

async def main():
    """Main test function"""
    
    # Test payload
    test_payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 200,
        "stream": True,
        "messages": [
            {
                "role": "user", 
                "content": "Please write a short story about a cat. Make it exactly 3 sentences."
            }
        ]
    }
    
    # Test our proxy
    proxy_url = "http://localhost:8000/v1/messages"
    proxy_headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-key"  # Our proxy doesn't validate this
    }
    
    print("Testing streaming response behavior...")
    print("This will help us verify if the fix resolves the buffering issue.")
    
    await test_streaming_response(proxy_url, proxy_headers, test_payload, "Claude-to-Gemini Proxy")
    
    # Optionally test Claude directly if API key is available
    claude_api_key = input("\nEnter Claude API key to test direct comparison (or press Enter to skip): ").strip()
    
    if claude_api_key:
        claude_url = "https://api.anthropic.com/v1/messages"
        claude_headers = {
            "Content-Type": "application/json",
            "x-api-key": claude_api_key,
            "anthropic-version": "2023-06-01"
        }
        
        await test_streaming_response(claude_url, claude_headers, test_payload, "Claude Native API")
    
    print("\n" + "="*50)
    print("Test completed!")
    print("Compare the timing patterns between proxy and native API.")
    print("Good streaming should show frequent small chunks with consistent timing.")

if __name__ == "__main__":
    asyncio.run(main())
