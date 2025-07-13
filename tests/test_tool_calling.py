#!/usr/bin/env python3
"""
测试工具调用功能 - 验证LLM是否能正常调用工具
"""

import requests
import json

def test_tool_calling():
    """测试工具调用功能"""
    url = "http://localhost:8083/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-key"
    }
    
    print("🔧 测试工具调用功能")
    print("=" * 60)
    
    # 测试请求，应该触发工具调用
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 200,
        "messages": [
            {
                "role": "user",
                "content": "请帮我计算 25 * 4 的结果，使用计算器工具。"
            }
        ],
        "tools": [
            {
                "name": "calculator",
                "description": "执行数学计算",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "要计算的数学表达式"
                        }
                    },
                    "required": ["expression"]
                }
            }
        ],
        "tool_choice": {"type": "any"}  # 强制使用工具
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        print(f"📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("📋 响应结构:")
            print(f"   ID: {result.get('id')}")
            print(f"   Model: {result.get('model')}")
            print(f"   Stop reason: {result.get('stop_reason')}")
            print(f"   Content blocks: {len(result.get('content', []))}")
            
            # 检查工具调用
            tool_calls_found = 0
            for i, block in enumerate(result.get('content', [])):
                print(f"\n📝 Content Block {i+1}:")
                print(f"   Type: {block.get('type')}")
                
                if block.get('type') == 'tool_use':
                    tool_calls_found += 1
                    print(f"   🔧 工具调用检测到!")
                    print(f"   Tool ID: {block.get('id')}")
                    print(f"   Tool Name: {block.get('name')}")
                    print(f"   Tool Input: {block.get('input')}")
                elif block.get('type') == 'text':
                    text = block.get('text', '')
                    print(f"   Text length: {len(text)} characters")
                    if text:
                        print(f"   Text preview: {text[:100]}...")
            
            # 检查Token使用
            usage = result.get('usage', {})
            print(f"\n📈 Token 使用:")
            print(f"   Input tokens: {usage.get('input_tokens', 0)}")
            print(f"   Output tokens: {usage.get('output_tokens', 0)}")
            if usage.get('thoughts_token_count'):
                print(f"   Thinking tokens: {usage.get('thoughts_token_count')}")
            
            # 结果分析
            if tool_calls_found > 0:
                print(f"\n✅ 工具调用成功! 检测到 {tool_calls_found} 个工具调用")
            else:
                print(f"\n❌ 未检测到工具调用")
                print("可能的原因:")
                print("- LLM没有选择使用工具")
                print("- 工具调用转换逻辑有问题")
                print("- tool_choice配置无效")
                
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    test_tool_calling()
