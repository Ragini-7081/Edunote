To run the **EduNote** project on your Windows machine, follow these steps:

---

### 1. Open Terminal in the Project Directory
Ensure your terminal (PowerShell or Command Prompt) is in the project root folder:
```powershell
cd <Project_location>
```

---

### 2. Install Dependencies
If you haven't installed the dependencies yet or are using a virtual environment:
```powershell
python -m pip install -r requirements.txt
```

---

### 3. Start the Application Server
Run the FastAPI application using **Uvicorn**:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

---

### 4. Open in Your Browser
Once the server starts, open your browser and navigate to:

- **Web Application**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive API Documentation (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

### Additional Notes
- To stop the server at any time, press `Ctrl + C` in the terminal.