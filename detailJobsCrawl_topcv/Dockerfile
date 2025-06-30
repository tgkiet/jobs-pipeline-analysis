FROM python:3.12-slim

# Cài thư viện hệ thống cần cho Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    fonts-liberation \
    libnss3 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libxss1 \
    libasound2 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libatspi2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    --no-install-recommends

# Add Google signing key and repo, cài Google Chrome
RUN wget -qO - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
 && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
 && apt-get update \
 && apt-get install -y google-chrome-stable --no-install-recommends \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Làm việc ở /app
WORKDIR /app

# Sao chép requirements và cài packages (cài dưới root để toàn hệ thống xài được)
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade pip \
 && python -m pip install --no-cache-dir -r requirements.txt

# Sao chép source code
COPY . .

RUN useradd -ms /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

ENV HOME=/tmp
CMD ["python", "listPageScraper.py"]

