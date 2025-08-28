# HaliCred

## Setting Up the Backend Environment

Follow these steps to install the dependencies and set up the backend environment before beginning development:

### Prerequisites
Ensure you have the following installed on your system:
- Python 3.10 or higher
- pip (Python package manager)
- Virtual environment tool (e.g., `venv` or `virtualenv`)

### Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/bjeptum/GreenScore.git
   cd GreenScore/backend/app
   ```

2. **Create and Activate a Virtual Environment**
   On Windows:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
   On macOS/Linux:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**
   With the virtual environment activated, install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify Installation**
   Ensure all dependencies are installed correctly:
   ```bash
   pip list
   ```

### Next Steps
- Configure environment variables using a `.env` file or HashiCorp Vault.
- Set up the database and run migrations.
- Start the development server using Uvicorn.

Refer to the documentation in the `docs/` folder for more details on project setup and workflows.
