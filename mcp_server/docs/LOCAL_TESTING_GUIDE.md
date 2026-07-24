# Local Testing Guide for PM Tool MCP Server

This guide provides end-to-end instructions for setting up, running, and functionally testing the PM Tool MCP Server via a User Interface (the MCP Inspector). It is designed for senior developers to review and validate the integration before connecting it to Hey Tam.

---

## 1. Prerequisites

Before you begin, ensure you have the following installed on your local machine:
*   **Python 3.11+**
*   **Node.js (v18+) & npm/npx** (Required for the MCP Inspector UI)
*   **PostgreSQL** (or whichever database your local PM Tool backend uses)
*   A running instance of the **PM Tool Frontend** (optional, but helpful for generating a valid test token)

---

## 2. Setting Up the Backend & Generating a Token

Because the MCP Server acts as an HTTP Proxy to your existing FastAPI backend, the backend must be running, and you need a valid user token.

### Step 2.1: Start the FastAPI Backend
1. Open a terminal and navigate to the backend root:
   ```bash
   cd c:/Users/kandp/Desktop/KK/Projects/PMTool/proj-mgmt-backend
   ```
2. Activate your virtual environment and install backend dependencies:
   ```bash
   # (Activate your venv here)
   pip install -r requirements.txt
   ```
3. Start the backend server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   *Ensure the backend is running at `http://127.0.0.1:8000`.*

### Step 2.2: Get a Valid JWT Token
To allow the MCP Server to authenticate its proxy requests, you need a valid Bearer token.
1. Log into your local **Next.js Frontend** (`http://localhost:3000`).
2. Open your browser's Developer Tools (F12) -> Application/Storage tab -> Local Storage (or Network tab).
3. Copy your current user's `access_token` (the long JWT string).
4. *Alternatively*, use Postman/Swagger UI (`http://127.0.0.1:8000/docs`) to log in and copy the token.

---

## 3. Configuring the MCP Server

Now, configure the MCP Server to communicate with your local backend.

### Step 3.1: Install MCP Dependencies
1. Open a **new** terminal window and navigate to the MCP server directory:
   ```bash
   cd c:/Users/kandp/Desktop/KK/Projects/PMTool/proj-mgmt-backend/mcp_server
   ```
2. Install the required MCP packages:
   ```bash
   pip install -r requirements.txt
   ```

### Step 3.2: Set Up Environment Variables
1. Rename `.env.example` to `.env` (or just edit the existing `.env`).
2. Update the `PMTOOL_API_BASE_URL` to point to your local host:
   ```env
   PMTOOL_API_BASE_URL=http://127.0.0.1:8000/api/v1
   ```
3. **Crucial for Inspector UI**: Change the transport to `stdio` in your `.env`:
   ```env
   MCP_TRANSPORT=stdio
   ```
   *(The Inspector communicates via Standard I/O, not HTTP).*

### Step 3.3: Inject the Test Token
For local testing (before the dynamic Hey Tam OAuth flow is fully wired), we will hardcode the token you retrieved in Step 2.2.
1. Open `mcp_server/api_client.py`.
2. Scroll to the bottom to the `get_client()` function.
3. Replace the placeholder with your actual JWT token:
   ```python
   def get_client() -> PMToolAPIClient:
       # PASTE YOUR REAL TOKEN HERE FOR LOCAL TESTING
       token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." 
       return PMToolAPIClient(token=token)
   ```

### Step 3.4: Temporarily Disable OAuth Requirement (For Local UI Testing)
The MCP Inspector UI uses STDIO transport and does not natively perform an OAuth 2.1 PKCE login flow. To test the tools seamlessly in the UI:
1. Open `mcp_server/server.py`.
2. Comment out the `auth_provider` line:
   ```python
   mcp = FastMCP(
       name="PMTool",
       instructions="...",
       # auth_provider="oauth2",  <-- COMMENT THIS OUT FOR LOCAL UI TESTING
   )
   ```

---

## 4. UI-Wise Functional Testing (MCP Inspector)

We will use the **official MCP Inspector**, an interactive web UI that connects to your server and allows you to test every tool and resource visually.

### Step 4.1: Launch the Inspector
You must run the inspector from the **parent directory** (`proj-mgmt-backend`) so Python can resolve the `mcp_server` package imports correctly.

In a terminal window, navigate to the backend root and run the following command using `npx`:
```bash
cd c:/Users/kandp/Desktop/KK/Projects/PMTool/proj-mgmt-backend
npx @modelcontextprotocol/inspector python -m mcp_server.server
```
*Note: This command spins up a local React app and connects it to your `server.py` script over STDIO.*

### Step 4.2: Access the UI
1. The terminal will output a localhost URL (usually `http://localhost:5173`).
2. Open this URL in your web browser. 
3. Click the **Connect** button in the top right corner of the UI.

### Step 4.3: Execute Functional Tests
You should now see a sidebar listing all 48 tools (e.g., `list_projects`, `create_task`, `get_analytics_summary`) and resources.

#### Test 1: Read Operations
1. Click on the **`list_projects`** tool in the left sidebar.
2. Leave parameters blank and click **Run Tool**.
3. **Expected Result**: The UI should display a JSON array of all projects currently in your local PostgreSQL database.

#### Test 2: Write Operations (Create Task)
1. Copy a valid `project_id` from the output of Test 1.
2. Click on the **`create_task`** tool.
3. Fill in the required parameters in the UI form:
   *   `project_id`: (paste the ID)
   *   `title`: "MCP UI Test Task"
   *   `priority`: "HIGH"
4. Click **Run Tool**.
5. **Expected Result**: The UI should display the newly created task object with a generated `task_code`.

#### Test 3: Resource Data Fetching
1. Navigate to the **Resources** tab in the Inspector UI.
2. Select `pmtool://analytics/summary`.
3. Click **Fetch**.
4. **Expected Result**: The UI should display system-wide analytics (total users, active tasks, etc.).

#### Test 4: Verify in PM Tool Frontend
1. Go back to your running Next.js Frontend (`http://localhost:3000`).
2. Navigate to the project you used in Test 2.
3. **Expected Result**: The "MCP UI Test Task" should be visibly present on the Kanban board or task list, proving that the MCP Server successfully proxied the request to the backend and mutated the database.

---

## 5. Post-Testing Cleanup (Prep for Integration)

Once the senior developer has completed the UI-wise testing and approved the functional flows:

1. **Revert Transport**: In your `.env` file, change `MCP_TRANSPORT=stdio` back to `MCP_TRANSPORT=http` so it's ready for Hey Tam.
2. **Re-enable OAuth**: In `mcp_server/server.py`, uncomment the `auth_provider="oauth2"` line.
3. **Remove Hardcoded Token**: In `mcp_server/api_client.py`, remove your personal JWT token and prepare the `get_client()` function to extract the token dynamically from the FastMCP request context as outlined in `HEY_TAM_INTEGRATION.md`.
4. **Commit Code**: The `mcp_server` directory is now ready to be deployed alongside the FastAPI backend for the Hey Tam integration!
