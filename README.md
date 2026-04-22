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

4. **Edit `config/user.yaml`** with your search preferences.

## Configuration Files

This project uses several configuration files. Here's what each does:

### config/user.yaml

Main configuration file with your profile and search preferences.

```yaml
profile:
  name: Your Name
  total_experience: 5
  preferred_roles:
    - software engineer
    - full stack developer
  resume_path: resume.pdf
  expected_salary_lpa: 20
  notice_period: immediate
  remote_preference: hybrid  # remote, hybrid, or onsite

search:
  platforms:
    - naukri
  salary_min_lpa: 15
  salary_max_lpa: 30
  max_jobs: 50           # 0 = no limit
  max_jobs_per_query: 20
  max_roles: 5           # number of search queries to generate
  max_locations: 3
  excluded_companies: []  # company names to skip
  excluded_keywords: []   # keywords in job title to skip
  delay_min_seconds: 3.0   # anti-blocking: random delay between actions
  delay_max_seconds: 8.0

naukri:
  login_required: true
  headless: false         # NOT recommended - triggers bot detection
  page_timeout: 30000
  max_pages: 3           # pages to scrape per query
  delay_between_pages: 3

scoring:
  shortlist_threshold: 30  # jobs below this won't be listed
  apply_threshold: 30      # jobs below this won't be auto-applied
  skill_weight: 0.35       # most important!
  role_weight: 0.2
  experience_weight: 0.2
  company_weight: 0.1
  location_weight: 0.08
  work_mode_weight: 0.07

auto_apply:
  enabled: true
  max_per_day: 10
  max_per_run: 5
  delay_between_seconds: 5
  require_confirmation: false  # true = prompts before each apply
  skip_if_already_applied: true
```

### config/screening.yaml

Answers to common screening questions asked during applications.

```yaml
screening_answers:
  willing_to_relocate: true
  comfortable_with_shifts: false
  current_ctc_lpa: 15
  expected_ctc_lpa: 20
  notice_period: immediate
  reason_for_change: Looking for better growth opportunities
  remote_work_preference: flexible

screening_answers_extended:
  # Optional longer answers:
  # reason_for_change: |
  #   Detailed reason here...
  # strengths: |
  #   Your key strengths...
```

### config/constants.yaml

Domain knowledge used by the scoring engine. You can tune these without touching code:

- **skill_aliases** — Alternative names for skills (e.g., "node" = "node.js")
- **company_rating_bands** — Score boosts based on company ratings
- **experience_penalties** — Score reductions for over/under-qualified roles
- **metro_cities** — City name variations for location matching

## Commands

### job-hunter init

Initialize the project. Creates `config/user.yaml` and `data/`/`output/` directories.

```bash
job-hunter init
```

### job-hunter run

Run the full pipeline. Options:

| Option | Short | Description |
|--------|-------|-------------|
| `--resume` | `-r` | Path to resume file (PDF, DOCX, or TXT) |
| `--config` | `-c` | Path to config YAML file |
| `--headless` | | Run browser in headless mode (not recommended) |
| `--force-parse` | | Force re-parse resume even if cached |

```bash
# Basic usage
job-hunter run --resume resume.pdf

# With custom config
job-hunter run --resume resume.pdf --config custom.yaml

# Force re-parse cached resume
job-hunter run --force-parse
```

### job-hunter status

Show cached profile data and recent CSV exports.

```bash
job-hunter status
```

### job-hunter clean

Clear all cached data (parsed profile, detailed profile, resume hash).

```bash
job-hunter clean
```

## Tips for Better Results

1. **Use non-headless mode** — Running headless triggers bot detection on Naukri. Always run with a visible browser for the first few runs.

2. **Set accurate preferred_roles** — The scoring engine weights role matching at 20%. Use exact titles like "Software Engineer" not "Software".

3. **Tune scoring weights** — Default weights work for most cases, but you can adjust:
   - Higher `skill_weight` (0.35) if skills are your priority
   - Higher `role_weight` (0.2) if title matching matters most
   - Set `location_weight: 0` if location is flexible

4. **Configure excluded_companies/keywords** — Block companies or title keywords you don't want:
   ```yaml
   search:
     excluded_companies:
       - TCS
       - Infosys
     excluded_keywords:
       - Java    # if you don't want Java roles
       - Manager
   ```

5. **Set appropriate thresholds** — Start with lower thresholds and adjust based on results:
   ```yaml
   scoring:
     shortlist_threshold: 30   # jobs below this won't appear in CSV
     apply_threshold: 30       # jobs below this won't be auto-applied
   ```

6. **Enable LLM scoring for better matching** — For more accurate scoring using AI:
   ```yaml
   scoring:
     llm_scoring:
       enabled: true
       batch_size: 10
       shortlist_threshold: 30
       custom_requirements: |
         - For AI/ML jobs, experience can be relaxed with relevant skills.
   ```

7. **Use confirmation mode initially** — When trying auto-apply for the first time:
   ```yaml
   auto_apply:
     require_confirmation: true
   ```
   This lets you review each application before submission.

8. **Keep your resume updated** — The tool detects resume changes via hash. Use `--force-parse` if you've updated your resume.

9. **Respect rate limits** — Don't set `max_jobs` too high in a single run. Naukri may temporarily block excessive requests.

## Data & Outputs

After running, you'll find:

| Directory | Contents |
|----------|----------|
| `data/profile.json` | Cached parsed resume |
| `data/profile_detailed.yaml` | Extended profile from resume |
| `data/resume_hash.txt` | SHA256 hash for change detection |
| `output/shortlist_*.csv` | Exported job listings |

## Disclaimer

- This tool is for personal use only. Respect the terms of service of the job platforms you use.
- Use responsibly and at your own risk. Excessive automation may lead to account restrictions.
- The authors are not responsible for any account bans or restrictions.

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

Licensed under the MIT License. See [LICENSE](LICENSE) for details.