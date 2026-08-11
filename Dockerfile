FROM gex-base-streamlit:latest

WORKDIR /app

# git: bắt buộc để pip cài gex-msgraph từ GitHub (không có trên PyPI — #68).
# Bỏ qua nếu image gốc đã có sẵn git (which git thành công).
RUN which git || (apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*)

# Install extra packages (one per line in requirements.txt). The base image
# already has streamlit, pandas, numpy, pydantic, plotly, sqlalchemy, psycopg2.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app.
COPY . .

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]