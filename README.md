# Lab 2: Extracting Error Patterns from Application Logs Using AI

Use GitHub Copilot Chat in VS Code to summarize application activity, group and count errors, and investigate recurring failures. **Treat every AI finding as provisional until you verify it against the original log lines.**

The FastAPI demo writes live events to the terminal and `logs/application.log` when run. The activities use the fixed sample [`application.log`](application.log) at the project root, so everyone analyzes the same evidence. The workflow is: application logs → Copilot summary and investigation → developer verification against the raw lines.

## Setup

Open the `ai-log-analysis` folder in VS Code. In the integrated terminal, create and activate a virtual environment and install the dependencies.

**macOS/Linux**

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

**Windows PowerShell**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The app is optional for the analysis activities. To run it, use `python -m uvicorn main:app` and open [the API docs](http://127.0.0.1:8000/docs). Try `GET /`, `GET /health`, `GET /employees/101`, and `GET /employees/101/bonus` for normal activity. An unknown employee ID gives a 404, and `POST /demo/database-error` returns an intentional 503.

Each call to `GET /demo-log-errors` returns 200 and appends nine simulated errors, three warnings, and one INFO entry to the live log. The timestamps reflect when the endpoint runs, not the fixed sample's timeline. No real database or payment service is called.

## Activity 1: Summarize the Log

Open GitHub Copilot Chat, select **Ask** mode, and attach `application.log` using `#file:application.log` or the context picker. Keep that file attached for all five prompts.

**Prompt 1: Log summarization**

```text
Analyze the attached application.log as an application support engineer.
Summarize the overall activity. Count all entries and give separate counts
for INFO, WARNING, and ERROR. Identify the exception types, highlight the
most important issues, and give a short operational health summary.
Use only the supplied log. Do not modify the file or generate code.
```

**Expected:** 18 entries: 6 INFO, 3 WARNING, and 9 ERROR. Startup and some employee operations succeeded, but the window also shows repeated database failures, invalid salary values, payment API timeouts, an employee lookup error, and a division-by-zero error. A successful health check does not establish that all dependencies were healthy.

## Activity 2: Group and Count Errors

**Prompt 2: Error classification**

```text
Group the ERROR entries in application.log by exception type. In a Markdown
table, give each type, its count, an exact example message, its first and
last timestamps, a possible root cause, and a suggested corrective action.
Separate warnings from errors and observed facts from hypotheses. Do not
assume repeated messages always share a root cause.
```

**Expected counts and evidence (all timestamps are on 2026-11-17):**

| Error type | Count | First | Last | Log lines |
| --- | ---: | --- | --- | --- |
| `DatabaseConnectionError` | 3 | 09:02:15 | 09:08:22 | 3, 4, 12 |
| `ValueError` | 2 | 09:04:10 | 09:04:45 | 6, 7 |
| `TimeoutError` | 2 | 09:06:30 | 09:06:55 | 9, 10 |
| `KeyError` | 1 | 09:10:30 | 09:10:30 | 14 |
| `ZeroDivisionError` | 1 | 09:12:10 | 09:12:10 | 16 |
| **Total** | **9** | | | |

The database error is the most frequent in this sample. Frequency alone does not establish impact, priority, or cause.

## Activity 3: Investigate Two Patterns

**Prompt 3: Database connectivity**

```text
Investigate DatabaseConnectionError in application.log. Report the count,
every failure timestamp, and the gaps between consecutive failures. Can
the log distinguish a continuous outage from intermittent failures? List
possible technical explanations, additional logs or metrics to check,
and preventive and corrective actions. Separate facts from hypotheses.
```

**Expected:** Three failures at `09:02:15`, `09:02:20`, and `09:08:22`. The consecutive gaps are **5 seconds** and **6 minutes 2 seconds**; the first-to-last span is **6 minutes 7 seconds**. The errors were logged at separated times, but the sample does not establish database availability between them. Check database uptime and resource metrics, connection pool usage and wait time, network and DNS errors, and authentication or configuration changes before choosing a fix.

**Prompt 4: Payment API timeouts**

```text
Analyze all TimeoutError entries in application.log. Give the count,
timestamps, spacing, possible impact on payment processing, and possible
causes. Recommend timeout, retry, and monitoring strategies. Explain how
to distinguish a temporary provider issue from a persistent integration
issue, and how to verify payment status before retrying. Do not assume a
timeout means the payment failed.
```

**Expected:** Two payment API timeouts at `09:06:30` and `09:06:55`, 25 seconds apart. Compare provider status and latency with client-side connection and timeout metrics, request IDs, and deployment history. A timeout only means the application did not receive a timely response. Check the provider's transaction status using the original reference or reconcile webhook events before retrying. Use bounded retries with backoff and reuse the original idempotency key when the provider supports it.

## Activity 4: Verify Every AI Finding

**Prompt 5: Evidence-based validation**

```text
Validate your previous error analysis against the original application.log.
Quote every ERROR entry exactly and give its 1-based line number. Verify
each group's count and first and last timestamps. Flag any missing or
misclassified entries. End with a table: Error Type | AI Count | Verified
Count | Validation Status. Do not invent log entries or fill gaps in the
evidence. Use only the original file.
```

Check the evidence independently in the terminal from the project root.

**Windows PowerShell**

```powershell
# Count database errors
(Select-String -Path application.log -Pattern '^\S+\s+\S+\s+ERROR\s+DatabaseConnectionError:' -CaseSensitive | Measure-Object).Count

# Count all lines and group by severity
(Get-Content application.log | Measure-Object).Count
Get-Content application.log | ForEach-Object { ($_ -split '\s+')[2] } | Group-Object -NoElement

# List exact ERROR lines with their original line numbers
Select-String -Path application.log -Pattern '^\S+\s+\S+\s+ERROR\s+' -CaseSensitive |
    ForEach-Object { '{0}: {1}' -f $_.LineNumber, $_.Line }
```

**macOS/Linux**

```bash
# Count database errors
grep -Ec '^[^[:space:]]+[[:space:]]+[^[:space:]]+[[:space:]]+ERROR[[:space:]]+DatabaseConnectionError:' application.log

# Count all lines and group by severity
awk '{count[$3]++} END {print "Total", NR; for (level in count) print level, count[level]}' application.log

# List exact ERROR lines with their original line numbers
awk '$3 == "ERROR" {print NR ": " $0}' application.log
```

The database command should return `3`, and the numbered listing should contain nine lines. For each exception type, tally the listed lines and check the earliest and latest timestamps against Copilot's claims. Check important observations against their source lines too, including the three warnings. Mark claims as **Verified**, **Mismatch**, or **Not established by the log**. Leave the fixture unchanged and correct the analysis rather than the evidence.