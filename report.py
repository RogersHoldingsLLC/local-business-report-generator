import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

CONFIG_FILE = Path("rogers_os_config.json")


def fetch_website(website):
    try:
        return requests.get(website, timeout=10)
    except requests.RequestException:
        return None


def analyze_website(website):
    response = fetch_website(website)

    results = {
        "reachable": "No",
        "https": "Yes" if website.startswith("https://") else "No",
        "title": "Not Found",
        "meta_description": "Not Found",
        "phone_found": "No",
        "email_found": "No",
        "contact_language": "No",
        "service_language": "No",
    }

    if response is None:
        return results

    results["reachable"] = "Yes"

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" ", strip=True).lower()

    if soup.title and soup.title.string:
        results["title"] = soup.title.string.strip()

    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        results["meta_description"] = meta.get("content").strip()

    if re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", response.text):
        results["phone_found"] = "Yes"

    if re.search(r"[\w\.-]+@[\w\.-]+\.\w+", response.text):
        results["email_found"] = "Yes"

    if any(word in text for word in ["contact", "call", "schedule", "quote", "appointment"]):
        results["contact_language"] = "Yes"

    if any(word in text for word in ["services", "service", "what we do", "solutions"]):
        results["service_language"] = "Yes"

    return results


def calculate_score(results):
    score = 0

    if results["reachable"] == "Yes":
        score += 20
    if results["https"] == "Yes":
        score += 15
    if results["title"] != "Not Found":
        score += 15
    if results["meta_description"] != "Not Found":
        score += 15
    if results["phone_found"] == "Yes":
        score += 10
    if results["email_found"] == "Yes":
        score += 10
    if results["contact_language"] == "Yes":
        score += 10
    if results["service_language"] == "Yes":
        score += 5

    return score


def score_rating(score):
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Strong"
    if score >= 60:
        return "Average"
    if score >= 40:
        return "Needs Improvement"
    return "Critical"


def opportunity_rating(score):
    if score >= 90:
        return "LOW OPPORTUNITY"
    if score >= 75:
        return "MODERATE OPPORTUNITY"
    if score >= 60:
        return "GOOD OPPORTUNITY"
    return "HIGH OPPORTUNITY"


def priority_tier(score):
    if score < 60:
        return "High"
    if score < 75:
        return "Medium"
    return "Low"


def offer_service(results, score):
    if results["phone_found"] == "No" or results["contact_language"] == "No":
        return "Website conversion optimization"
    if results["title"] == "Not Found" or results["meta_description"] == "Not Found":
        return "SEO basics cleanup"
    if results["https"] == "No" or results["reachable"] == "No":
        return "Technical website cleanup"
    if score < 75:
        return "Local digital optimization"
    return "Conversion and local visibility review"


def next_action(score):
    if score < 60:
        return "Send audit summary and recommend a website optimization consultation."
    if score < 75:
        return "Send audit summary and recommend practical quick-win improvements."
    return "Send audit summary and offer a conversion and local visibility review."


def follow_up_date():
    return (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")


def load_rogers_os_config():
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Missing configuration file: {CONFIG_FILE}")

    with open(CONFIG_FILE) as file:
        config = json.load(file)

    web_app_url = str(config.get("web_app_url", "")).strip()
    api_key = str(config.get("api_key", "")).strip()

    if not web_app_url or web_app_url.startswith("PASTE_"):
        raise ValueError("Rogers Holdings OS Web App URL is not configured.")
    if not api_key or api_key.startswith("PASTE_"):
        raise ValueError("Rogers Holdings OS API key is not configured.")

    return web_app_url, api_key


def send_to_rogers_os(audit):
    web_app_url, api_key = load_rogers_os_config()
    separator = "&" if "?" in web_app_url else "?"
    url = f"{web_app_url}{separator}{urlencode({'apiKey': api_key})}"

    response = requests.post(url, json=build_rogers_os_payload(audit), timeout=20)
    response.raise_for_status()

    result = response.json()
    if not result.get("ok"):
        raise RuntimeError(result.get("error", "Rogers Holdings OS rejected the audit."))

    return result


def build_rogers_os_payload(audit):
    return {
        "company": audit["company"],
        "website": audit["website"],
        "auditScore": audit["auditScore"],
        "auditOutcome": audit["auditOutcome"],
        "priorityTier": audit["priorityTier"],
        "recommendedService": audit["recommendedService"],
        "notes": audit["notes"],
        "followUpDate": audit["followUpDate"],
        "nextAction": audit["nextAction"],
    }


def generate_recommendations(results):
    recommendations = []

    if results["reachable"] == "No":
        recommendations.append("Confirm the website is live and loading correctly.")
    if results["https"] == "No":
        recommendations.append("Add HTTPS/SSL security to improve trust.")
    if results["title"] == "Not Found":
        recommendations.append("Add a clear page title with the business name and main service.")
    if results["meta_description"] == "Not Found":
        recommendations.append("Add a meta description for better search visibility.")
    if results["phone_found"] == "No":
        recommendations.append("Make the phone number easy to find.")
    if results["email_found"] == "No":
        recommendations.append("Add a visible email address or contact form.")
    if results["contact_language"] == "No":
        recommendations.append("Add clear calls-to-action like Call, Schedule, or Request a Quote.")
    if results["service_language"] == "No":
        recommendations.append("Clearly list the services offered.")

    if not recommendations:
        recommendations.append("Website fundamentals look strong. Review design, speed, conversion flow, and Google Business Profile next.")

    return recommendations


def generate_sales_talking_points(results, score, opportunity):
    points = []

    if results["meta_description"] == "Not Found":
        points.append("Website is missing a meta description.")
    if results["email_found"] == "No":
        points.append("No visible email address was detected.")
    if results["phone_found"] == "No":
        points.append("A phone number was not detected.")
    if results["contact_language"] == "No":
        points.append("Calls-to-action could be improved.")
    if results["service_language"] == "No":
        points.append("Services are not clearly communicated.")
    if score < 60:
        points.append("This business may be a strong Rogers Holdings prospect.")
    if score >= 75:
        points.append("Website has solid fundamentals, but conversion and local visibility may still be improved.")

    points.append(f"Opportunity rating: {opportunity}")

    return points


def run_audit(business, website, location):
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    safe_name = "".join(c for c in business if c.isalnum() or c in (" ", "_")).replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = reports_dir / f"{safe_name}_Report_{timestamp}.txt"

    website_results = analyze_website(website)
    score = calculate_score(website_results)
    rating = score_rating(score)
    opportunity = opportunity_rating(score)
    tier = priority_tier(score)
    service = offer_service(website_results, score)
    action = next_action(score)
    follow_up = follow_up_date()

    recommendations = generate_recommendations(website_results)
    sales_points = generate_sales_talking_points(website_results, score, opportunity)

    recommendation_text = "\n".join(f"{i + 1}. {item}" for i, item in enumerate(recommendations))
    sales_points_text = "\n".join(f"• {item}" for item in sales_points)

    report = f"""
==================================================
ROGERS HOLDINGS LLC
LOCAL BUSINESS DIGITAL OPTIMIZATION REPORT
==================================================

BUSINESS INFORMATION
--------------------------------------------------
Business Name : {business}
Website       : {website}
Location      : {location}
Generated     : {datetime.now().strftime("%B %d, %Y %I:%M %p")}

==================================================
WEBSITE OPTIMIZATION SCORE
==================================================
Score       : {score}/100
Rating      : {rating}
Opportunity : {opportunity}

==================================================
AUTOMATED WEBSITE CHECKS
==================================================
Website Reachable        : {website_results["reachable"]}
HTTPS Enabled            : {website_results["https"]}
Page Title               : {website_results["title"]}
Meta Description         : {website_results["meta_description"]}
Phone Number Found       : {website_results["phone_found"]}
Email Address Found      : {website_results["email_found"]}
Contact Language Found   : {website_results["contact_language"]}
Service Language Found   : {website_results["service_language"]}

==================================================
INTELLIGENT RECOMMENDATIONS
==================================================
{recommendation_text}

==================================================
SALES TALKING POINTS
==================================================
{sales_points_text}

==================================================
MANUAL WEBSITE AUDIT
==================================================
[ ] Mobile Friendly
[ ] Clear Call-To-Action
[ ] Contact Information Easy To Find
[ ] Services Clearly Listed
[ ] Trust Signals Present
[ ] Fast Load Speed
[ ] Strong Homepage Message

==================================================
GOOGLE BUSINESS PROFILE REVIEW
==================================================
[ ] Reviews Reviewed
[ ] Photos Reviewed
[ ] Categories Reviewed
[ ] Hours Verified
[ ] Services Verified

==================================================
ROGERS HOLDINGS LLC SUMMARY
==================================================
This report was generated by Rogers Holdings LLC to identify
digital optimization opportunities for local businesses.

A higher score means stronger digital fundamentals.
A lower score means there may be clearer opportunities to improve visibility,
trust, and customer conversion.
==================================================
"""

    with open(file_path, "w") as file:
        file.write(report)

    notes = " ".join(recommendations)
    summary = (
        f"{business} scored {score}/100 with an audit outcome of {opportunity}. "
        f"Recommended service: {service}."
    )

    return {
        "company": business,
        "website": website,
        "auditScore": score,
        "auditOutcome": opportunity,
        "priorityTier": tier,
        "offerService": service,
        "recommendedService": service,
        "notes": notes,
        "summary": summary,
        "followUpDate": follow_up,
        "nextAction": action,
        "reportPath": str(file_path),
        "reportFileName": file_path.name,
        "reportText": report,
        "rating": rating,
    }


def create_report(business, website, location):
    result = run_audit(business, website, location)

    print("\n✅ Report successfully created:")
    print(result["reportPath"])
    print(f"\nWebsite Optimization Score: {result['auditScore']}/100 - {result['rating']}")
    print(f"Opportunity Rating: {result['auditOutcome']}")

    send_choice = input("\nSend to Rogers Holdings OS? [y/N]: ").strip().lower()
    if send_choice in ("y", "yes"):
        try:
            send_to_rogers_os(result)
            print("Prospect successfully added to Rogers Holdings OS")
        except Exception as error:
            print(f"Error sending prospect to Rogers Holdings OS: {error}")

    return result


def main():
    if len(sys.argv) != 4:
        print('\nUsage: python3 report.py "Business Name" "Website URL" "City, State"\n')
        sys.exit(1)

    create_report(sys.argv[1], sys.argv[2], sys.argv[3])


if __name__ == "__main__":
    main()
