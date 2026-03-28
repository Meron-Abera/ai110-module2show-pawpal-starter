import streamlit as st
from uuid import uuid4
from datetime import date, datetime

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
        duration_minutes=int(duration),
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
st.caption("This button should call your scheduling logic once you implement it.")

if st.button("Generate schedule"):
    st.warning(
        "Not implemented yet. Next step: create your scheduling logic (classes/functions) and call it here."
    )
    st.markdown(
        """
Suggested approach:
1. Design your UML (draft).
2. Create class stubs (no logic).
3. Implement scheduling behavior.
4. Connect your scheduler here and display results.
"""
    )
