# HaliCred – Green Credit Scoring Platform

![HaliCred Logo](./assets/logo.png) <!-- replace with actual logo path -->

### **AI-Powered Green Credit Scoring for SMEs, Farmers & Informal Workers**

HaliCred is an **AI-driven platform** that empowers small businesses, farmers, and informal workers to access affordable loans by proving their **climate-friendly practices**.

We turn **eco-actions → GreenScore → Cheaper Loans + Carbon Credits.**

---

## Why HaliCred?

Access to finance is one of the biggest barriers for small businesses in Africa. Traditional credit systems ignore climate-positive behaviors like:

- Using **solar energy** instead of diesel.  
- Practicing **sustainable farming**.  
- Switching to **biogas or clean transport**.

HaliCred solves this by assigning a **GreenScore** that reflects real environmental impact, verified through **AI + APIs + uploaded evidence**.

Banks can then use this score to **offer better loan terms**, while SMEs earn from **carbon credits**.

---

## What It Does

- ✅ **Green Credit Scoring**: Dynamic AI-based GreenScore calculated using climate APIs + user evidence.  
- ✅ **SME Portal**: Farmers, welders, salons, boda riders, etc. upload eco-evidence, apply for loans, and track carbon credits.  
- ✅ **Bank Portal**: Financial institutions review AI-verified SME profiles with risk + impact summaries.  
- ✅ **AI Assistant (Inflection Pi)**: Conversational guide answering FAQs, personalized climate tips.  
- ✅ **Carbon Credit Integration**: SMEs can view & eventually trade credits earned from reduced emissions.  
- ✅ **USSD Support**: Offline access via \*483# for rural and low-data SMEs.

---

## 💡 Real Use Cases

1. **Farmer (Agriculture)** – uploads receipt for drip irrigation → AI confirms water-saving tech → GreenScore + carbon credits → gets discounted loan.  
2. **Salon Owner (SME)** – switches to solar power → GreenScore boosts → better credit access.  
3. **Boda Rider (Transport)** – uses electric bike → lower emissions → earns carbon credits + cheaper financing for battery swap.  
4. **Welder (Informal sector)** – replaces diesel generator with solar → higher score + ESG-friendly financing.  
5. **Biogas Household SME** – reduces methane → quantified CO₂ savings → credits + loan support.

---

## 🛠 Tech Stack

### **Frontend**

- React.js (Bank Portal)  
- React Native (SME App – Web & Mobile)  
- Tailwind CSS + ShadCN UI (UI consistency & polish)  

### **Backend**

- Python (FastAPI / Flask)  
- PostgreSQL (loan & SME structured data)  
- MongoDB (evidence storage – optional)  

### **AI & APIs**

- Inflection Pi (Conversational AI Guide)  
- OpenAI GPT-4/5 (evidence reasoning + text parsing)  
- HuggingFace (BERT, YOLOv8 – NLP & image recognition)  
- Climatiq API (emissions factors)  
- Carbon Interface API (carbon footprint calculations)  
- LangChain (AI orchestration)  

### **Other**

- Africa’s Talking API (USSD support)  
- Secure Auth (JWT + 2FA)  
- Docker (deployment)

---

## User Flows

### **SME Side**

1. Register → Create profile (sector, business, eco-actions).  
2. Upload evidence (photos, receipts, documents).  
3. AI validates with Climate APIs → generates **GreenScore**.  
4. Apply for loan → AI pre-matches offers from banks.  
5. Track repayments + carbon credits.  
6. Access via web app, mobile app, or USSD (\*483#).

### **Bank Side**

1. Bank login → secure portal.  
2. View loan application queue → with SME GreenScores.  
3. Review AI breakdown (eco-actions, risks, climate impact).  
4. Approve/decline loan with confidence.  
5. ESG dashboard → view portfolio’s total climate impact.

---

## Impact

- **Climate**: Quantifies emissions reduced (tons of CO₂ saved).  
- **Finance**: Unlocks credit for millions of SMEs excluded by traditional banks.  
- **Trust**: Transparent scoring backed by AI + verified data.  
- **Inclusivity**: Supports both **high-tech mobile app users** and **offline rural SMEs via USSD**.

---

## Setup & Installation

Clone repo:

```bash
git clone https://github.com/Annfelicty/hali-cred.git
cd hali-cred


### **Backend**

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### **Frontend**

```bash
cd frontend
npm install
npm run dev
```

### **Mobile App**

```bash
cd mobile
npm install
npx expo start
```

