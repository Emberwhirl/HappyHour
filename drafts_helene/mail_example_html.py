
from html import escape


def build_email(vocab: list[tuple[str, str]], today_str: str) -> tuple[str, str]:
    """Return (subject, html_body)."""

    # Questions: numbered French words, answers hidden below.
    questions = ""
    for i, (french, _english) in enumerate(vocab, start=1):
        questions += f"""
            <tr>
              <td style="padding:14px 18px;border-bottom:1px solid #dde7f0;
                         font-size:15px;color:#4a6a8e;font-weight:bold;width:36px;
                         vertical-align:top;">{i}.</td>
              <td style="padding:14px 18px;border-bottom:1px solid #dde7f0;
                         font-size:17px;font-weight:bold;color:#0d2340;
                         font-family:Georgia,serif;">{escape(french)}</td>
            </tr>"""

    # Answers: numbered English translations, in a lighter panel below.
    answers = ""
    for i, (_french, english) in enumerate(vocab, start=1):
        answers += f"""
            <tr>
              <td style="padding:8px 18px;font-size:13px;color:#3b7fb5;
                         font-weight:bold;width:36px;                         vertical-align:top;">{i}.</td>
              <td style="padding:8px 18px;font-size:14px;color:#2a4a6e;
                         font-family:Georgia,serif;">{escape(english)}</td>
            </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:24px;background:#eef4fa;font-family:Georgia,serif;">
  <div style="max-width:600px;margin:0 auto;background:#ffffff;
              border-radius:12px;overflow:hidden;
              box-shadow:0 6px 20px rgba(20,50,120,0.18);">

    <!-- Deep-ocean blue gradient header -->
    <div style="background:#1e5b9e;
                background:linear-gradient(180deg,#A5D6E5 0%,#3B7FB5 45%,#0D2340 100%);
                padding:36px 28px;">
      <div style="font-size:11px;letter-spacing:3px;color:#e8f3fb;
                  text-transform:uppercase;margin-bottom:6px;">
        Révision hebdomadaire
      </div>
      <h1 style="margin:0;color:#ffffff;font-size:26px;letter-spacing:0.5px;
                 text-shadow:0 1px 3px rgba(10,25,60,0.35);">
        Quiz de Vocabulaire
      </h1>
      <p style="margin:10px 0 0;color:#d6e8f5;font-size:13px;">{escape(today_str)}</p>
    </div>

    <!-- Intro -->
    <div style="padding:22px 28px 4px;">
      <p style="color:#4a5b7a;font-size:14px;margin:0 0 4px;line-height:1.5;">
        Testez vos connaissances avec ces <strong>{len(vocab)} mots</strong>
        déjà vus du <em>Comte de Monte-Cristo</em> de Dumas.
      </p>
      <p style="color:#8a9bb5;font-size:12px;margin:6px 0 0;font-style:italic;">
        Essayez de les traduire avant de regarder les réponses.
      </p>
    </div>

    <!-- Questions -->
    <div style="padding:16px 20px 0;">
      <div style="font-size:12px;letter-spacing:2px;color:#1e5b9e;
                  text-transform:uppercase;font-weight:bold;
                  padding:0 8px 8px;border-bottom:2px solid #A5D6E5;">
        Questions
      </div>
      <table style="width:100%;border-collapse:collapse;margin-top:4px;">
        <tbody>{questions}
        </tbody>
      </table>
    </div>

    <!-- Divider -->
    <div style="text-align:center;padding:24px 28px 8px;">
      <span style="display:inline-block;font-size:11px;letter-spacing:4px;
                   color:#6a8bb5;padding:0 12px;">
        ▾ &nbsp; RÉPONSES &nbsp; ▾
      </span>
    </div>

    <!-- Answers -->
    <div style="padding:0 20px 20px;">
      <div style="background:#eef6fc;border-radius:8px;padding:14px 4px;">
        <table style="width:100%;border-collapse:collapse;">
          <tbody>{answers}
          </tbody>
        </table>
      </div>
    </div>

    <!-- Footer -->
    <div style="padding:16px 28px 24px;text-align:center;
                border-top:1px solid #dde7f0;">
      <p style="color:#7a90b0;font-size:12px;margin:0;letter-spacing:1px;">
        Bonne chance avec la révision !
      </p>
    </div>
  </div>
</body>
</html>"""

    subject = f"Quiz de vocabulaire — {today_str}"
    return subject, html
