FROM python:3.11-slim

RUN apt-get update && apt-get install -y     curl     ca-certificates     unzip     && rm -rf /var/lib/apt/lists/*

# Install subfinder
RUN curl -s https://api.github.com/repos/projectdiscovery/subfinder/releases/latest     | grep browser_download_url     | grep linux_amd64     | cut -d '"' -f 4     | xargs curl -L -o subfinder.zip     && unzip subfinder.zip     && mv subfinder /usr/local/bin/     && rm -f subfinder.zip

# Install httpx
RUN curl -s https://api.github.com/repos/projectdiscovery/httpx/releases/latest     | grep browser_download_url     | grep linux_amd64     | cut -d '"' -f 4     | xargs curl -L -o httpx.zip     && unzip httpx.zip     && mv httpx /usr/local/bin/     && rm -f httpx.zip

WORKDIR /app

COPY subprober.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python3", "subdomain-prober.py"]
