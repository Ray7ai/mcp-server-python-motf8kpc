from fastmcp import FastMCP
from fastmcp.tools import tool
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from fastapi.responses import JSONResponse

mcp = FastMCP("163-email-connector")

# ================== 关键 OAuth Metadata（必须返回这些） ==================
@mcp.app.get("/.well-known/oauth-protected-resource")
async def protected_resource():
    return JSONResponse({
        "resource": "https://my-mcp-server-6fay.onrender.onrender.com/mcp",
        "authorization_servers": ["https://my-mcp-server-6fay.onrender.onrender.com"],
        "scopes_supported": ["send_email"],
        "bearer_methods_supported": ["header"]
    })

@mcp.app.get("/.well-known/oauth-authorization-server")
async def authorization_server():
    base = "https://my-mcp-server-6fay.onrender.onrender.com"
    return JSONResponse({
        "issuer": base,
        "authorization_endpoint": f"{base}/oauth/authorize",
        "token_endpoint": f"{base}/oauth/token",
        "response_types_supported": ["code", "token"],
        "grant_types_supported": ["client_credentials", "authorization_code"],
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
        "scopes_supported": ["send_email"]
    })

# ================== Token 验证（临时宽松） ==================
MCP_TOKEN = os.getenv("MCP_AUTH_TOKEN", "default-token-please-change")

@mcp.auth
def verify_auth(token: str = None) -> bool:
    if MCP_TOKEN == "default-token-please-change":
        return True  # 测试时临时放行
    if not token:
        return False
    clean = token.replace("Bearer ", "").strip()
    return clean == MCP_TOKEN

# ================== 163 发邮件工具 ==================
@tool
def send_163_email(to: str, subject: str, body: str) -> str:
    """通过163邮箱发送邮件（Grok每日提醒专用）"""
    sender = os.getenv("EMAIL_USER")
    auth_code = os.getenv("EMAIL_AUTH_CODE")

    if not sender or not auth_code:
        return "❌ 163环境变量未设置，请检查 Render Environment"

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
