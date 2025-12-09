"""
API调试工具
提供统一的API请求调试输出
"""

import json


class APIDebugger:
    """API请求调试器"""

    def __init__(self, logger, enabled=False):
        """
        初始化调试器

        Args:
            logger: 日志记录器实例
            enabled: 是否启用调试模式
        """
        self.logger = logger
        self.enabled = enabled

    def log_request(self, url, headers, payload, pdf_data=None):
        """
        记录API请求详情

        Args:
            url: 请求URL
            headers: 请求头
            payload: 请求体
            pdf_data: Base64编码的PDF数据（可选）
        """
        if not self.enabled:
            return

        self.logger.info("\n" + "=" * 70)
        self.logger.info("🐛 调试模式：API 请求详情")
        self.logger.info("=" * 70)

        # 1. 请求URL
        self.logger.info(f"📡 请求 URL: {url}")

        # 2. 请求头（隐藏敏感信息）
        safe_headers = self._mask_sensitive_data(headers)
        self.logger.info(f"📋 请求头: {safe_headers}")

        # 3. Payload基本信息
        self.logger.info(f"📦 模型: {payload.get('model', 'N/A')}")
        self.logger.info(f"📦 Temperature: {payload.get('temperature', 'N/A')}")
        self.logger.info(f"📦 Max Tokens: {payload.get('max_tokens', 'N/A')}")
        self.logger.info(f"📦 Messages 数量: {len(payload.get('messages', []))}")

        # 4. Base64数据大小（如果提供）
        if pdf_data:
            base64_size_mb = len(pdf_data) / (1024 * 1024)
            base64_size_kb = len(pdf_data) / 1024
            self.logger.info(f"📊 Base64 编码大小: {base64_size_mb:.2f} MB ({base64_size_kb:.2f} KB)")

            # 预估原始大小（Base64会增大约33%）
            original_size_mb = base64_size_mb * 0.75
            self.logger.info(f"📊 原始 PDF 大小（估算）: {original_size_mb:.2f} MB")

        # 5. 完整请求体大小
        payload_json = json.dumps(payload, ensure_ascii=False)
        payload_size_kb = len(payload_json) / 1024
        payload_size_mb = payload_size_kb / 1024
        self.logger.info(f"📊 完整请求体大小: {payload_size_mb:.2f} MB ({payload_size_kb:.2f} KB)")

        # 6. Payload结构预览
        payload_preview = self._summarize_payload(payload, pdf_data)
        self.logger.info(f"\n📝 Payload 结构预览:")
        for line in payload_preview.split('\n')[:30]:
            self.logger.info(f"   {line}")
        if len(payload_preview.split('\n')) > 30:
            self.logger.info(f"   ... (共 {len(payload_preview.split('\n'))} 行)")

        # 7. 提示词预览
        messages = payload.get('messages', [])
        if messages and 'content' in messages[0]:
            content = messages[0]['content']
            if isinstance(content, list):
                for item in content:
                    if item.get('type') == 'text':
                        prompt = item.get('text', '')
                        prompt_preview = prompt[:200] + "..." if len(prompt) > 200 else prompt
                        self.logger.info(f"\n💬 提示词预览:")
                        for line in prompt_preview.split('\n')[:5]:
                            self.logger.info(f"   {line}")
                        break

        self.logger.info("=" * 70 + "\n")

    def _mask_sensitive_data(self, headers):
        """
        隐藏敏感信息

        Args:
            headers: 原始请求头

        Returns:
            脱敏后的请求头
        """
        safe_headers = headers.copy()
        if 'Authorization' in safe_headers:
            key = safe_headers['Authorization']
            if len(key) > 20:
                safe_headers['Authorization'] = f"{key[:15]}...{key[-10:]}"
        return safe_headers

    def _summarize_payload(self, payload, pdf_data=None):
        """
        生成Payload摘要（隐藏base64数据）

        Args:
            payload: 原始payload
            pdf_data: Base64数据（如果有）

        Returns:
            摘要文本
        """
        payload_copy = payload.copy()

        # 替换messages中的base64数据为占位符
        if 'messages' in payload_copy:
            payload_copy['messages'] = [
                {
                    "role": m["role"],
                    "content": [
                        {
                            "type": c["type"],
                            "text": c.get("text", "")[:100] + "..."
                            if c["type"] == "text" and len(c.get("text", "")) > 100
                            else c.get("text", "")
                        }
                        if c["type"] == "text"
                        else {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:application/pdf;base64,<{len(pdf_data) if pdf_data else 0} chars>"
                            }
                        }
                        for c in m.get("content", [])
                    ]
                }
                for m in payload['messages']
            ]

        return json.dumps(payload_copy, indent=2, ensure_ascii=False)
