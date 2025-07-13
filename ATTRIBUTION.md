# 项目来源声明与致谢

## 项目来源

本项目是基于MIT许可证开源项目的衍生作品。虽然当前实现已经过大幅修改和增强，我们仍然感谢使本项目成为可能的基础工作。

## 原始项目信息

- **原始项目名称**: claude-code-proxy
- **当前项目名称**: Claude Code Gemini
- **原始作者**: 所有贡献者（详见原仓库 [Contributors](https://github.com/fuergaosi233/claude-code-proxy/graphs/contributors) 页面）
- **原始仓库**: https://github.com/fuergaosi233/claude-code-proxy
- **原始许可证**: MIT License
- **原始目的**: 使Claude Code能够与OpenAI兼容API提供商协作的代理服务器

## 主要修改和增强

本衍生作品包含大量修改和新功能：

1. **完整的API转换**: 从Claude-to-OpenAI代理转换为Claude-to-Gemini API代理
2. **全新架构**: 重新设计了整个转换层以兼容Gemini API
3. **增强功能**:
   - 添加了Gemini 2.5思考模式支持，可配置思考预算
   - 实现了完整的SSE流式响应转换
   - 添加了高级函数调用兼容性和schema转换
   - 增强了错误处理和全面的日志记录
   - 添加了多模态图像支持（实验性功能）
   - 实现了安全设置和内容过滤
4. **配置系统**: 为Gemini API完全重写了配置管理
5. **文档**: 全面的新文档和Gemini特定的使用指南
6. **模型管理**: 新的Gemini模型智能映射系统
7. **性能优化**: 带连接池的async/await架构

## 合规声明

本项目通过以下方式符合MIT许可证要求：

- ✅ 包含原始MIT许可证文本（见LICENSE文件）
- ✅ 在适用情况下保留版权声明
- ✅ 提供此归属文档
- ✅ 为衍生作品维护相同的MIT许可证

## 免责声明

本衍生作品按"原样"提供，不提供任何形式的保证。原始作者不对本衍生作品或其使用可能产生的任何问题负责。

## 贡献

如果您为本项目做出贡献，即表示您同意您的贡献将在相同的MIT许可证下授权。

---

**最后更新**: 2025-07-13
**Maintainer**: yuqie6
