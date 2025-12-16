# Sub-Pro — Subdomain Prober

Sub-Pro is a Python-based automation tool that helps in **subdomain reconnaissance and validation**.  
It discovers subdomains for given root domains, probes which ones are live, identifies HTTP status codes and technologies, and exports the results into **text files and an Excel report**.

This tool is useful for:
- VAPT / security assessments
- Bug bounty reconnaissance
- Attack surface discovery
- Asset inventory and monitoring

---

## Features

- Subdomain enumeration using **subfinder**
- Live host probing using **httpx**
- HTTP status code & technology detection
- Status-based filtering (200, 301, 401, 403 by default)
- Clean TXT artifacts for each stage
- Excel report generation for easy sharing
- Readable terminal summary per domain

---

## Prerequisites

### System Requirements
- Linux / macOS (recommended)
- Python **3.8 or higher**

### Required External Tools
The following binaries must be installed and available in your `$PATH`:

- **subfinder**
- **httpx**

# Install using ProjectDiscovery:

```bash
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
```

### Ensure they are accessible:

```bash
subfinder -h
httpx -h
```

## Installation Guidelines

1. Clone or copy the script

```bash
git clone <repository-url>
cd sub-pro
```

Or place subdomain-prober.py in your desired directory.

2. Install Python dependencies

```bash
pip3 install pandas openpyxl tabulate pyfiglet termcolor
```
(Optional – recommended)

```bash
pip3 install -r requirements.txt
```
3. Make the script executable (optional)

```bash
chmod +x subdomain-prober.py
```

How to Run
Basic usage
```bash
python3 subdomain-prober.py example.com
```
Scan multiple domains
```bash
python3 subdomain-prober.py example.com test.com
```

Specify output directory
```bash
python3 subdomain-prober.py example.com --outdir results
```
Run with custom status codes
```bash
python3 subdomain-prober.py example.com --status 200,302,401,403
```
Run with threading enabled
```bash

python3 subdomain-prober.py example.com --threads 50
```
Full example (recommended)
```bash

python3 subdomain-prober.py example.com \
  --outdir recon-results \
  --threads 50 \
  --status 200,301,401,403 \
  --httpx-batch-size 500
```
Verbose (debug) mode
```bash
python3 subdomain-prober.py example.com -v
```
Run as executable
```bash
./subdomain-prober.py example.com
```

### Output Structure
For each domain, a folder is created with the following files:

```python
example/
├── example.com-all.txt        # All discovered subdomains
├── example.com-probed.txt     # Live subdomains with status & tech
├── example.com-filtered.txt   # Filtered by status codes
└── example.com-probed.xlsx    # Excel report
```
### Excel Columns

* Sno
* Subdomain Name
* Status Code
* Technology

# Default Status Code Filter

By default, the script filters:
```bash
200, 301, 401, 403
```
These usually indicate:

* Live applications
* Login portals
* Redirects
* Protected endpoints

## Notes & Best Practices
This tool performs non-intrusive reconnaissance only
Use only on assets you own or are authorized to test
Large domains may take time depending on subdomain count
Internet connectivity is required for probing

## Author : Saurabh Jain

## Disclaimer
This tool is intended for educational and authorized security testing purposes only.
The author is not responsible for misuse or unauthorized scanning.

# License
MIT License



