#!/usr/bin/env python3
"""
测试流式思考内容格式化 - 验证流式响应中的思考内容是否正确处理
"""

import requests
import json

def test_thinking_stream():
    """测试流式思考内容的格式化"""
    url = "http://localhost:8083/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-key"
    }
    
    print("🌊 测试流式思考内容格式化")
    print("=" * 60)
    
    # 测试流式请求，应该触发思考
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 150,
        "stream": True,
        "messages": [
            {
                "role": "user",
                "content": "请详细解释一下机器学习的基本概念，并思考一下它的应用前景。"
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
            print("📋 流式响应内容:")
            
            thinking_content = ""
            regular_content = ""
            in_thinking = False
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    
                    # 跳过空行和注释
                    if not line_str.strip() or line_str.startswith(':'):
                        continue
                    
                    # 解析 SSE 事件
                    if line_str.startswith('event: '):
                        event_type = line_str[7:]
                        continue
                    elif line_str.startswith('data: '):
                        try:
                            data_str = line_str[6:]
                            if data_str.strip() == '[DONE]':
                                break
                                
                            data = json.loads(data_str)
                            
                            # 检查内容块增量
                            if data.get('type') == 'content_block_delta':
                                delta = data.get('delta', {})
                                if delta.get('type') == 'text_delta':
                                    text = delta.get('text', '')
                                    
                                    # 检查是否包含完整的思考内容块
                                    if '<thinking>' in text and '</thinking>' in text:
                                        print("🧠 检测到完整思考内容块")
                                        # 提取思考内容（去除标签）
                                        start_idx = text.find('<thinking>') + len('<thinking>')
                                        end_idx = text.find('</thinking>')
                                        if start_idx < end_idx:
                                            thinking_part = text[start_idx:end_idx].strip()
                                            thinking_content += thinking_part
                                            print(f"🧠 提取思考内容: {thinking_part[:50]}...")
                                        continue

                                    # 检查是否是思考内容的开始/结束标签（流式模式）
                                    if '<thinking>' in text:
                                        in_thinking = True
                                        print("🧠 检测到思考内容开始")
                                        # 移除标签，只保留内容
                                        text = text.replace('<thinking>', '').strip()
                                    elif '</thinking>' in text:
                                        in_thinking = False
                                        print("🧠 检测到思考内容结束")
                                        # 移除标签，只保留内容
                                        text = text.replace('</thinking>', '').strip()

                                    # 收集内容
                                    if in_thinking and text:
                                        thinking_content += text
                                    elif not in_thinking and text:
                                        regular_content += text
                                        
                            # 检查最终使用统计
                            elif data.get('type') == 'message_delta':
                                usage = data.get('usage', {})
                                if usage:
                                    print(f"\n📈 最终 Token 使用:")
                                    print(f"   Input tokens: {usage.get('input_tokens', 0)}")
                                    print(f"   Output tokens: {usage.get('output_tokens', 0)}")
                                    if 'thoughts_token_count' in usage:
                                        thoughts_tokens = usage['thoughts_token_count']
                                        print(f"   Thinking tokens: {thoughts_tokens}")
                                        if thoughts_tokens > 0:
                                            print("   ✅ 检测到思考 tokens")
                                        
                        except json.JSONDecodeError:
                            continue
            
            print(f"\n📝 内容分析:")
            print(f"   思考内容长度: {len(thinking_content)} 字符")
            print(f"   常规内容长度: {len(regular_content)} 字符")
            
            if thinking_content:
                print(f"   🧠 思考内容预览: {thinking_content[:100]}...")
                print("   ✅ 流式思考内容正确检测")
            else:
                print("   ❌ 未检测到思考内容")
                
            if regular_content:
                print(f"   📄 常规内容预览: {regular_content[:100]}...")
                
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🏁 流式测试完成")

if __name__ == "__main__":
    test_thinking_stream()
