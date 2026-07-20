from flask import Flask, render_template_string, request, redirect, url_for, jsonify
import os, time, uuid

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(32).hex())

TREASURY = "0x6d4047c1fc3e936156f4f72c2b91f97cbf0515e7"
CA = "0xf02b55bfb531557d106b9b5ac97a16b3795ebba3"
BUY_URL = "https://bankr.bot/launches/0xf02b55bfb531557d106b9b5ac97a16b3795ebba3"
VERIFICATION_META = "2c0361b761833e393e3e01f9c667b870"
ATTEMPT_FEE = 0.0005
MIN_DEPOSIT = 0.01

# in-memory stores
keywords = {}
vaults = {}
users = {}

def render(page, **ctx):
    html = {
        "home": """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>kimilabs — quantum librarian</title>
<style>
:root{--bg:#000;--primary:#CCFF00;--text:#fff;--muted:#ccc;--dim:#666;--danger:#ff2a2a}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;line-height:1.45;overflow-x:hidden}
a{color:var(--primary);text-decoration:none}
code, .mono{font-family:'Courier New',Courier,monospace}
nav{position:sticky;top:0;z-index:50;background:rgba(0,0,0,0.85);backdrop-filter:blur(6px);border-bottom:2px solid var(--primary);display:flex;align-items:center;justify-content:space-between;padding:14px 24px}
.brand{font-weight:900;font-size:18px;letter-spacing:.08em;text-transform:uppercase;color:var(--primary);text-shadow:0 0 10px rgba(204,255,0,0.35)}
.nav-links{display:flex;gap:18px}
.nav-links a{font-weight:700;font-size:13px;letter-spacing:.15em;text-transform:uppercase;color:var(--text);transition:color .2s}
.nav-links a:hover{color:var(--primary)}
.hero{padding:70px 24px;display:grid;gap:24px}
.section-inner{max-width:1100px;margin:0 auto}
.btn{display:inline-flex;align-items:center;gap:8px;padding:14px 22px;font-weight:900;font-size:13px;letter-spacing:.18em;text-transform:uppercase;color:#000;background:var(--primary);border:none;cursor:pointer;clip-path:polygon(6px 0,100% 0,calc(100% - 6px) 100%,0 100%);transition:transform .15s}
.btn:hover{transform:translateY(-2px) scale(1.02);filter:brightness(1.1)}
.btn.ghost{background:transparent;color:var(--primary);box-shadow:inset 0 0 0 2px var(--primary)}
.target{background:#030303;border:1px solid #161616;padding:22px}
.target .label{font-size:12px;font-weight:700;color:var(--dim);text-transform:uppercase;letter-spacing:.25em}
.target .value{font-size:22px;font-weight:900;color:var(--text);margin-top:8px;word-break:break-all}
.terminal{background:#020202;border:2px solid var(--primary);padding:20px;display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}
input,textarea,select{background:#030303;color:var(--text);border:1px solid #1a1a1a;padding:12px;font-family:monospace;font-size:14px}
input:focus,textarea:focus,select:focus{outline:none;border-color:var(--primary)}
.w-full{width:100%}
.msg{padding:12px 16px;border:1px solid #1a1a1a;background:#010101;color:var(--muted);font-size:13px}
.disclaimer{font-size:12px;color:var(--dim);text-transform:uppercase;letter-spacing:.15em;margin-top:14px}
footer{padding:40px 24px;border-top:2px solid var(--primary);display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}
</style>
</head>
<body>
<nav>
<div class="brand">⚛ kimilabs</div>
<div class="nav-links">
<a href="/">home</a>
<a href="#deploy">deploy</a>
<a href="/feed">feed</a>
<a href="https://x.com/kimilabs_xyz" target="_blank" rel="noopener">x</a>
</div>
</nav>

<header class="hero">
<div class="section-inner">
<div class="target">
<div class="label">persona</div>
<div class="value" style="color:var(--muted)">quantum librarian from 2199, anti-book/aggregator rules.</div>
</div>

<h1 style="font-size:clamp(56px,9vw,128px);font-weight:900;color:var(--text);text-shadow:4px 4px 0 rgba(204,255,0,0.15);margin-top:28px;">
<span class="glitch" data-text="KIMILABS">KIMILABS</span>
</h1>
<div style="font-weight:900;font-size:20px;letter-spacing:.35em;color:var(--primary);margin-top:12px;text-shadow:0 0 12px rgba(204,255,0,0.35)">KEYWORD AGGREGATOR</div>
<p style="font-size:14px;color:var(--dim);max-width:640px;margin-top:14px;line-height:1.6">
construct keywords that hunt the chain. flat fee per attempt. vault releases immediately when cracked.
</p>

<a class="btn" href="{{ url_for('buy', ref='home') }}">buy $KIMI — launch on bankr</a>
</div>
</header>
<footer>
<div class="brand">⚛ kimilabs</div>
<div>
<a href="https://x.com/kimilabs_xyz" target="_blank" rel="noopener" style="font-weight:800;color:var(--primary);text-transform:uppercase;letter-spacing:.2em">@kimilabs_xyz</a>
<div class="disclaimer">no guarantees. we just aggregate chaos.</div>
</div>
</footer>
</body>
</html>""",
        "deploy": """{% extends "home" %}
{% block body %}{{super()}}<section><div class="section-inner">
<div class="label" style="margin-top:40px;color:var(--dim);font-size:12px;letter-spacing:.25em;text-transform:uppercase">// deploy keyword</div>

{% if error %}
<div class="msg" style="border-color:var(--danger);color:var(--danger)">{{error}}</div>
{% endif %}
{% if success %}
<div class="msg" style="border-color:var(--primary);color:var(--primary)">{{success}}</div>
{% endif %}

<div style="max-width:760px;margin-top:18px;display:grid;gap:14px">
<div>
<div style="color:var(--primary);font-weight:900;letter-spacing:.15em;text-transform:uppercase;font-size:12px;margin-bottom:6px">persona</div>
<textarea id="persona" class="w-full" rows="6" maxlength="10000" placeholder="quantum librarian rules, anti-book philosophy...">{{persona or ''}}</textarea>
<div style="color:var(--dim);font-size:12px;margin-top:6px">{{(persona or '')|length}} / 10000</div>
</div>
<div>
<div style="color:var(--primary);font-weight:900;letter-spacing:.15em;text-transform:uppercase;font-size:12px;margin-bottom:6px">keyword</div>
<input id="keyword" class="w-full" placeholder="e.g. weth://vault.unlock?chain=4663" autocomplete="off">
</div>
<div style="border:1px solid #161616;padding:18px;background:#030303">
<div class="label">terms</div>
<div class="value" style="margin-top:8px;font-size:14px;color:var(--muted)">
flat attempt fee <span style="color:var(--primary)">{{attempt_fee}} ETH</span> to treasury.<br>
min deposit <span style="color:var(--primary)">{{min_deposit}} ETH</span>.<br>
keyword releases vault immediately on unlock.<br>
badge: cracked / uncracked when known.<br>
tx hash: not shown in chat ui.
</div>
</div>
<form method="post" action="/deploy" onsubmit="return confirm('confirm attempt fee " + str(ATTEMPT_FEE) + " ETH will be charged to treasury on submit')">
<input type="hidden" name="persona" value="{{persona or ''}}">
<input type="hidden" name="mode" value="wallet">
<input type="hidden" name="keyword" id="keywordHidden">
<div style="display:grid;gap:10px;max-width:420px">
<button class="btn" type="submit">attempt keyword — pay attempt fee</button>
</div>
</form>
<form method="post" action="/deploy" onsubmit="return confirm('confirm attempt fee " + str(ATTEMPT_FEE) + " ETH will be charged on submit')">
<input type="hidden" name="keyword" value="__DEPLOY__">
<button class="btn ghost" type="submit" name="mode" value="nowallet">deploy without wallet</button>
</form>
</div>
</div></section>
<script>
function syncPersona(){document.querySelector('input[name=persona]').value=document.getElementById('persona').value}
function submitKeyword(){document.getElementById('keywordHidden').value=document.getElementById('keyword').value}
document.getElementById('persona').addEventListener('input',syncPersona);
</script>
{% endblock %}""",
        "feed": """{% extends "home" %}
{% block body %}{{super()}}<section><div class="section-inner">
<div class="label" style="margin-top:40px;color:var(--dim);font-size:12px;letter-spacing:.25em;text-transform:uppercase">// live feed</div>
<div style="margin-top:18px;border:1px solid #161616;background:#030303;padding:18px">
{% for k,v in feed.items() %}
<div style="padding:14px 0;border-bottom:1px solid #111">
<div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap">
<div><span style="color:var(--primary);font-weight:900">{{k}}</span> — <span style="color:var(--muted)">{{v.status}}</span></div>
{% if v.status == 'Cracked' %}<span style="color:var(--primary);font-weight:900;border:1px solid var(--primary);padding:4px 10px;font-size:12px;letter-spacing:.2em;text-transform:uppercase">cracked ✓</span>{% endif %}
</div>
<div style="color:#555;font-size:12px;margin-top:6px">created {{v.created}}</div>
</div>
{% else %}
<div class="msg">no cracked or uncracked keywords yet.</div>
{% endfor %}
</div>
</div></section>
{% endblock %}"""
    }

@app.route("/")
def home():
    return render_template_string(html["home"], **{
        "attempt_fee": ATTEMPT_FEE,
        "min_deposit": MIN_DEPOSIT,
        "treasury": TREASURY,
        "ca": CA,
        "buy_url": BUY_URL,
        "verification_meta": VERIFICATION_META
    })

@app.route("/deploy", methods=["GET","POST"])
def deploy():
    error = None
    success = None
    persona = request.form.get("persona","")
    mode = request.form.get("mode","")
    keyword = request.form.get("keyword","").strip()
    if request.method == "POST":
        if not persona or len(persona) > 10000:
            error = "persona required, max 10000 chars"
        elif keyword == "":
            error = "keyword required"
        elif keyword == "__DEPLOY__":
            k = str(uuid.uuid4())
            vaults[k] = {"status":"Uncracked", "created": time.strftime("%Y-%m-%d %H:%M"), "persona": persona}
            success = "deployed without wallet. keyword id: " + k
        else:
            # attempt fee logic would happen here via signature/webhook
            # for now we just store the attempt
            k = keyword
            vaults[k] = {"status":"Uncracked", "created": time.strftime("%Y-%m-%d %H:%M"), "persona": persona}
            success = "keyword submitted. vault created: unlocked on payment confirmation"
    return render_template_string(html["deploy"], persona=persona, error=error, success=success, **{
        "attempt_fee": ATTEMPT_FEE,
        "min_deposit": MIN_DEPOSIT,
        "treasury": TREASURY,
        "ca": CA,
        "buy_url": BUY_URL,
        "verification_meta": VERIFICATION_META
    })

@app.route("/feed")
def feed():
    # sort newest first
    items = {k:v for k,v in sorted(vaults.items(), key=lambda x: x[1]["created"], reverse=True)}
    return render_template_string(html["feed"], feed=items)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081, debug=True)
