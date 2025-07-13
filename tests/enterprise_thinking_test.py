#!/usr/bin/env python3
"""
企业级Thinking功能验证测试
验证所有thinking相关功能是否正常工作
"""

import requests
import json
import time
from datetime import datetime

def test_thinking_comprehensive():
    """全面测试thinking功能"""
    
    base_url = "http://localhost:8000/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-key"
    }
    
    test_cases = [
        {
            "name": "基础thinking测试",
            "payload": {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 200,
                "messages": [{"role": "user", "content": "解释什么是机器学习？"}],
                "thinking": {"enabled": True}
            },
            "expected": ["thinking配置生效", "正常响应"]
        },
        {
            "name": "包含思考摘要测试",
            "payload": {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 200,
                "messages": [{"role": "user", "content": "分析Python和Java的区别"}],
                "thinking": {"enabled": True, "include_thoughts": True}
            },
            "expected": ["thoughts_token_count", "is_thought_summary标记"]
        },
        {
            "name": "自定义预算测试",
            "payload": {
                "model": "claude-3-5-haiku-20241022",
                "max_tokens": 150,
                "messages": [{"role": "user", "content": "简单解释区块链"}],
                "thinking": {"enabled": True, "budget": 5000, "include_thoughts": True}
            },
            "expected": ["自定义预算生效", "小模型thinking"]
        }
    ]
    
    print("🏢 企业级Thinking功能验证测试")
    print("=" * 60)
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 测试 {i}: {test_case['name']}")
        print("-" * 40)
        
        start_time = time.time()
        
        try:
            response = requests.post(base_url, headers=headers, json=test_case['payload'], timeout=30)
            elapsed_time = time.time() - start_time
            
            print(f"⏱️  响应时间: {elapsed_time:.2f}s")
            print(f"📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()

                    # 分析响应结构
                    analysis = analyze_thinking_response(result, test_case['expected'])
                    results.append({
                        "test_name": test_case['name'],
                        "status": "PASS" if analysis['all_checks_passed'] else "FAIL",
                        "analysis": analysis,
                        "response_time": elapsed_time
                    })

                    print_analysis(analysis)

                except Exception as parse_error:
                    print(f"❌ 响应解析错误: {parse_error}")
                    print(f"   原始响应: {response.text[:200]}...")
                    results.append({
                        "test_name": test_case['name'],
                        "status": "PARSE_ERROR",
                        "error": str(parse_error),
                        "response_time": elapsed_time
                    })
                
            else:
                print(f"❌ 请求失败: {response.status_code}")
                print(f"   错误信息: {response.text}")
                results.append({
                    "test_name": test_case['name'],
                    "status": "ERROR",
                    "error": response.text,
                    "response_time": elapsed_time
                })
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            results.append({
                "test_name": test_case['name'],
                "status": "EXCEPTION",
                "error": str(e),
                "response_time": 0
            })
        
        if i < len(test_cases):
            print("\n⏳ 等待2秒后进行下一个测试...")
            time.sleep(2)
    
    # 生成测试报告
    print_test_report(results)

def analyze_thinking_response(response, expected_features):
    """分析thinking响应的详细情况"""
    analysis = {
        "all_checks_passed": True,
        "checks": {},
        "details": {}
    }
    
    # 检查基本结构
    analysis['checks']['basic_structure'] = bool(
        response.get('id') and 
        response.get('content') and 
        response.get('usage')
    )
    
    # 检查thinking tokens
    usage = response.get('usage', {})
    thoughts_count = usage.get('thoughts_token_count')
    analysis['checks']['thoughts_token_count_present'] = thoughts_count is not None
    analysis['checks']['thoughts_token_count_valid'] = thoughts_count is not None and thoughts_count > 0
    analysis['details']['thoughts_token_count'] = thoughts_count
    
    # 检查content中的思考摘要标记
    content_blocks = response.get('content', [])
    thought_summary_found = False
    for block in content_blocks:
        if block.get('metadata', {}).get('is_thought_summary'):
            thought_summary_found = True
            break
    
    analysis['checks']['thought_summary_metadata'] = thought_summary_found
    analysis['details']['content_blocks_count'] = len(content_blocks)
    
    # 检查token统计
    analysis['details']['input_tokens'] = usage.get('input_tokens', 0)
    analysis['details']['output_tokens'] = usage.get('output_tokens', 0)
    
    # 总体评估
    critical_checks = ['basic_structure', 'thoughts_token_count_present']
    analysis['all_checks_passed'] = all(analysis['checks'].get(check, False) for check in critical_checks)
    
    return analysis

def print_analysis(analysis):
    """打印分析结果"""
    print("🔍 响应分析:")
    
    checks = analysis['checks']
    details = analysis['details']
    
    # 基本检查
    print(f"   ✅ 基本结构: {'通过' if checks.get('basic_structure') else '❌ 失败'}")
    
    # Thinking相关检查
    thoughts_present = checks.get('thoughts_token_count_present')
    thoughts_valid = checks.get('thoughts_token_count_valid')
    thoughts_count = details.get('thoughts_token_count')
    
    if thoughts_present:
        if thoughts_valid:
            print(f"   ✅ Thinking tokens: {thoughts_count} (有效)")
        else:
            print(f"   ⚠️  Thinking tokens: {thoughts_count} (存在但为空)")
    else:
        print(f"   ❌ Thinking tokens: 缺失")
    
    # 思考摘要检查
    summary_found = checks.get('thought_summary_metadata')
    print(f"   {'✅' if summary_found else '❌'} 思考摘要标记: {'找到' if summary_found else '未找到'}")
    
    # Token统计
    print(f"   📊 Token统计: 输入={details.get('input_tokens')}, 输出={details.get('output_tokens')}")
    print(f"   📝 内容块数量: {details.get('content_blocks_count')}")

def print_test_report(results):
    """打印测试报告"""
    print("\n" + "=" * 60)
    print("📋 企业级Thinking功能测试报告")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['status'] == 'PASS')
    failed_tests = sum(1 for r in results if r['status'] == 'FAIL')
    error_tests = sum(1 for r in results if r['status'] == 'ERROR')
    
    print(f"📊 测试统计:")
    print(f"   总测试数: {total_tests}")
    print(f"   通过: {passed_tests} ✅")
    print(f"   失败: {failed_tests} ❌")
    print(f"   错误: {error_tests} 🚫")
    print(f"   成功率: {(passed_tests/total_tests)*100:.1f}%")
    
    print(f"\n📝 详细结果:")
    for result in results:
        status_icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "🚫", "EXCEPTION": "💥"}
        icon = status_icon.get(result['status'], "❓")
        print(f"   {icon} {result['test_name']}: {result['status']} ({result['response_time']:.2f}s)")
    
    # 企业级建议
    print(f"\n🏢 企业级部署建议:")
    if passed_tests == total_tests:
        print("   ✅ Thinking功能完全正常，可以部署到生产环境")
    elif passed_tests > 0:
        print("   ⚠️  Thinking功能部分正常，建议修复后部署")
        print("   🔧 需要修复的问题:")
        for result in results:
            if result['status'] != 'PASS':
                print(f"      - {result['test_name']}")
    else:
        print("   ❌ Thinking功能存在严重问题，不建议部署")
    
    print(f"\n⏰ 测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    test_thinking_comprehensive()
