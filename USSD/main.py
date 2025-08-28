# main.py
from fastapi import FastAPI, Form
from twilio.twiml.messaging_response import MessagingResponse
from typing import Dict, Any, List
import random

app = FastAPI()


# Na tukumbuke "DB" just for demo

USER_DB: Dict[str, Dict[str, Any]] = {}
# phone -> {
#   "stage": "MENU"|"SIGNUP_NAME"|"SIGNUP_BIZ"|"CONSENT"|"UPLOAD_WAIT",
#   "name": str,
#   "business_type": str,   # farmer | salon | welder | other
#   "consent": {"mpesa":bool,"geo":bool,"receipts":bool,"telemetry":bool},
#   "evidence": List[Dict], # [{type:"receipt|photo", url:str, tags:[]}]
#   "score": int,
#   "explain": List[str],   # explanation bullets
#   "loan": str,
# }

DEMO_TIPS = {
    "farmer": "🌱 Add/expand drip irrigation for +7 pts.",
    "welder": "⚡ Upgrade more tools to inverter welders for +5–8 pts.",
    "salon":  "💡 Replace remaining dryers with efficient models for +6 pts.",
    "other":  "🔧 Switch to energy-efficient equipment and LED lighting (+4–8 pts)."
}

def menu_text():
    return (
        "👋 *HaliCred Bot* 🌱\n"
        "Choose an option:\n"
        "1️⃣ Sign Up\n"
        "2️⃣ Give Consent\n"
        "3️⃣ Upload Proof (photo/receipt)\n"
        "4️⃣ Check GreenScore\n"
        "5️⃣ Loan Offer\n"
        "6️⃣ Tips to Improve\n"
        "Type a number any time, or type *menu*."
    )

def ensure_user(phone: str):
    if phone not in USER_DB:
        USER_DB[phone] = {
            "stage": "MENU",
            "name": None,
            "business_type": None,
            "consent": {"mpesa": False, "geo": False, "receipts": True, "telemetry": False},
            "evidence": [],
            "score": None,
            "explain": [],
            "loan": None,
        }
    return USER_DB[phone]


# Core scoring + quote (mock)

def compute_green_score(user: Dict[str, Any]) -> None:
    """
    We look at business type + number of evidences + random nudge.
    Also attaches a friendly explanation.
    """
    base_by_biz = {"farmer": 60, "welder": 55, "salon": 52, "other": 50}
    base = base_by_biz.get((user["business_type"] or "other").lower(), 50)

    # proof-based bumps
    bumps = 0
    expl = []
    for ev in user["evidence"]:
        if "drip" in ev.get("tags", []) or "solar" in ev.get("tags", []):
            bumps += 10
            expl.append("Verified clean tech purchase (+10).")
        else:
            bumps += 5
            expl.append("Eco-action receipt accepted (+5).")

    # consent signals (they matter in real system)
    if user["consent"]["mpesa"]:
        bumps += 3
        expl.append("Financial data sharing enabled (+3).")
    if user["consent"]["geo"]:
        bumps += 2
        expl.append("Location verification enabled (+2).")
    if user["consent"]["telemetry"]:
        bumps += 3
        expl.append("Telemetry sharing enabled (+3).")

    # small randomization for demo feel
    bumps += random.randint(0, 3)

    score = max(40, min(95, base + bumps))
    user["score"] = score

    # attach one domain-specific tip
    tip = DEMO_TIPS.get((user["business_type"] or "other").lower(), DEMO_TIPS["other"])
    user["explain"] = expl + [f"Tip: {tip}"]

def map_loan_offer(score: int) -> str:
    """
    Simple tiering that mirrors the doc idea: higher score → better discount.
    """
    if score is None:
        return "No loan quote yet. Check your GreenScore first."
    if score >= 80:
        return "KES 200,000 @ *3.0%* green discount"
    if score >= 70:
        return "KES 150,000 @ *2.5%* green discount"
    if score >= 60:
        return "KES 100,000 @ *1.5%* green discount"
    return "KES 50,000 @ *0.5%* green discount (improve score for better rates)"


# WhatsApp webhook

@app.post("/whatsapp")
async def whatsapp(
    From: str = Form(...),
    Body: str = Form(""),
    NumMedia: str = Form("0"),
    MediaUrl0: str = Form(None),
):
    phone = From
    user = ensure_user(phone)
    msg_in = (Body or "").strip().lower()
    twiml = MessagingResponse()
    reply = twiml.message()

    # Shortcuts
    if msg_in in ["hi", "hello", "hey", "menu", "start"]:
        user["stage"] = "MENU"
        reply.body(menu_text())
        return str(twiml)

    # ---------- Numbered actions ----------
    if msg_in == "1":  # Sign Up
        user["stage"] = "SIGNUP_NAME"
        reply.body("📱 Great! What’s your *name*?")
        return str(twiml)

    if user["stage"] == "SIGNUP_NAME" and msg_in:
        user["name"] = Body.strip()
        user["stage"] = "SIGNUP_BIZ"
        reply.body("🧑‍💼 Thanks, *{}*! What’s your *business type*? (farmer / welder / salon / other)".format(user["name"]))
        return str(twiml)

    if user["stage"] == "SIGNUP_BIZ" and msg_in:
        bt = msg_in.split()[0]
        user["business_type"] = bt if bt in ["farmer", "welder", "salon", "other"] else "other"
        user["stage"] = "MENU"
        reply.body("✅ Signed up as *{}*.\n\n{}".format(user["business_type"], menu_text()))
        return str(twiml)

    if msg_in == "2":  # Consent
        user["stage"] = "CONSENT"
        reply.body(
            "🔐 Consent settings (reply with a line like: mpesa yes, geo no, telemetry yes)\n"
            f"Current → mpesa: {user['consent']['mpesa']}, geo: {user['consent']['geo']}, receipts: {user['consent']['receipts']}, telemetry: {user['consent']['telemetry']}"
        )
        return str(twiml)

    if user["stage"] == "CONSENT" and msg_in:
        # crude parse; look for yes/no for each key
        text = msg_in.replace(",", " ")
        for key in ["mpesa", "geo", "receipts", "telemetry"]:
            if f"{key} yes" in text:
                user["consent"][key] = True
            if f"{key} no" in text:
                user["consent"][key] = False
        user["stage"] = "MENU"
        reply.body("✅ Consent saved.\n\n{}".format(menu_text()))
        return str(twiml)

    if msg_in == "3":  # Upload Proof
        # If image present right now, handle; else prompt
        if NumMedia != "0" and MediaUrl0:
            # naive tag inference for demo
            tags = []
            # users can also type words like "solar", "drip" with the photo
            text = (Body or "").lower()
            if "solar" in text:
                tags.append("solar")
            if "drip" in text:
                tags.append("drip")

            user["evidence"].append({"type": "photo", "url": MediaUrl0, "tags": tags})
            # auto-score on new evidence
            compute_green_score(user)
            user["loan"] = map_loan_offer(user["score"])

            explain = "\n".join([f"• {e}" for e in user["explain"]])
            reply.body(
                "✅ Proof received!\n"
                f"📊 *GreenScore:* {user['score']}\n"
                f"💬 Why: \n{explain}\n\n"
                f"💰 *Loan Offer:* {user['loan']}\n\nType *menu* for options."
            )
            return str(twiml)
        else:
            user["stage"] = "UPLOAD_WAIT"
            reply.body("📸 Please send a *photo/receipt* now (you can add words like 'solar' or 'drip' in the caption).")
            return str(twiml)

    if user["stage"] == "UPLOAD_WAIT":
        if NumMedia != "0" and MediaUrl0:
            tags = []
            text = (Body or "").lower()
            if "solar" in text:
                tags.append("solar")
            if "drip" in text:
                tags.append("drip")
            user["evidence"].append({"type": "photo", "url": MediaUrl0, "tags": tags})
            compute_green_score(user)
            user["loan"] = map_loan_offer(user["score"])
            explain = "\n".join([f"• {e}" for e in user["explain"]])
            reply.body(
                "✅ Proof received!\n"
                f"📊 *GreenScore:* {user['score']}\n"
                f"💬 Why: \n{explain}\n\n"
                f"💰 *Loan Offer:* {user['loan']}\n\nType *menu* for options."
            )
            user["stage"] = "MENU"
            return str(twiml)
        else:
            reply.body("📸 Still waiting—please send a *photo/receipt*.")
            return str(twiml)

    if msg_in == "4":  # Check GreenScore
        if user["score"] is None:
            # compute something light even without evidence for demo
            compute_green_score(user)
        explain = "\n".join([f"• {e}" for e in user["explain"]]) or "• Take eco-actions and upload proof to boost your score."
        reply.body(f"📊 *GreenScore:* {user['score']}\n💬 Why:\n{explain}\n\nType *menu* for options.")
        return str(twiml)

    if msg_in == "5":  # Loan Offer
        if user["score"] is None:
            compute_green_score(user)
        user["loan"] = map_loan_offer(user["score"])
        reply.body(f"💰 *Loan Offer:* {user['loan']}\n(Based on GreenScore {user['score']})\n\nType *menu* for options.")
        return str(twiml)

    if msg_in == "6":  # Tips
        bt = (user["business_type"] or "other").lower()
        tip = DEMO_TIPS.get(bt, DEMO_TIPS["other"])
        reply.body(f"{tip}\n\nTry option *3* to upload proof and increase your score.")
        return str(twiml)

    # fallback
    reply.body("🤖 I didn’t get that.\n\n" + menu_text())
    return str(twiml)
