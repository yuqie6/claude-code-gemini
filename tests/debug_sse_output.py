#!/usr/bin/env python3
"""
调试SSE输出格式 - 查看实际的SSE事件序列
"""

import requests
import json

def debug_sse_output():
    """调试SSE输出格式"""
    url = "http://localhost:8083/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-key"
    }
    
    print("🔍 调试SSE输出格式")
    print("=" * 60)
    
    # 测试流式请求，应该触发思考
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 50,  # 很小的token限制，确保只有思考内容
        "stream": True,
        "messages": [
            {
                "role": "user",
                "content": "请思考一下1+1等于多少"
            }
        ],
        "thinking": {
            "enabled": True,
            "include_thoughts": True
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, stream=True, timeout=60)
        
        print(f"📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            print("📋 原始SSE事件:")
            
            event_count = 0
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    event_count += 1
                    print(f"[{event_count:03d}] {line}")
                    
                    # 解析data行
                    if line.startswith('data: '):
                        try:
                            data_str = line[6:]  # 移除 "data: " 前缀
                            data = json.loads(data_str)
                            
                            # 检查是否包含思考内容
                            if data.get('type') == 'content_block_delta':
                                delta = data.get('delta', {})
                                if delta.get('type') == 'text':
                                    text = delta.get('text', '')
                                    if '<thinking>' in text or '</thinking>' in text:
                                        print(f"    🧠 检测到思考标签: {text[:100]}...")
                                    elif text.strip():
                                        print(f"    📝 常规文本: {text[:50]}...")
                                        
                        except json.JSONDecodeError:
                            pass
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    debug_sse_output()
