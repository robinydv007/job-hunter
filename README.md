# Job Hunter Agent

**AI-powered job search automation for Indian job platforms.**

Job Hunter automates the tedious task of searching for and shortlisting jobs on platforms like Naukri. It uses Playwright for browser automation and LangGraph to structure the AI decision-making process, scoring jobs against your resume and exporting a ranked shortlist to CSV.

## Features

- **Automated Job Search** — Browser automation queries job boards based on your profile
- **Smart Resume Parsing** — Extracts skills, target roles, and experience from PDF, DOCX, or TXT using LLMs
- **Intelligent Job Scoring** — Scores jobs against your profile using a weighted 6-factor rubric
- **Auto-Apply** — Applies to jobs above your threshold directly through the platform's API
- **CSV Export** — Outputs ranked jobs to a ready-to-view CSV file
- **Caching** — Caches parsed profiles and search results for faster subsequent runs

## Supported Platforms

- Naukri.com

## Technology Stack

- **Python:** >= 3.12
- **Agent Workflow:** LangGraph, LangChain Core
- **LLMs:** OpenAI, Groq
- **Browser Automation:** Playwright
- **Data:** Pydantic, aiosqlite, PyYAML
- **CLI:** Click, Rich

## Installation

We recommend using [uv](https://docs.astral.sh/uv/) for fast, reproducible dependency management.

```bash
# Clone the repository
git clone https://github.com/yourusername/job-hunter.git
cd job-hunter

# Create virtual environment
uv venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

# Install dependencies
uv pip install -e .

# Install Playwright browsers
playwright install
```

## Configuration

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env`** and add your API keys:
   ```
   GROQ_API_KEY=your_groq_api_key   # Get at https://console.groq.com
   OPENAI_API_KEY=your_openai_api_key  # Optional fallback
   NAUKRI_EMAIL=your_naukri_email
   NAUKRI_PASSWORD=your_naukri_password
   ```

3. **Initialize the project:**
   ```bash
   job-hunter init
   ```

4. **Edit `config/user.yaml`** with your search preferences:
   ```yaml
   profile:
     name: Your Name
     total_experience: 5
     preferred_roles:
       - software engineer
     resume_path: resume.pdf
     expected_salary_lpa: 20
     notice_period: immediate

   search:
     platforms:
       - naukri
     salary_min_lpa: 15
     salary_max_lpa: 30
     max_jobs: 20

   scoring:
     shortlist_threshold: 30
   ```

## Usage

```bash
# Run with your resume
job-hunter run --resume resume.pdf

# Run in headless mode (not recommended for first login)
job-hunter run --resume resume.pdf --headless

# Check status
job-hunter status
```

## Commands

| Command | Description |
|---------|-------------|
| `job-hunter init` | Initialize config and directories |
| `job-hunter run` | Run the full pipeline |
| `job-hunter status` | Show cached data and outputs |
| `job-hunter clean` | Clear cached files |

## Disclaimer

- This tool is for personal use only. Respect the terms of service of the job platforms you use.
- Use responsibly and at your own risk. Excessive automation may lead to account restrictions.
- The authors are not responsible for any account bans or restrictions.

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

Licensed under the MIT License. See [LICENSE](LICENSE) for details.