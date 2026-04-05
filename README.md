# Job Hunter Agent

**Agentic AI job hunter for Indian job platforms.**

Job Hunter Automates the tedious task of searching for and shortlisting jobs. Utilizing Playwright for reliable browser automation and LangGraph to structure the AI decision-making process, this tool targets platforms like Naukri to identify the best job matches based on your resume.

## Features

- **Automated Job Search:** Drives browser interactions using Playwright to query job boards.
- **Platform Specific:** Tailored primarily for Indian job platforms such as Naukri.
- **Smart Resume Parsing:** Automatically extracts skills, targets roles, and experience from PDF, DOCX, or TXT formats using LLMs to form a strong search baseline.
- **Job Scoring & Shortlisting:** Evaluates job descriptions intelligently against the active profile.
- **CSV Export:** Outputs processed jobs smoothly to ready-to-view CSV format.
- **Local SQLite Cache:** Caches outputs effectively keeping previous runs and states intact.

## Technology Stack

- **Core:** Python >= 3.12
- **Agent Workflow:** LangGraph, LangChain Core
- **LLMs:** OpenAI, Groq
- **Browser Automation:** Playwright
- **Data & Structure:** Pydantic, aiosqlite, PyYAML
- **CLI Utilities:** Click, Rich

## Installation & Setup

We recommend using [uv](https://docs.astral.sh/uv/) for fast, reproducible dependency management.

1. **Clone the repository and enter the directory:**
   ```bash
   git clone <repository-url>
   cd job-hunter-repo
   ```

2. **Setup virtual environment and install dependencies:**
   ```bash
   uv venv
   # Depending on your terminal, activate virtual environment:
   # Windows: .venv\Scripts\activate
   # macOS/Linux: source .venv/bin/activate
   
   uv pip install -e .
   ```

3. **Install Browser Dependencies for Playwright:**
   ```bash
   playwright install
   ```

4. **Environment Variables:**
   Copy the example environment file and fill in your details (e.g., API keys for OpenAI/Groq or Naukri credentials if defined):
   ```bash
   cp .env.example .env
   ```

## Usage Structure

The project comes with a fully functioning command-line interface.

### Initialization

Initialize the required directories and basic configurations:
```bash
job-hunter init
```
This generates the initial `config/user.yaml` config along with internal `data/` and `output/` folders. Proceed to edit `config/user.yaml` based on your search requirements.

### Running the Pipeline

Ensure you have a resume stored in the active directory, or explicitly pass a path. 

```bash
# Example running with an explicit resume file
job-hunter run --resume path/to/my_resume.pdf

# Using a specific config or headless mode (Headless omitted is safer for Naukri logins)
job-hunter run --resume my_resume.pdf --config config/user.yaml --headless
```

### Checking Status

Verify output status, parsed cached profile structures, and recent CSV exports:
```bash
job-hunter status
```

## Contributing / Development Architecture

This project is integrated within an **Autonomous Spec-driven Development (SDD)** workflow.

- Check `specs/status.md` first before starting any active development work.
- Agent constraints and workflow are managed in `CLAUDE.md`.
- Changes must strictly adhere to the enforced `.opencode` protocols where tasks, specs, changelogs, and branch guidelines are constantly synced directly into the GitHub pre-commits. 
