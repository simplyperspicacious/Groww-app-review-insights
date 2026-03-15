"""
Email Builder (Phase 6).

Reads the Markdown pulse, converts it to HTML, and wraps it in a
responsive email template string. Returns both HTML and fallback Text.
"""

import markdown

from utils.logger import get_logger

logger = get_logger(__name__)

# Sleek, premium, minimalist CSS for the email.
_EMAIL_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body {{
        font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        line-height: 1.7;
        color: #2c3e50;
        background-color: #f4f7f6;
        margin: 0;
        padding: 40px 20px;
        -webkit-font-smoothing: antialiased;
    }}
    .container {{
        max-width: 640px;
        margin: 0 auto;
        background-color: #ffffff;
        border-radius: 12px;
        padding: 40px;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
    }}
    .header {{
        text-align: center;
        border-bottom: 2px solid #00d09c; /* Groww Green */
        padding-bottom: 24px;
        margin-bottom: 32px;
    }}
    .header h2 {{
        margin: 0;
        color: #1a1a1a;
        font-weight: 600;
        letter-spacing: -0.5px;
    }}
    h3 {{
        color: #1a1a1a;
        margin-top: 32px;
        font-weight: 600;
        letter-spacing: -0.3px;
        border-bottom: 1px solid #eaeaea;
        padding-bottom: 8px;
    }}
    p {{
        margin-bottom: 16px;
    }}
    strong {{
        color: #111111;
        font-weight: 600;
    }}
    ul, ol {{
        padding-left: 24px;
        margin-bottom: 24px;
    }}
    li {{
        margin-bottom: 12px;
    }}
    blockquote {{
        border-left: 3px solid #00d09c;
        margin: 24px 0;
        padding: 16px 20px;
        color: #4a5568;
        font-style: italic;
        background-color: #fcfcfc;
        border-radius: 0 8px 8px 0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }}
    blockquote p {{
        margin: 0;
    }}
    .footer {{
        margin-top: 48px;
        font-size: 13px;
        color: #a0aec0;
        text-align: center;
        border-top: 1px solid #f0f0f0;
        padding-top: 24px;
    }}
</style>
</head>
<body>
    <div class="container">
        <!-- Content injected here -->
        {html_content}
        
        <div class="footer">
            <p>Powered by Groq & Gemini • 100% Free Tier Stack</p>
        </div>
    </div>
</body>
</html>
"""


def build_email_content(markdown_text: str) -> tuple[str, str]:
    """
    Convert Markdown to an HTML email string.
    
    Args:
        markdown_text: The weekly pulse in Markdown format.
        
    Returns:
        (html_body, text_body) tuple.
    """
    # 1. Plain text fallback: Clean up Markdown symbols so it looks neat in plain text
    text_body = markdown_text.replace("**", "").replace("*   ", "- ").replace("* ", "- ").strip()
    
    # 2. Convert to HTML using the 'markdown' package
    try:
        html_snippet = markdown.markdown(markdown_text.strip())
    except Exception as e:
        logger.error(f"Markdown parsing failed: {e}")
        # Fallback if markdown package fails
        html_snippet = f"<pre>{text_body}</pre>"
        
    # 3. Drop into template
    html_body = _EMAIL_HTML_TEMPLATE.format(html_content=html_snippet)
    
    logger.info("Email built successfully (HTML + Text fallback).")
    return html_body, text_body
