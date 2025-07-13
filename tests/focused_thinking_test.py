#!/usr/bin/env python3
"""
专注的Thinking功能测试
"""

import requests
import json

def test_thinking_focused():
    """专注测试thinking功能"""
    
    url = "http://localhost:8000/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-key"
    }
    
    # 简单的thinking测试
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 150,
        "messages": [
            {
                "role": "user",
                "content": "简单解释什么是人工智能？"
            }
        ],
        "thinking": {
            "enabled": True,
            "include_thoughts": True
        }
    }
    
    print("🧠 专注Thinking功能测试")
    print("=" * 50)
    
    try:
        print("📤 发送请求...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 请求成功!")

            try:
                result = response.json()

                # 打印完整的响应用于调试
                print("🔍 完整响应 (用于调试):")
                print(json.dumps(result, ensure_ascii=False, indent=2))
                print("=" * 50)

                print("📋 响应结构分析:")
                
                # 基本信息
                print(f"   ID: {result.get('id', 'N/A')}")
                print(f"   模型: {result.get('model', 'N/A')}")
                print(f"   停止原因: {result.get('stop_reason', 'N/A')}")
                
                # Usage分析
                usage = result.get('usage', {})
                print(f"   📊 Token使用:")
                print(f"      输入: {usage.get('input_tokens', 'N/A')}")
                print(f"      输出: {usage.get('output_tokens', 'N/A')}")
                print(f"      思考: {usage.get('thoughts_token_count', 'N/A')}")
                
                # Content分析
                content = result.get('content', [])
                print(f"   📝 内容块数量: {len(content)}")
                
                for i, block in enumerate(content):
                    print(f"   📄 块 {i+1}:")
                    print(f"      类型: {block.get('type', 'N/A')}")
                    if block.get('text'):
                        text_preview = block['text'][:100] + "..." if len(block['text']) > 100 else block['text']
                        print(f"      文本: {text_preview}")
                    if block.get('metadata'):
                        print(f"      元数据: {block['metadata']}")
                        if block['metadata'].get('is_thought_summary'):
                            print("      🧠 这是思考摘要!")
                
                # 验证thinking功能
                print("\n🔍 Thinking功能验证:")
                
                # 检查1: thoughts_token_count
                thoughts_count = usage.get('thoughts_token_count')
                if thoughts_count is not None and thoughts_count > 0:
                    print(f"   ✅ 思考tokens: {thoughts_count} (正常)")
                elif thoughts_count is not None:
                    print(f"   ⚠️  思考tokens: {thoughts_count} (存在但为0)")
                else:
                    print(f"   ❌ 思考tokens: 缺失")
                
                # 检查2: 思考摘要标记
                thought_summary_found = any(
                    block.get('metadata', {}).get('is_thought_summary') if block.get('metadata') else False
                    for block in content
                )
                if thought_summary_found:
                    print(f"   ✅ 思考摘要标记: 找到")
                else:
                    print(f"   ❌ 思考摘要标记: 未找到")
                
                # 检查3: 思考相关内容
                has_thinking_content = any(
                    "思考" in block.get('text', '') or 
                    "分析" in block.get('text', '') or
                    "reasoning" in block.get('text', '').lower()
                    for block in content
                )
                if has_thinking_content:
                    print(f"   ✅ 思考相关内容: 检测到")
                else:
                    print(f"   ⚠️  思考相关内容: 未明确检测到")
                
                # 总体评估
                print(f"\n🎯 总体评估:")
                if thoughts_count and thoughts_count > 0:
                    print(f"   ✅ Thinking功能基本正常")
                    if thought_summary_found:
                        print(f"   ✅ 思考摘要功能正常")
                    else:
                        print(f"   ⚠️  思考摘要标记需要修复")
                else:
                    print(f"   ❌ Thinking功能需要修复")
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON解析错误: {e}")
                print(f"   原始响应: {response.text[:300]}...")
                
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")

if __name__ == "__main__":
    test_thinking_focused()
