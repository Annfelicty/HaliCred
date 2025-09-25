from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def update_portfolio_dashboard() -> None:
    path = ROOT / "src" / "Components" / "Bank" / "PortfolioDashboard.tsx"
    text = read(path)

    text = re.sub(r"import \{ useState \} from 'react';\r?\n", "", text)
    text = re.sub(r",\s*PieChart", "", text)
    text = re.sub(r",\s*Droplets", "", text)
    text = re.sub(r",\s*Zap", "", text)
    text = re.sub(r"\s*const \[timeframe, setTimeframe\] = useState\('month'\);\r?\n", "\n", text, count=1)

    write(path, text)


def update_repayment_tracker() -> None:
    path = ROOT / "src" / "Components" / "Sme" / "RepaymentTracker.tsx"
    text = read(path)
    text = re.sub(r",\s*TrendingUp", "", text)
    write(path, text)


def update_sme_onboarding() -> None:
    path = ROOT / "src" / "Components" / "Sme" / "SMEOnboarding.tsx"
    text = read(path)
    text = re.sub(r",\s*MapPin", "", text)
    text = re.sub(r",\s*Camera", "", text)
    write(path, text)


def update_case_review() -> None:
    path = ROOT / "src" / "Components" / "Bank" / "CaseReview.tsx"
    text = read(path)
    text = re.sub(r"map\((\s*)\(action,\s*index\) =>", r"map(\1(action) =>", text)
    write(path, text)


def main() -> None:
    update_portfolio_dashboard()
    update_repayment_tracker()
    update_sme_onboarding()
    update_case_review()


if __name__ == "__main__":
    main()
