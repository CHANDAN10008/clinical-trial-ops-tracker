FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml requirements.txt ./
COPY src ./src
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py ./
COPY docs ./docs
COPY sql ./sql
COPY .streamlit ./.streamlit
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
