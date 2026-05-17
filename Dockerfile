FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    unixodbc \
    unixodbc-dev \
    freetds-dev \
    freetds-bin \
    tdsodbc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# إيجاد المسار الصح وتسجيل FreeTDS
RUN TDSODBC=$(find / -name "libtdsodbc.so" 2>/dev/null | head -1) && \
    printf "[FreeTDS]\nDescription = FreeTDS Driver\nDriver = $TDSODBC\nSetup = $TDSODBC\n" > /etc/odbcinst.ini && \
    cat /etc/odbcinst.ini

RUN printf "[global]\ntds version = 7.2\n" > /etc/freetds/freetds.conf

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY Main.py .

EXPOSE 8000

CMD ["uvicorn", "Main:app", "--host", "0.0.0.0", "--port", "8000"]