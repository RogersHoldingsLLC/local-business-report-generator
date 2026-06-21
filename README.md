# Local Business Report Generator

Canonical Website Audit Tool project for Rogers Holdings LLC.

This project supports:

- CLI report generation
- customer-facing printable report creation
- optional "Send to Rogers Holdings OS" prospect sync
- local API access for Rogers Holdings OS through `WEBSITE_AUDIT_TOOL_URL`

## Installation

Install dependencies:

```bash
pip3 install -r requirements.txt
```

## CLI Usage

Run the existing printable/customer-facing report workflow:

```bash
python3 report.py "Business Name" "https://example.com" "City, State"
```

The report is written to `reports/`.

After report creation, the CLI asks:

```text
Send to Rogers Holdings OS? [y/N]:
```

Enter `y` to send the audit as a prospect to Rogers Holdings OS. Enter or type `n` to skip sending.

## Rogers Holdings OS Send Support

Configure `rogers_os_config.json`:

```json
{
  "web_app_url": "https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec",
  "api_key": "YOUR_ROGERS_OS_API_KEY"
}
```

The API key must match the key configured in the Rogers Holdings OS Apps Script Web App.

### Testing Rogers Holdings OS Integration

1. Configure `rogers_os_config.json`.
2. Run:

```bash
python3 report.py "Test Company" "https://example.com" "Test City, ST"
```

3. Enter `y` at the send prompt.
4. Confirm this success notification:

```text
Prospect successfully added to Rogers Holdings OS
```

5. Confirm Rogers Holdings OS has the prospect row, activity feed entry, and updated dashboard metrics.

## Website Audit Tool API

The API exposes the existing `report.py` audit engine so Rogers Holdings OS can call it through `WEBSITE_AUDIT_TOOL_URL`.

It does not replace the CLI workflow and does not modify Rogers Holdings OS.

### Running The API Locally

Start the API:

```bash
python3 audit_api.py
```

Default URL:

```text
http://127.0.0.1:8080
```

You can override the host and port:

```bash
WEBSITE_AUDIT_HOST=0.0.0.0 WEBSITE_AUDIT_PORT=8080 python3 audit_api.py
```

### Health Check

```bash
curl -s "http://127.0.0.1:8080/health"
```

Expected response:

```json
{
  "ok": true,
  "service": "Website Audit Tool API"
}
```

### Testing The API With curl

```bash
curl -s -X POST "http://127.0.0.1:8080/audit" \
  -H "Content-Type: application/json" \
  -d '{
    "company": "Test Company",
    "website": "https://example.com",
    "city": "Test City, ST"
  }'
```

Successful responses use this shape:

```json
{
  "success": true,
  "company": "Test Company",
  "website": "https://example.com",
  "auditScore": 35,
  "auditOutcome": "HIGH OPPORTUNITY",
  "priorityTier": "High",
  "offerService": "Website conversion optimization",
  "notes": "...",
  "summary": "...",
  "reportPath": "reports/Test_Company_Report_..."
}
```

The API preserves report creation. Each successful `/audit` request creates a customer-facing report in `reports/`.

### Audit Package Request

Rogers Holdings OS can request a full audit package by adding `requestType`, `includeReport`, and `formats`:

```bash
curl -s -X POST "http://127.0.0.1:8080/audit" \
  -H "Content-Type: application/json" \
  -d '{
    "company": "Test Company",
    "website": "https://example.com",
    "city": "Test City, ST",
    "requestType": "auditPackage",
    "includeReport": true,
    "formats": ["pdf", "txt"]
  }'
```

Successful audit package responses include the normal audit fields plus a `report` object:

```json
{
  "success": true,
  "company": "Test Company",
  "website": "https://example.com",
  "auditScore": 35,
  "auditOutcome": "HIGH OPPORTUNITY",
  "priorityTier": "High",
  "offerService": "Website conversion optimization",
  "notes": "...",
  "summary": "...",
  "reportPath": "reports/Test_Company_Report_...",
  "report": {
    "fileName": "Test_Company_Report_20260621_120000.txt",
    "reportText": "FULL CUSTOMER REPORT CONTENT"
  }
}
```

If PDF generation is added later, the audit package response can also include:

```json
{
  "pdfBase64": "..."
}
```

The current implementation supports TXT report packaging. It does not return `pdfBase64` because PDF generation is not currently implemented.

## Render Deployment

Render is the simplest deployment target for this Flask-style API.

### 1. Push To GitHub

Commit and push this project to:

```text
RogersHoldingsLLC/local-business-report-generator
```

### 2. Create Render Web Service

1. Go to Render.
2. Create a new `Web Service`.
3. Connect the GitHub repository.
4. Select the branch to deploy.
5. Use Python runtime.

### 3. Set Build And Start Commands

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
gunicorn audit_api:app
```

The included `render.yaml` also defines:

```yaml
startCommand: gunicorn audit_api:app
healthCheckPath: /health
```

### 4. Environment Variable Notes

Render provides `PORT` automatically. No required environment variables are needed for the public API.

Optional local-only environment variables:

```text
WEBSITE_AUDIT_HOST
WEBSITE_AUDIT_PORT
```

### 5. Test Render /health

After deployment, open:

```text
https://YOUR-RENDER-SERVICE.onrender.com/health
```

Expected response:

```json
{
  "ok": true,
  "service": "Website Audit Tool API"
}
```

### 6. Test Render /audit

```bash
curl -s -X POST "https://YOUR-RENDER-SERVICE.onrender.com/audit" \
  -H "Content-Type: application/json" \
  -d '{
    "company": "Test Company",
    "website": "https://example.com",
    "city": "Test City, ST"
  }'
```

### 7. Set WEBSITE_AUDIT_TOOL_URL In Rogers Holdings OS

Use the public `/audit` URL:

```text
https://YOUR-RENDER-SERVICE.onrender.com/audit
```

### Setting WEBSITE_AUDIT_TOOL_URL In Apps Script

In Rogers Holdings OS Apps Script, set the Website Audit Tool URL as a Script Property:

```javascript
function setWebsiteAuditToolUrl() {
  PropertiesService
    .getScriptProperties()
    .setProperty('WEBSITE_AUDIT_TOOL_URL', 'https://YOUR-RENDER-SERVICE.onrender.com/audit');
}
```

For local development only, use:

```javascript
function setLocalWebsiteAuditToolUrl() {
  PropertiesService
    .getScriptProperties()
    .setProperty('WEBSITE_AUDIT_TOOL_URL', 'http://127.0.0.1:8080/audit');
}
```
