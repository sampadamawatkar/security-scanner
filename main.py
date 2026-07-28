"""
AI-Powered Vulnerability Scanner Backend
Runs on Kali Linux. Triggers nmap scans and sends results to a local
Ollama instance (running on the Mac host) for AI-generated analysis.
"""

import subprocess
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="AI Security Scanner")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- Configuration ---
# IP of the Mac host running Ollama (found via `ifconfig` on Mac).
# Update this if your Mac's IP on the VMware NAT network changes.
OLLAMA_HOST = "http://192.168.141.1:11434"
OLLAMA_MODEL = "llama3.2"


class ScanRequest(BaseModel):
    target: str  # IP address or hostname to scan


def run_nmap(target: str) -> str:
    """Runs an nmap version-detection scan against the target and
    returns the raw text output."""
    try:
        result = subprocess.run(
            ["nmap", "-sV", target],
            capture_output=True,
            text=True,
            timeout=180,
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Scan timed out")
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="nmap not found. Install it with: sudo apt install nmap",
        )


def analyze_with_ollama(scan_output: str) -> str:
    """Sends the raw nmap output to Ollama and asks for a structured
    security analysis in plain English."""
    prompt = f"""You are a security analyst. Analyze this nmap scan output
and produce a concise report with these sections:
1. Summary (2-3 sentences)
2. Open ports and what they mean
3. Potential risks (ranked: high/medium/low)
4. Recommended fixes

Nmap output:
{scan_output}
"""

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        return response.json().get("response", "No response from model")
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=502,
            detail=f"Could not reach Ollama at {OLLAMA_HOST}. "
            "Check that Ollama is running on the Mac and reachable from Kali.",
        )
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Ollama analysis timed out")


@app.get("/")
def root():
    return {"status": "Security scanner API is running"}


@app.post("/scan")
def scan(request: ScanRequest):
    """Runs an nmap scan against the target and returns an AI-generated
    security report."""
    raw_output = run_nmap(request.target)

    if not raw_output.strip():
        raise HTTPException(status_code=500, detail="Empty scan output — check target reachability")

    ai_report = analyze_with_ollama(raw_output)

    return {
        "target": request.target,
        "raw_scan": raw_output,
        "ai_report": ai_report,
    }
