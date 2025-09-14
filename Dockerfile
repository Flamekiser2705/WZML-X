FROM mysterysd/wzmlx:latest

WORKDIR /usr/src/app
RUN chmod 777 /usr/src/app

COPY requirements.txt .
RUN pip3 install --upgrade setuptools wheel
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

# Set Python path to include current directory
ENV PYTHONPATH="/usr/src/app:$PYTHONPATH"

# Ensure scripts have proper permissions
RUN chmod +x start.sh aria.sh

CMD ["bash", "start.sh"]
