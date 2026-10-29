"""Admin-only Streamlit dashboard for the project's FastAPI forecast scheduler."""

import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
IST = ZoneInfo("Asia/Kolkata")

st.set_page_config(
    page_title="Forecast Scheduler",
    page_icon="📅",
    layout="wide",
)

st.title("📅 Forecast Scheduler")
st.caption("Monitor weekly ML forecasting and manage runs through the FastAPI backend.")


# Use the access token already created by the login page.
token = st.session_state.get("access_token")
if isinstance(token, dict):
    token = token.get("access_token")

if not token:
    st.warning("Please log in from the main Recommendation page first.")
    st.stop()

HEADERS = {"Authorization": f"Bearer {token}"}


def api_request(method: str, endpoint: str, timeout: int = 15):
    """Call the FastAPI backend without exposing credentials to Streamlit."""
    try:
        response = requests.request(
            method=method,
            url=f"{API_BASE_URL}{endpoint}",
            headers=HEADERS,
            timeout=timeout,
        )
    except requests.RequestException:
        st.error(
            "Cannot reach the FastAPI backend. Check that Uvicorn is running "
            "on http://127.0.0.1:8000 (or set API_BASE_URL)."
        )
        return None

    if response.status_code == 401:
        st.error("Your session has expired. Please log in again.")
        st.stop()

    if response.status_code == 403:
        st.error("Access denied. Scheduler management is restricted to Admin users.")
        st.stop()

    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", "Request failed")
        except (ValueError, AttributeError):
            detail = "Request failed"

        st.error(f"Backend error ({response.status_code}): {detail}")
        return None

    try:
        return response.json()
    except ValueError:
        st.error("The backend returned a non-JSON response.")
        return None


def display_time(value):
    """Display datetimes in IST; scheduler_runs timestamps are stored as UTC."""
    if not value:
        return "Not available"

    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            # auto_scheduler/run_log.py writes naive UTC timestamps.
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(IST).strftime("%d %b %Y, %I:%M %p IST")
    except (ValueError, TypeError):
        return str(value)


def display_number(value, decimals=2, suffix=""):
    if value is None:
        return "—"
    try:
        return f"{float(value):,.{decimals}f}{suffix}"
    except (ValueError, TypeError):
        return str(value)


# Frontend role visibility; the backend independently enforces Admin permissions.
profile = api_request("GET", "/auth/me")
if profile is None:
    st.stop()

if str(profile.get("role", "")).lower() != "admin":
    st.warning(
        "This page is for Admin only. Managers can use the other dashboard pages."
    )
    st.stop()

top_left, top_right = st.columns([5, 1])
with top_left:
    st.info(f"Logged in as **{profile.get('username', 'Admin')}** · Admin access")
with top_right:
    st.button("🔄 Refresh", use_container_width=True, help="Reload scheduler data")

history_limit = st.selectbox(
    "History records",
    options=[5, 10, 25, 50],
    index=1,
    help="Number of recent forecasting runs to display",
)

status_data = api_request("GET", "/scheduler/status")
next_data = api_request("GET", "/scheduler/next-run")
history_data = api_request("GET", f"/scheduler/history?limit={history_limit}")

if status_data is None or next_data is None or history_data is None:
    st.info("Resolve the backend error above, then refresh this page.")
    st.stop()

scheduler_running = bool(status_data.get("scheduler_running"))
pipeline_running = bool(status_data.get("pipeline_running"))
last_run = status_data.get("last_run") or {}
next_run_at = next_data.get("next_run_at")

st.subheader("Scheduler overview")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Scheduler", "Running" if scheduler_running else "Stopped")
with col2:
    st.metric("Forecast pipeline", "Running" if pipeline_running else "Idle")
with col3:
    st.metric("Last run", last_run.get("status", "No runs yet"))
with col4:
    st.metric("Records written (last run)", last_run.get("records_written") or 0)

st.write(f"**Next scheduled run:** {display_time(next_run_at)}")
st.caption(
    f"Scheduled job: {next_data.get('job_id', 'unknown')} · "
    f"Scheduler timezone: {next_data.get('timezone', 'unknown')}"
)

if not scheduler_running:
    st.warning("The scheduler is not running. Check the FastAPI startup logs.")

st.divider()
st.subheader("Most recent forecast run")

if not last_run:
    st.info("No scheduler runs have been recorded yet.")
else:
    a, b, c, d = st.columns(4)
    a.metric("Run ID", last_run.get("run_id", "—"))
    b.metric("Selected model", last_run.get("model_used") or "Pending")
    c.metric("Training weeks", last_run.get("training_weeks") or "—")
    d.metric(
        "Forecast accuracy",
        display_number(last_run.get("forecast_accuracy"), suffix="%"),
    )

    e, f = st.columns(2)
    e.metric("WMAPE (holdout)", display_number(last_run.get("wmape"), suffix="%"))
    f.metric("RMSE (holdout)", display_number(last_run.get("rmse")))

    st.write(
        f"**Started:** {display_time(last_run.get('triggered_at'))}  \n"
        f"**Completed:** {display_time(last_run.get('completed_at'))}  \n"
        f"**Triggered by:** {last_run.get('triggered_by', 'Unknown')}  \n"
        f"**Forecast anchor date:** {last_run.get('run_date_anchor', '—')}"
    )

    if last_run.get("error_message"):
        st.error(f"Last run error: {last_run['error_message']}")

st.divider()
st.subheader("Run history")
runs = history_data.get("runs") or []

if not runs:
    st.info("No historical runs available.")
else:
    table_rows = []
    for run in runs:
        table_rows.append(
            {
                "Run ID": run.get("run_id"),
                "Started (IST)": display_time(run.get("triggered_at")),
                "Completed (IST)": display_time(run.get("completed_at")),
                "Triggered by": run.get("triggered_by"),
                "Status": run.get("status"),
                "Model": run.get("model_used") or "—",
                "WMAPE (%)": run.get("wmape"),
                "RMSE": run.get("rmse"),
                "Accuracy (%)": run.get("forecast_accuracy"),
                "Records written": run.get("records_written"),
            }
        )
    st.dataframe(table_rows, use_container_width=True, hide_index=True)
    with st.expander("View error messages from historical runs"):
        failed = [run for run in runs if run.get("error_message")]
        if not failed:
            st.write("No error messages in the displayed history.")
        for run in failed:
            st.markdown(f"**Run {run.get('run_id')} ({run.get('status')})**")
            st.code(str(run.get("error_message")), language="text")

st.divider()
st.subheader("Run forecast manually")
st.warning(
    "A manual run executes the forecasting pipeline and may update the "
    "recommendation table and scheduler history in MariaDB."
)

confirmed = st.checkbox(
    "I understand that triggering the pipeline will write forecast results to the database.",
    key="scheduler_trigger_confirmed",
)

if st.button(
    "▶️ Start manual forecast",
    type="primary",
    disabled=not confirmed or pipeline_running,
):
    result = api_request("POST", "/scheduler/trigger", timeout=30)
    if result is not None:
        st.success(result.get("message", "Forecast run accepted."))
        st.info("Use Refresh to monitor its progress and final result.")

st.caption(
    "This dashboard uses the same JWT login as your other pages. "
    "Only the Admin role can access scheduler endpoints."
)