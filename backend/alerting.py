"""
邮件告警：通过 SMTP（默认 Gmail SSL 465）发送运维告警。

所需环境变量（写入 backend/.env）：
  ALERT_SMTP_USER      发信账号，如 xxx@gmail.com
  ALERT_SMTP_PASSWORD  Gmail 应用专用密码（非登录密码）
可选：
  ALERT_EMAIL_TO       收件人，默认 poe4high.dimension@gmail.com
  ALERT_SMTP_HOST      默认 smtp.gmail.com
  ALERT_SMTP_PORT      默认 465
未配置时只写日志，不抛异常，避免告警本身拖垮调度器。
"""
import os
import smtplib
import socket
from email.message import EmailMessage

from app_logger import get_logger

logger = get_logger(__name__)

DEFAULT_ALERT_TO = "poe4high.dimension@gmail.com"


def send_email_alert(subject: str, body: str) -> bool:
    user = os.environ.get("ALERT_SMTP_USER")
    password = os.environ.get("ALERT_SMTP_PASSWORD")
    if not user or not password:
        logger.warning(f"[Alert] SMTP 未配置（ALERT_SMTP_USER/ALERT_SMTP_PASSWORD），仅记录告警: {subject}")
        return False

    msg = EmailMessage()
    msg["Subject"] = f"[Read-Tube 告警] {subject}"
    msg["From"] = user
    msg["To"] = os.environ.get("ALERT_EMAIL_TO", DEFAULT_ALERT_TO)
    msg.set_content(f"{body}\n\n-- 来自 {socket.gethostname()} 的 tldw-scheduler")

    host = os.environ.get("ALERT_SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("ALERT_SMTP_PORT", "465"))
    try:
        with smtplib.SMTP_SSL(host, port, timeout=30) as smtp:
            smtp.login(user, password)
            smtp.send_message(msg)
        logger.info(f"[Alert] 已发送告警邮件: {subject}")
        return True
    except Exception as e:
        logger.error(f"[Alert] 告警邮件发送失败: {e}")
        return False


if __name__ == "__main__":
    # 手动测试：venv/bin/python alerting.py（服务中由 systemd EnvironmentFile 注入，命令行需自行加载 .env）
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
    ok = send_email_alert("测试邮件", "这是一封 SMTP 配置测试邮件，收到说明告警通道正常。")
    print("sent" if ok else "not sent (see log)")
