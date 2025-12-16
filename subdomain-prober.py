#!/usr/bin/env python3
"""
Sub-Pro — Subdomain Prober

Enumerate subdomains (subfinder) → probe (httpx) → save TXT artifacts
→ export Excel from PROBED output with columns:
[Sno, Subdomain Name, Status Code, Technology]

Console output (per domain):
- Big banner via pyfiglet: "Sub-Pro" + subtitle "Subdomain Prober"
- One vertical, BOXED table showing:
  Domain
  Total Domains Found
  Probed Domains
  Filtered Domains
  Excel Path

Requires binaries in PATH: subfinder, httpx
Python deps: pandas, openpyxl, tabulate, pyfiglet
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
import pyfiglet
from termcolor import colored

from typing import Dict, Iterable, List, Sequence, Set

import pandas as pd
from tabulate import tabulate

LOG = logging.getLogger("sub_pro")

ANSI_RE = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
BRACKET_RE = re.compile(r'\[([^\]]+)\]')


# ---------------- Utilities ----------------

def setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=(logging.DEBUG if verbose else logging.WARNING),  # quiet by default
        format="%(asctime)s | %(levelname)-8s | %(message)s",
    )

def which_or_die(bin_name: str) -> str:
    path = shutil.which(bin_name)
    if not path:
        LOG.error(f"Required binary not found in PATH: {bin_name}")
        sys.exit(2)
    return path

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def write_lines(path: str, lines: Iterable[str]) -> None:
    ensure_dir(os.path.dirname(path) or ".")
    with open(path, "w", encoding="utf-8") as f:
        for ln in lines:
            f.write(ln.rstrip("\n") + "\n")

def run_subprocess(cmd: Sequence[str], input_text: str = "", timeout: int = 0) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            cmd,
            input=(input_text or None),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=(timeout or None),
        )
    except subprocess.TimeoutExpired as e:
        return subprocess.CompletedProcess(cmd, returncode=124, stdout="", stderr=str(e))

def strip_ansi(s: str) -> str:
    return ANSI_RE.sub("", s)

def domain_folder_name(domain: str) -> str:
    d = domain.strip().lower()
    parts = [p for p in d.split(".") if p]
    if len(parts) >= 2:
        parts = parts[:-1]  # drop TLD for folder name
    name = "-".join(parts) if parts else d
    name = re.sub(r"[^a-z0-9\-_]", "-", name)
    name = re.sub(r"-{2,}", "-", name).strip("-")
    return name or "domain"

def chunked(seq: Sequence[str], size: int) -> Iterable[List[str]]:
    for i in range(0, len(seq), size):
        yield seq[i:i+size]


# ---------------- Tool wrappers ----------------

def subfinder_domains(subfinder_bin: str, domain: str, threads: int, timeout: int) -> List[str]:
    cmd = [subfinder_bin, "-silent", "-d", domain]
    if threads > 0:
        cmd += ["-t", str(threads)]
    cp = run_subprocess(cmd, timeout=timeout)
    return sorted(set([ln.strip() for ln in cp.stdout.splitlines() if ln.strip()]))

def httpx_probe(httpx_bin: str, hosts: Sequence[str], threads: int,
                batch_size: int, timeout: int) -> List[str]:
    if not hosts:
        return []
    all_out: List[str] = []
    # avoid huge stdin hangs by batching
    for i in range(0, len(hosts), batch_size):
        batch = hosts[i:i+batch_size]
        input_text = "\n".join(batch) + "\n"
        cmd = [httpx_bin, "-silent", "-tech-detect", "-status-code"]
        if threads > 0:
            cmd += ["-threads", str(threads)]
        # ask tools to avoid colors; we still strip ANSI anyway
        env = dict(os.environ); env = env  # (kept for clarity; not used with run_subprocess)
        cp = run_subprocess(cmd, input_text=input_text, timeout=timeout)
        all_out.extend([ln.strip() for ln in cp.stdout.splitlines() if ln.strip()])
    return all_out


# ---------------- Parsing ----------------

@dataclass
class ProbedRow:
    url: str
    status: str
    tech: str

def parse_httpx_line(line: str) -> ProbedRow:
    clean = strip_ansi(line)
    parts = clean.split()
    url = parts[0] if parts else clean.strip()
    status = ""
    tech_tokens: List[str] = []
    for tok in BRACKET_RE.findall(clean):
        if tok.isdigit() and not status:
            status = tok
        else:
            tech_tokens.append(tok.strip())
    return ProbedRow(url=url, status=status, tech=", ".join(tech_tokens).strip(", "))

def filter_by_status(lines: Sequence[str], statuses: Set[str]) -> List[str]:
    return [ln for ln in lines if parse_httpx_line(ln).status in statuses]


# ---------------- Excel export ----------------

def write_probed_excel(probed_lines: Sequence[str], xlsx_path: str) -> None:
    rows = []
    for i, ln in enumerate(probed_lines, start=1):
        r = parse_httpx_line(ln)
        rows.append({
            "Sno": i,
            "Subdomain Name": r.url,
            "Status Code": r.status,
            "Technology": r.tech,
        })
    df = pd.DataFrame(rows, columns=["Sno", "Subdomain Name", "Status Code", "Technology"])
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="probed")


# ---------------- Pipeline ----------------

@dataclass
class DomainCounts:
    domain: str
    found: int
    probed: int
    filtered: int
    excel_path: str

def process_domain(domain: str, outdir: str, statuses: Set[str],
                   subfinder_bin: str, httpx_bin: str,
                   threads: int, batch_size: int, timeout: int) -> DomainCounts:
    folder = domain_folder_name(domain)
    d_out = os.path.join(outdir, folder)
    ensure_dir(d_out)

    subs = subfinder_domains(subfinder_bin, domain, threads, timeout)
    write_lines(os.path.join(d_out, f"{domain}-all.txt"), subs)

    probed = httpx_probe(httpx_bin, subs, threads, batch_size, timeout)
    write_lines(os.path.join(d_out, f"{domain}-probed.txt"), probed)

    filtered = filter_by_status(probed, statuses)
    write_lines(os.path.join(d_out, f"{domain}-filtered.txt"), filtered)

    xlsx = os.path.join(d_out, f"{domain}-probed.xlsx")
    write_probed_excel(probed, xlsx)

    return DomainCounts(domain, len(subs), len(probed), len(filtered), os.path.abspath(xlsx))


# ---------------- CLI ----------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sub-Pro — Subdomain Prober")
    p.add_argument("domains", nargs="+", help="One or more root domains (e.g., example.com test.com)")
    p.add_argument("--outdir", default=".", help="Base directory for outputs")
    p.add_argument("--status", default="200,301,401,403", help="Comma-separated status codes for filtered.txt")
    p.add_argument("--threads", type=int, default=0, help="Threads for subfinder/httpx (0 = tool default)")
    p.add_argument("--httpx-batch-size", type=int, default=500, help="Hosts per httpx invocation (default: 500)")
    p.add_argument("--timeout", type=int, default=0, help="Per-process timeout seconds (0 = none)")
    p.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    return p.parse_args()

def main() -> None:
    args = parse_args()
    setup_logging(args.verbose)

    # Banner
    ascii_banner = pyfiglet.figlet_format("Sub - Pro")
    print(colored(ascii_banner, "cyan"))
    print(colored("   Subdomain Prober v1.0.0", "green"))
    print(colored("   Author: Saurabh Jain", "yellow"))
    subfinder_bin = which_or_die("subfinder")
    httpx_bin = which_or_die("httpx")
    ensure_dir(args.outdir)

    statuses = {s.strip() for s in args.status.split(",") if s.strip().isdigit()}

    for domain in args.domains:
        c = process_domain(
            domain=domain,
            outdir=args.outdir,
            statuses=statuses,
            subfinder_bin=subfinder_bin,
            httpx_bin=httpx_bin,
            threads=args.threads,
            batch_size=args.httpx_batch_size,
            timeout=args.timeout,
        )

        # Boxed (grid) vertical table per domain
        rows = [
            ["Domain", c.domain],
            ["Total Domains Found", c.found],
            ["Probed Domains", c.probed],
            ["Filtered Domains", c.filtered],
            ["Excel Path", c.excel_path],
        ]
        print(tabulate(rows, tablefmt="grid"))
        print()  # blank line between domains

if __name__ == "__main__":
    main()

