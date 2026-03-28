import asyncio
import logging

from app.config import settings

logger = logging.getLogger(__name__)


async def send_activation_email(email: str, token: str) -> None:
    activation_url = f"{settings.BASE_URL}/auth/activate/{token}"

    if settings.DEV_MODE or not settings.SMTP_HOST:
        # 開発モード: コンソールに表示
        print("\n" + "=" * 60)
        print(f"[開発モード] アクティベーションURL:")
        print(f"  {activation_url}")
        print("=" * 60 + "\n")
        logger.info(f"Activation URL for {email}: {activation_url}")
        return

    try:
        import aiosmtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "【投票アプリ】アカウントのアクティベーション"
        msg["From"] = settings.SMTP_FROM
        msg["To"] = email

        html_body = f"""
        <html><body>
        <h2>アカウントのアクティベーション</h2>
        <p>ご登録ありがとうございます。</p>
        <p>以下のリンクをクリックしてアカウントを有効化してください：</p>
        <p><a href="{activation_url}">{activation_url}</a></p>
        <p>このリンクは24時間有効です。</p>
        </body></html>
        """
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
    except Exception as e:
        logger.error(f"Failed to send activation email to {email}: {e}")
        # メール送信失敗時もコンソールに表示
        print(f"[メール送信失敗] アクティベーションURL: {activation_url}")
