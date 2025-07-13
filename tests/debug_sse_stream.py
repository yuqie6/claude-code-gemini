#!/usr/bin/env python3
"""
调试SSE流式响应的脚本
用于查看实际发送的SSE数据内容
"""

import requests
import json

def debug_sse_stream():
    """调试SSE流式响应"""
    print("🔍 调试SSE流式响应")
    print("=" * 60)
    
    try:
        # 发送请求
        url = "http://localhost:8082/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-key"
        }
        
        data = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": "Explain the fundamentals of machine learning"
                }
            ],
            "stream": True
        }
        
        print(f"📤 发送请求到: {url}")
        response = requests.post(url, headers=headers, json=data, stream=True)
        print(f"📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            print("\n📋 原始SSE数据:")
            print("-" * 40)
            
            line_count = 0
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    line_count += 1
                    
                    # 打印前100行的原始数据
                    if line_count <= 100:
                        print(f"[{line_count:03d}] {line_str}")
                    
                    # 解析SSE事件
                    if line_str.startswith('data: '):
                        try:
                            data_str = line_str[6:]
                            if data_str.strip() == '[DONE]':
                                print(f"[{line_count:03d}] 🏁 流结束")
                                break
                                
                            data = json.loads(data_str)
                            
                            # 检查内容块增量
                            if data.get('type') == 'content_block_delta':
                                delta = data.get('delta', {})
                                if delta.get('type') == 'text':
                                    text = delta.get('text', '')
                                    
                                    # 检查是否包含思考标签
                                    if '<thinking>' in text or '</thinking>' in text:
                                        print(f"[{line_count:03d}] 🧠 发现思考标签: {text[:100]}...")
                                        
                        except json.JSONDecodeError:
                            continue
            
            print(f"\n📊 总共处理了 {line_count} 行SSE数据")
                
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 调试失败: {str(e)}")

if __name__ == "__main__":
    debug_sse_stream()
