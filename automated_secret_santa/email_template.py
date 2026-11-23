import html
import sys

from rich.console import Console
from string import Template


console = Console()

SUPPORTED_LANGUAGES = ("en", "fr")

# Palette
BG = "#0f0f23"
TEXT = "#b9b9c0"
ORANGE = "#ffb347"
GREEN = "#0ad228"
LIME = "#a7c957"
NAME_RED = "#bc4749"
YELLOW = "#f9e900"
BALL_RED = "#ff4c4c"
BALL_BLUE = "#735ed3"
TRUNK = "#8b5a2b"

FONT = "Garamond, 'Times New Roman', Times, serif"
MONO = "'Courier New', Courier, monospace"

# Inline styles
STYLE_H2 = (f"margin:0 0 18px 0; padding:0; font-family:{FONT}; font-size:30px; line-height:1.2; "
            f"font-weight:normal; color:{ORANGE}; text-shadow:0 0 2px {ORANGE}, 0 0 5px #ffcc33;")
STYLE_P = (f"margin:0 0 14px 0; padding:0; font-family:{FONT}; font-size:17px; line-height:1.5; "
           f"color:{TEXT}; text-align:justify;")
STYLE_NAME = f"color:{NAME_RED};"
STYLE_HIGHLIGHT = f"color:{LIME};"
STYLE_QUOTE = (f"border-left:3px solid {ORANGE}; padding:4px 0 4px 14px; font-family:{FONT}; "
               f"font-size:17px; line-height:1.5; color:{TEXT}; text-align:left;")

EMPTY_MESSAGE = {
    "fr": "(Aucun texte - voir les pièces jointes éventuelles.)",
    "en": "(No text - see the attachments, if any.)",
}


def check_language(language):
    if language not in SUPPORTED_LANGUAGES:
        console.print(f"[red] Error: Language {language} not supported. - Only 'en' and 'fr' are supported.[/red]")
        sys.exit(1)


def prepare_message(message: str) -> str:
    message = message.replace("\r\n", "\n").replace("\r", "\n")
    return html.escape(message).replace("\n", "<br>")


def create_email1(santa, santa_of, budget, language):
    check_language(language)
    santa, santa_of, budget = html.escape(santa), html.escape(santa_of), html.escape(budget)
    if language == 'fr':
        html_body = email1_template_fr(santa, santa_of, budget)
    else:
        html_body = email1_template_en(santa, santa_of, budget)

    full_html = email1_template(html_body)
    return full_html


def create_email2(santa, santa_of, message, language):
    check_language(language)
    santa, santa_of = html.escape(santa), html.escape(santa_of)
    if message.strip():
        message = prepare_message(message)
    else:
        message = html.escape(EMPTY_MESSAGE[language])
    if language == 'fr':
        html_body = email2_template_fr(santa, santa_of, message)
    else:
        html_body = email2_template_en(santa, santa_of, message)

    full_html = email2_template(html_body)
    return full_html


# HTML building blocks

def _h2(text: str) -> str:
    return f'<h2 style="{STYLE_H2}">{text}</h2>'


def _p(text: str) -> str:
    return f'<p style="{STYLE_P}">{text}</p>'


def _name(text: str) -> str:
    return f'<span style="{STYLE_NAME}">{text}</span>'


def _highlight(text: str) -> str:
    return f'<span style="{STYLE_HIGHLIGHT}">{text}</span>'


def _quote(message: str) -> str:
    return (
        '<div style="margin:0 0 14px 0;">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
        f'<td style="{STYLE_QUOTE}">{message}</td>'
        '</tr></table></div>'
    )


# Message bodies

def email1_template_fr(santa, santa_of, budget):
    return "\n".join([
        _h2(f"Ho ho ho {santa} !"),
        _p(f"Je t'ai désigné pour être le Père Noël secret de {_name(santa_of)} !"),
        _p(f"Le budget est de {_highlight(budget)}."),
        _p("Tu peux faire ta liste d'envies à ton Père Noël en répondant à cet e-mail, "
           "je me chargerai de la transmettre à la personne que j'ai désignée pour toi."),
        _p("Le Père Noël"),
    ])


def email1_template_en(santa, santa_of, budget):
    return "\n".join([
        _h2(f"Ho ho ho {santa} !"),
        _p(f"You have been chosen to be the secret Santa for {_name(santa_of)}!"),
        _p(f"The budget is {_highlight(budget)}."),
        _p("You can send your wishlist to your Santa by replying to this email, "
           "and I will make sure it reaches the person I've assigned to you."),
        _p("Santa Claus"),
    ])


def email2_template_fr(santa, santa_of, message: str) -> str:
    return "\n".join([
        _h2(f"Ho ho ho {santa} !"),
        _p(f"Tu as reçu un message de {_name(santa_of)} :"),
        _quote(message),
        _p("Le Père Noël"),
    ])


def email2_template_en(santa, santa_of, message: str) -> str:
    return "\n".join([
        _h2(f"Ho ho ho {santa} !"),
        _p(f"You have received a message from {_name(santa_of)}:"),
        _quote(message),
        _p("Santa Claus"),
    ])


# ASCII tree
TREE_ROWS = [
    "         |",
    "        -+-",
    "         A",
    "        /=\\",
    "      i/ O \\i",
    "      /=====\\",
    "      /  i  \\",
    "    i/ 0 * 0 \\i",
    "    /=========\\",
    "    /  *   *  \\",
    "  i/ O   i   O \\i",
    "  /=============\\",
    "  /  0   i   0  \\",
    "i/  *  O   O   * \\i",
    "/=================\\",
    "       |___|",
]
TREE_CHARS = {
    "*": ("star", YELLOW),
    "O": ("ball", BALL_RED),
    "0": ("ball_blue", BALL_BLUE),
    "i": ("candle", ORANGE),
}


def render_tree() -> str:
    last = len(TREE_ROWS) - 1
    lines = []
    for r, row in enumerate(TREE_ROWS):
        out = []
        for ch in row.rstrip():
            if ch == " ":
                out.append(" ")
                continue
            if r < 3:
                cls, color = "star", YELLOW
            elif r == last:
                cls, color = "trunk", TRUNK
            else:
                cls, color = TREE_CHARS.get(ch, ("tree", GREEN))
            glow = f" text-shadow:0 0 5px {color};" if cls not in ("tree", "trunk") else ""
            glyph = "O" if ch == "0" else ch
            out.append(f'<span class="{cls}" style="color:{color};{glow}">{html.escape(glyph)}</span>')
        lines.append("".join(out))
    return "\n".join(lines)


# Page shell

PAGE_TEMPLATE = Template("""<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="color-scheme" content="light only">
    <meta name="supported-color-schemes" content="light only">
    <title>Secret Santa</title>
    <!--[if mso]><style>body, table, td, h2, p, pre { font-family: 'Times New Roman', serif !important; }</style><![endif]-->
    <style data-premailer="ignore">
        :root { color-scheme: light only; supported-color-schemes: light only; }
        body { margin: 0; padding: 0; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }
        a[x-apple-data-detectors] { color: inherit !important; text-decoration: none !important; }

        /* Animated tree: only clients supporting CSS animations (Apple Mail, iOS Mail) will animate it */
        .star { animation: twinkle 1.5s infinite alternate ease-in-out; }
        .ball { animation: blink-red 2s infinite alternate ease-in-out; }
        .ball_blue { animation: blink-blue 2.5s infinite alternate ease-in-out; }
        .candle { animation: flicker 0.3s infinite alternate ease-in-out; }

        @keyframes twinkle { 0% { opacity: 0.6; } 100% { opacity: 1; text-shadow: 0 0 10px #fff700, 0 0 20px #f9e900; } }
        @keyframes blink-red { 0% { opacity: 0.5; } 100% { opacity: 1; text-shadow: 0 0 8px #ff4c4c, 0 0 15px rgba(255,76,76,0.8); } }
        @keyframes blink-blue { 0% { opacity: 0.5; } 100% { opacity: 1; text-shadow: 0 0 8px #735ed3, 0 0 15px rgba(115,94,211,0.8); } }
        @keyframes flicker { 0% { opacity: 0.8; } 100% { opacity: 1; text-shadow: 0 0 6px #ffd966, 0 0 14px #ffb347; } }
    </style>
</head>
<body style="margin:0; padding:0; background-color:$bg;" bgcolor="$bg">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="$bg" style="background-color:$bg;">
        <tr>
            <td align="center" style="padding:24px 16px;">
                <!--[if mso]><table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"><tr><td><![endif]-->
                <div style="max-width:600px; margin:0 auto; text-align:left;">
$inner
                </div>
                <!--[if mso]></td></tr></table><![endif]-->
            </td>
        </tr>
    </table>
</body>
</html>
""")

COLUMNS_TEMPLATE = Template("""                    <div style="font-size:0; line-height:0; text-align:left;">
                        <!--[if mso]><table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"><tr><td width="390" valign="top"><![endif]-->
                        <div style="display:inline-block; width:100%; max-width:390px; vertical-align:top;">
$text
                        </div><!--[if mso]></td><td width="210" valign="top"><![endif]--><div style="display:inline-block; width:100%; max-width:210px; vertical-align:top; text-align:center;">
                            <pre style="display:inline-block; margin:0; padding:8px 0 0 0; font-family:$mono; font-size:13px; line-height:1; text-align:left; white-space:pre;">$tree</pre>
                        </div>
                        <!--[if mso]></td></tr></table><![endif]-->
                    </div>""")


def email1_template(div_text_content: str) -> str:
    """
    HTML email template for Secret Santa assignment email (text + ASCII tree side by side).

    The ASCII art tree has been adapted from ASCII Art Archive (https://www.asciiart.eu/holiday-and-events/christmas/trees).
    """
    columns = COLUMNS_TEMPLATE.safe_substitute(text=div_text_content, tree=render_tree(), mono=MONO)
    return PAGE_TEMPLATE.safe_substitute(inner=columns, bg=BG)


def email2_template(div_text_content) -> str:
    return PAGE_TEMPLATE.safe_substitute(inner=div_text_content, bg=BG)