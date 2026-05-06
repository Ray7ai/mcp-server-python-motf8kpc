from fastmcp import FastMCP
from fastmcp.tools import tool
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

mcp = FastMCP("163-email-connector")

# 简单 Token 验证（推荐）
EXPECTED_TOKEN = os.getenv("MCP_AUTH_TOKEN", "your-secret-token-123")

@mcp.auth
def verify_token(token: str) -> bool:
    return token == EXPECTED_TOKEN or token == f"Bearer {EXPECTED_TOKEN}"

@tool
def send_163_email(to: str, subject: str, body: str) -> str:
    """通过163邮箱发送邮件（Grok每日提醒专用）"""
    sender = os.getenv("EMAIL_USER")
    auth_code = os.getenv("EMAIL_AUTH_CODE")

    if not sender or not auth_code:
        return "❌ 环境变量未设置"

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP_SSL('smtp.163.com', 465)
        server.login(sender, auth_code)
        server.sendmail(sender, to, msg.as_string())
        server.quit()
        return "✅ 邮件发送成功！"
    except Exception as e:
        return f"❌ 发送失败: {str(e)}"

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(mcp.app, host="0.0.0.0", port=port)
