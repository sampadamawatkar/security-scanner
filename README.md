# AI-Powered Vulnerability Scanner

A self-hosted security scanning tool that runs network scans against a target, sends the raw results to a local LLM for analysis, and displays a structured, human-readable vulnerability report through a web dashboard.

## What it does

1. A user enters a target IP through the dashboard
2. The backend runs an `nmap` scan against that target
3. The raw scan output is sent to a locally running LLM (Ollama)
4. The model returns a structured report: summary, open ports, risk ranking, and recommended fixes
5. The report is displayed back on the dashboard

All analysis runs locally — no data leaves the network, no paid API required.

## Architecture

```
┌────────────────┐        nmap scan        ┌──────────────────────┐
│  Kali Linux    │ ───────────────────────▶ │  CentOS               │
│  (scanner +    │                           │  Target: OWASP        │
│   FastAPI)     │ ◀─────────────────────── │  Juice Shop (Docker)  │
└───────┬────────┘        scan result        └──────────────────────┘
        │
        │  raw scan text
        ▼
┌────────────────┐
│  Ollama (LLM)  │   runs on the host machine, called over the network
│  llama3.2      │
└───────┬────────┘
        │  structured report
        ▼
┌────────────────┐
│  Web Dashboard │   browser UI, calls the FastAPI backend
└────────────────┘
```

CentOS also runs Jenkins with Docker enabled, in preparation for CI/CD automation of the build and deploy process.

## Tech stack

- **Scanning:** nmap
- **Backend:** Python, FastAPI
- **AI analysis:** Ollama (llama3.2), running locally — no cloud API
- **Frontend:** HTML/CSS/JavaScript dashboard
- **Target environment:** OWASP Juice Shop (intentionally vulnerable web app), containerized with Docker
- **CI/CD (in progress):** Jenkins on CentOS

## Setup

### Prerequisites
- A machine running the scanner (nmap + Python 3 + pip)
- A target machine reachable over the network, with Docker installed to run Juice Shop
- Ollama installed and reachable over the network from the scanner machine

### 1. Run the target
On the target machine:
```bash
docker run -d -p 3000:3000 --name juice-shop bkimminich/juice-shop
```

### 2. Run Ollama
On the machine hosting the LLM:
```bash
ollama pull llama3.2
```
Make sure Ollama is reachable from the scanner machine (bind it to `0.0.0.0` instead of `localhost` if they're on different hosts).

### 3. Run the backend
On the scanner machine:
```bash
pip3 install fastapi uvicorn requests --break-system-packages
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Update the `OLLAMA_HOST` value at the top of `main.py` to point to wherever Ollama is running.

### 4. Open the dashboard
Open `dashboard.html` in a browser (on the scanner machine, or any machine that can reach the backend). Enter a target IP and click **Run scan**.

## Project structure

```
security-scanner/
├── main.py          # FastAPI backend: runs nmap, calls Ollama, returns report
├── dashboard.html    # Browser-based UI for triggering scans and viewing reports
└── README.md
```

## Notes on this setup

- The target used here (OWASP Juice Shop) is an intentionally vulnerable application built for security training — no real systems were scanned.
- Due to hardware constraints (Apple Silicon, which can't run x86 virtual machines), the target and CI/CD server were co-located on a single VM rather than fully isolated across separate hosts, as would be typical in a production security lab.

## Future improvements

- Containerize the backend and dashboard with Docker
- Automate build/deploy through the Jenkins pipeline already configured
- Add authentication before exposing the dashboard beyond a local network
- Support additional scan types (nikto, dirb) alongside nmap
## Author
Sampada Manwatkar
