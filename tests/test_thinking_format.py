#!/usr/bin/env python3
"""
测试思考内容格式化 - 验证 Gemini 的思考内容是否正确转换为 Claude 格式
"""

import requests
import json

def test_thinking_format():
    """测试思考内容的格式化"""
    url = "http://localhost:8083/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-key"
    }
    
    print("🧠 测试思考内容格式化")
    print("=" * 60)
    
    # 测试请求，应该触发思考
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": "请解释一下量子计算的基本原理，并思考一下它与传统计算的区别。"
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # 检查响应结构
            print(f"📋 响应结构:")
            print(f"   ID: {result.get('id', 'N/A')}")
            print(f"   Model: {result.get('model', 'N/A')}")
            print(f"   Stop reason: {result.get('stop_reason', 'N/A')}")
            
            # 检查内容块
            content = result.get('content', [])
            print(f"   Content blocks: {len(content)}")
            
            for i, block in enumerate(content):
                print(f"\n📝 Content Block {i+1}:")
                print(f"   Type: {block.get('type', 'N/A')}")
                
                if block.get('type') == 'text':
                    text = block.get('text', '')
                    print(f"   Text length: {len(text)} characters")
                    
                    # 检查是否包含 <thinking> 标签
                    if '<thinking>' in text and '</thinking>' in text:
                        print("   ✅ 包含正确的 <thinking> 标签")
                        
                        # 提取思考内容
                        start = text.find('<thinking>') + len('<thinking>')
                        end = text.find('</thinking>')
                        thinking_content = text[start:end].strip()
                        
                        print(f"   🧠 思考内容预览: {thinking_content[:100]}...")
                        
                        # 检查思考内容外是否还有其他文本
                        before_thinking = text[:text.find('<thinking>')].strip()
                        after_thinking = text[text.find('</thinking>') + len('</thinking>'):].strip()
                        
                        if before_thinking:
                            print(f"   📄 思考前内容: {before_thinking[:50]}...")
                        if after_thinking:
                            print(f"   📄 思考后内容: {after_thinking[:50]}...")
                            
                    else:
                        print("   ❌ 未找到 <thinking> 标签")
                        print(f"   📄 文本预览: {text[:200]}...")
            
            # 检查 usage 信息
            usage = result.get('usage', {})
            print(f"\n📈 Token 使用:")
            print(f"   Input tokens: {usage.get('input_tokens', 0)}")
            print(f"   Output tokens: {usage.get('output_tokens', 0)}")
            
            if 'thoughts_token_count' in usage:
                thoughts_tokens = usage['thoughts_token_count']
                print(f"   Thinking tokens: {thoughts_tokens}")
                if thoughts_tokens > 0:
                    print("   ✅ 检测到思考 tokens")
                else:
                    print("   ⚠️ 思考 tokens 为 0")
            else:
                print("   ❌ 未找到 thoughts_token_count")
                
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🏁 测试完成")

if __name__ == "__main__":
    test_thinking_format()
