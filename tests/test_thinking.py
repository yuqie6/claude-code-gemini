#!/usr/bin/env python3
"""
Test script to demonstrate Gemini thinking capabilities through Claude API
"""

import requests
import json
import time

def test_thinking_feature():
    """Test different thinking configurations"""
    
    base_url = "http://localhost:8000/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-key"
    }
    
    test_cases = [
        {
            "name": "基础thinking启用",
            "payload": {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 500,
                "messages": [
                    {
                        "role": "user",
                        "content": "请解决这个数学问题：27 * 453 = ? 请显示你的计算步骤。"
                    }
                ],
                "thinking": {
                    "enabled": True
                }
            }
        },
        {
            "name": "包含思考摘要",
            "payload": {
                "model": "claude-3-5-sonnet-20241022", 
                "max_tokens": 500,
                "messages": [
                    {
                        "role": "user",
                        "content": "分析一下为什么Python比Java更适合数据科学？"
                    }
                ],
                "thinking": {
                    "enabled": True,
                    "include_thoughts": True
                }
            }
        },
        {
            "name": "自定义思考预算",
            "payload": {
                "model": "claude-3-5-haiku-20241022",
                "max_tokens": 300,
                "messages": [
                    {
                        "role": "user",
                        "content": "写一个简单的排序算法并解释其时间复杂度。"
                    }
                ],
                "thinking": {
                    "enabled": True,
                    "budget": 5000
                }
            }
        },
        {
            "name": "流式thinking",
            "payload": {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 400,
                "stream": True,
                "messages": [
                    {
                        "role": "user",
                        "content": "逐步解释什么是机器学习，包括其主要类型。"
                    }
                ],
                "thinking": {
                    "enabled": True,
                    "include_thoughts": True
                }
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"测试 {i}: {test_case['name']}")
        print(f"{'='*60}")
        
        try:
            if test_case['payload'].get('stream'):
                # 流式请求
                response = requests.post(base_url, headers=headers, json=test_case['payload'], stream=True)
                print(f"状态码: {response.status_code}")
                print("流式响应:")
                print("-" * 40)
                
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            try:
                                data = json.loads(line_str[6:])
                                if data.get('type') == 'content_block_delta':
                                    delta = data.get('delta', {})
                                    if delta.get('type') == 'text_delta':
                                        text = delta.get('text', '')
                                        is_thought = data.get('is_thought_summary', False)
                                        prefix = "🧠 [思考] " if is_thought else ""
                                        print(f"{prefix}{text}", end='', flush=True)
                                elif data.get('type') == 'message_delta':
                                    usage = data.get('usage', {})
                                    if usage.get('thoughts_token_count'):
                                        print(f"\n\n💭 思考tokens: {usage['thoughts_token_count']}")
                            except json.JSONDecodeError:
                                pass
                print("\n")
                
            else:
                # 非流式请求
                response = requests.post(base_url, headers=headers, json=test_case['payload'])
                print(f"状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print("响应内容:")
                    print("-" * 40)
                    
                    for content in result.get('content', []):
                        if content.get('type') == 'text':
                            text = content.get('text', '')
                            is_thought = content.get('metadata', {}).get('is_thought_summary', False)
                            prefix = "🧠 [思考摘要] " if is_thought else ""
                            print(f"{prefix}{text}")
                    
                    # 显示token使用情况
                    usage = result.get('usage', {})
                    print(f"\n📊 Token使用:")
                    print(f"   输入: {usage.get('input_tokens', 0)}")
                    print(f"   输出: {usage.get('output_tokens', 0)}")
                    if usage.get('thoughts_token_count'):
                        print(f"   思考: {usage['thoughts_token_count']}")
                else:
                    print(f"错误: {response.text}")
                    
        except Exception as e:
            print(f"请求失败: {e}")
        
        # 等待一下再进行下一个测试
        if i < len(test_cases):
            print("\n等待3秒后进行下一个测试...")
            time.sleep(3)

if __name__ == "__main__":
    print("🧠 Gemini Thinking功能测试")
    print("确保代理服务器正在运行在 http://localhost:8000")
    print("确保在.env文件中启用了thinking配置")
    
    input("\n按Enter键开始测试...")
    test_thinking_feature()
    
    print(f"\n{'='*60}")
    print("测试完成！")
    print("如果看到思考相关的输出，说明thinking功能正常工作。")
    print("查看服务器日志可以看到更详细的thinking配置信息。")
