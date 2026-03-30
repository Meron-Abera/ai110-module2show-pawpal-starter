import streamlit as st
from uuid import uuid4
from datetime import date, datetime, time

# import domain classes from the logic layer
from pawpal_system import Owner, Pet, Task, TaskType, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.
"""
    )



st.divider()

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])


## Persist an Owner instance in Streamlit's session_state so it survives reruns
if "owner" not in st.session_state:
    st.session_state.owner = Owner(id=str(uuid4()), name=owner_name)

# whether the schedule panel is visible (persist across reruns)
if "show_schedule" not in st.session_state:
    st.session_state.show_schedule = False

# keep the owner name in sync with the text input
if st.session_state.owner.name != owner_name:
    st.session_state.owner.name = owner_name

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

# add date and time inputs so tasks created via the UI have a due_date
col4, col5 = st.columns(2)
with col4:
    task_date = st.date_input("Task date", value=date.today())
with col5:
    task_time = st.time_input("Task time", value=time(9, 0))

if st.button("Add task"):
    owner = st.session_state.owner
    pet = owner.find_pet(pet_name)
    if pet is None:
        pet = Pet(id=str(uuid4()), owner_id=owner.id, name=pet_name)
        owner.add_pet(pet)

    pr_map = {"low": 1, "medium": 2, "high": 3}
    pr = pr_map.get(priority, 1)

    t = Task(
        id=str(uuid4()),
        pet_id=pet.id,
        description=task_title,
        task_type=TaskType.ENRICHMENT,
        priority=pr,
        priority_label=priority,
        duration_minutes=int(duration),
        due_date=datetime.combine(task_date, task_time),
        recurring=False,
    )
    pet.add_task(t)
    st.success(f"Added task '{task_title}' for pet {pet.name}")

if st.session_state.owner.pets:
    rows = []
    for p in st.session_state.owner.pets:
        for t in p.tasks:
            rows.append({
                "pet": p.name,
                "task": t.description,
                "duration": t.duration_minutes,
                "priority": t.priority,
            })
    st.write("Current tasks:")
    st.table(rows)
else:
    st.info("No pets or tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("Generate a schedule for the selected date using the Scheduler logic.")

# date selector for schedule generation
selected_date = st.date_input("Schedule date", value=date.today())

# option: include completed tasks so they don't disappear immediately when marked
show_completed = st.checkbox("Include completed tasks in the schedule", value=True)

# helpers for priority display
def _priority_label(task: Task) -> str:
    if getattr(task, "priority_label", None):
        return str(task.priority_label)
    # fallback to numeric
    if task.priority >= 3:
        return "high"
    if task.priority == 2:
        return "medium"
    return "low"

def _priority_emoji(label: str) -> str:
    m = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low"}
    return m.get(label, str(label))


def _maybe_rerun() -> None:
    """Call Streamlit's rerun if available; otherwise do nothing.

    Some Streamlit versions don't expose `st.experimental_rerun`. Button
    callbacks already trigger a rerun, so this is a safe no-op fallback.
    """
    rerun = getattr(st, "experimental_rerun", None)
    if callable(rerun):
        try:
            rerun()
        except Exception:
            # swallow errors from rerun to avoid crashing the app
            return

scheduler = Scheduler()

if st.button("Generate schedule"):
    st.session_state.show_schedule = True

# allow hiding the schedule panel
if st.session_state.show_schedule:
    if st.button("Hide schedule"):
        st.session_state.show_schedule = False

if st.session_state.show_schedule:
    owner = st.session_state.owner
    # fetch pending and completed separately so completed tasks can be shown below
    pending_items, pending_conflicts = scheduler.generate_owner_plan(owner, selected_date, status_filter="pending")
    completed_items, _ = scheduler.generate_owner_plan(owner, selected_date, status_filter="completed")

    # present pending schedule in a table (top)
    if not pending_items:
        st.info("No pending scheduled items for the selected date.")
    else:
        rows = []
        for it in pending_items:
            t = it.task
            label = _priority_label(t)
            rows.append({
                "time": it.start_time.strftime("%Y-%m-%d %H:%M"),
                "pet": it.pet_name or t.pet_id,
                "task": t.description,
                "priority": _priority_emoji(label),
                "recurring": bool(t.recurring),
            })

        st.write("### Pending Schedule")
        st.table(rows)

        # actions for pending tasks
        st.write("### Actions")
        for it in pending_items:
            t = it.task
            pet = None
            for p in owner.pets:
                if p.id == t.pet_id:
                    pet = p
                    break
            col1, col2 = st.columns([3, 1])
            with col1:
                label = f"{it.start_time.strftime('%H:%M')} — {it.pet_name or t.pet_id}: {t.description}"
                st.write(label)
            with col2:
                key_complete = f"complete_{t.id}"
                if st.button("Mark complete", key=key_complete):
                    new = t.mark_complete()
                    if new and pet is not None:
                        pet.add_task(new)
                        st.success(f"Marked complete. Created next occurrence for {pet.name} at {new.due_date}")
                    else:
                        st.success("Marked complete.")
                    # keep schedule visible across reruns
                    st.session_state.show_schedule = True
                    _maybe_rerun()

    # present completed tasks in an expander below (always fetched)
    with st.expander("Completed tasks", expanded=True):
        if not completed_items:
            st.write("No completed tasks for this date.")
        else:
            crow = []
            for it in completed_items:
                t = it.task
                crow.append({
                    "time": it.start_time.strftime("%Y-%m-%d %H:%M"),
                    "pet": it.pet_name or t.pet_id,
                    "task": t.description,
                    "priority": t.priority,
                    "recurring": bool(t.recurring),
                })
            st.table(crow)
            # allow unmarking completed tasks
            for it in completed_items:
                t = it.task
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**✅ {it.start_time.strftime('%H:%M')} — {it.pet_name or t.pet_id}: {t.description}**")
                with col2:
                    key_uncomplete = f"uncomplete_{t.id}"
                    if st.button("Unmark", key=key_uncomplete):
                        t.completed = False
                        # keep schedule visible
                        st.session_state.show_schedule = True
                        st.success("Marked as pending again.")
                        _maybe_rerun()

    # show conflict warnings for pending items
    warnings = scheduler.generate_conflict_warnings(pending_items)
    for w in warnings:
        st.warning(w)
