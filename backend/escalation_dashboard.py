from flask import Flask, render_template_string

from src.escalation_db import get_all_escalations


app = Flask(__name__)


HTML = """
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>Anisha - Human Help Requests</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f5f7fb;
            color: #1f2937;
        }

        .container {
            max-width: 1100px;
            margin: 0 auto;
            padding: 40px 20px;
        }

        .header {
            margin-bottom: 30px;
        }

        .header h1 {
            margin: 0 0 8px;
            font-size: 32px;
        }

        .header p {
            margin: 0;
            color: #6b7280;
        }

        .card {
            background: white;
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
        }

        .top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 20px;
            margin-bottom: 20px;
        }

        .reference {
            font-size: 20px;
            font-weight: bold;
        }

        .status {
            background: #dcfce7;
            color: #166534;
            padding: 6px 14px;
            border-radius: 999px;
            font-size: 13px;
            font-weight: bold;
            text-transform: uppercase;
        }

        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }

        .field {
            background: #f9fafb;
            padding: 14px;
            border-radius: 10px;
        }

        .label {
            display: block;
            font-size: 12px;
            font-weight: bold;
            color: #6b7280;
            text-transform: uppercase;
            margin-bottom: 6px;
        }

        .value {
            font-size: 15px;
            line-height: 1.5;
        }

        .empty {
            background: white;
            padding: 40px;
            text-align: center;
            border-radius: 16px;
            color: #6b7280;
        }

        @media (max-width: 700px) {
            .grid {
                grid-template-columns: 1fr;
            }

            .top {
                flex-direction: column;
                align-items: flex-start;
            }
        }
    </style>
</head>

<body>

<div class="container">

    <div class="header">
        <h1>🤝 Anisha Human Help Requests</h1>
        <p>Learning & Literacy escalation dashboard</p>
    </div>

    {% if requests %}

        {% for request in requests %}

        <div class="card">

            <div class="top">

                <div class="reference">
                    {{ request.reference_id }}
                </div>

                <div class="status">
                    {{ request.status }}
                </div>

            </div>

            <div class="grid">

                <div class="field">
                    <span class="label">Who needs help</span>
                    <div class="value">
                        {{ request.who_needs_help }}
                    </div>
                </div>

                <div class="field">
                    <span class="label">Urgency</span>
                    <div class="value">
                        {{ request.urgency }}
                    </div>
                </div>

                <div class="field">
                    <span class="label">Problem</span>
                    <div class="value">
                        {{ request.problem }}
                    </div>
                </div>

                <div class="field">
                    <span class="label">Language</span>
                    <div class="value">
                        {{ request.language }}
                    </div>
                </div>

                <div class="field">
                    <span class="label">Already checked</span>
                    <div class="value">
                        {{ request.already_checked }}
                    </div>
                </div>

                <div class="field">
                    <span class="label">Preferred follow-up</span>
                    <div class="value">
                        {{ request.preferred_followup }}
                    </div>
                </div>

                <div class="field">
                    <span class="label">Created</span>
                    <div class="value">
                        {{ request.created_at }}
                    </div>
                </div>

            </div>

        </div>

        {% endfor %}

    {% else %}

        <div class="empty">
            No human-help requests yet.
        </div>

    {% endif %}

</div>

</body>
</html>
"""


@app.route("/")
def dashboard():
    requests = get_all_escalations()

    return render_template_string(
        HTML,
        requests=requests,
    )


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )