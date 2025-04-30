FROM python:3.11-slim

# Install system dependencies for MoviePy, ffmpeg, and fonts
# Added gcc, python3-dev and build-essential for psutil
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    fonts-liberation \
    imagemagick \
    python3-fontforge \
    gcc \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Fix ImageMagick policy to allow font loading and other operations
RUN sed -i 's/<policy domain="path" rights="none" pattern="@\*"/<policy domain="path" rights="read | write" pattern="@\*"/g' /etc/ImageMagick-6/policy.xml && \
    sed -i 's/<policy domain="coder" rights="none" pattern="TTF"/<policy domain="coder" rights="read | write" pattern="TTF"/g' /etc/ImageMagick-6/policy.xml && \
    sed -i 's/<policy domain="coder" rights="none" pattern="PDF"/<policy domain="coder" rights="read" pattern="PDF"/g' /etc/ImageMagick-6/policy.xml && \
    sed -i 's/<policy domain="coder" rights="none" pattern="LABEL"/<policy domain="coder" rights="read | write" pattern="LABEL"/g' /etc/ImageMagick-6/policy.xml

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy all custom fonts and register them
COPY app/media/fonts/*.ttf /usr/share/fonts/truetype/
RUN fc-cache -f -v

# Explicitly install Wand (Python ImageMagick binding) which MoviePy might use
RUN pip install --no-cache-dir Wand

# Set up fonts properly - using the directory structure approach
RUN mkdir -p /tmp/font_setup
COPY app/media/fonts/*.ttf /tmp/font_setup/
RUN cd /tmp/font_setup && \
    for font in *.ttf; do \
        font_name="${font%.ttf}"; \
        mkdir -p "/usr/share/fonts/truetype/$font_name"; \
        cp "$font" "/usr/share/fonts/truetype/$font_name/"; \
    done && \
    # Also copy fonts to application directory for direct path access
    mkdir -p /app/app/media/fonts && \
    cp -r /tmp/font_setup/* /app/app/media/fonts/ && \
    fc-cache -f -v && \
    rm -rf /tmp/font_setup

# Create MoviePy configuration file with ImageMagick path
RUN mkdir -p /root/.moviepy && \
    echo "[MoviePy]\nIMAGEMAGICK_BINARY = $(which convert)" > /root/.moviepy/moviepy.conf

# Environment setup
ENV PYTHONPATH=/
ENV PYTHONUNBUFFERED=1
ENV MAX_WORKERS=8
ENV CACHE_TTL=600

# Volume for persistent output
VOLUME ["/app/app/media/output"]

# Run the application with proper host binding for container environment
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]