#!/usr/bin/env python3
"""
简单的thinking功能测试
"""

import requests
import json

def test_thinking():
    url = "http://localhost:8000/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-key"
    }
    
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": "计算 2+2 等于多少？"
            }
        ],
        "thinking": {
            "enabled": True,
            "include_thoughts": True
        }
    }
    
    print("🧠 简单thinking测试...")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 响应成功!")
            
            # 检查usage中的thinking tokens
            usage = result.get('usage', {})
            print(f"📊 Usage信息: {usage}")
            
            if usage.get('thoughts_token_count') is not None:
                print(f"🧠 检测到思考tokens: {usage['thoughts_token_count']}")
            else:
                print("❌ 没有检测到思考tokens")
            
            # 检查content中的思考摘要
            for i, content in enumerate(result.get('content', [])):
                print(f"📝 Content {i}: {content.get('type', 'unknown')}")
                if content.get('metadata'):
                    print(f"   Metadata: {content['metadata']}")
                if content.get('text'):
                    print(f"   Text: {content['text'][:100]}...")
                    
        else:
            print(f"❌ 请求失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    test_thinking()
