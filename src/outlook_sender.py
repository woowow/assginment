import html
import win32com.client


def text_to_html(text: str) -> str:
    safe = html.escape(text)
    safe = safe.replace("\n", "<br>")
    return f"<html><body style='font-family:맑은 고딕, Arial; font-size:11pt;'>{safe}</body></html>"


def send_outlook_mail(
    subject: str,
    body_text: str,
    to_list: list,
    cc_list: list = None,
    mode: str = "draft"
):
    cc_list = cc_list or []

    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)

    mail.Subject = subject
    mail.To = ";".join(to_list)
    mail.CC = ";".join(cc_list)
    mail.HTMLBody = text_to_html(body_text)

    if mode == "send":
        mail.Send()
    else:
        mail.Save()