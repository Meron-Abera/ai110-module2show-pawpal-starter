from datetime import datetime, date, time, timedelta

from pawpal_system import Owner, Pet, Task, TaskType, Scheduler
from uuid import uuid4


def pretty_print_schedule(items):
    if not items:
        print("No scheduled items for today.")
        return

    print("Today's Schedule:\n")
    print("{:<8} {:<12} {:<30} {:<8} {}".format('Time', 'Pet', 'Task', 'Priority', 'Rec'))
    print("-" * 70)
    for it in items:
        t = it.task
        time_str = it.start_time.strftime("%H:%M")
        pet_name = it.pet_name or getattr(t, 'pet_id', '')
        desc = t.description[:28]
        pr = t.priority
        rec = 'Y' if t.recurring else ' '
        print(f"{time_str:<8} {pet_name:<12} {desc:<30} {pr!s:<8} {rec}")


def main():
    today = date.today()
    now = datetime.now()

    owner = Owner(id=str(uuid4()), name="Alex")

    # create two pets
    pet1 = Pet(id=str(uuid4()), owner_id=owner.id, name="Mochi")
    pet2 = Pet(id=str(uuid4()), owner_id=owner.id, name="Nala")
    owner.add_pet(pet1)
    owner.add_pet(pet2)

    # add tasks with different times today
    t1 = Task(
        id=str(uuid4()),
        pet_id=pet1.id,
        description="Morning walk",
        task_type=TaskType.WALK,
        priority=2,
        duration_minutes=30,
        due_date=datetime.combine(today, time(8, 0)),
        recurring=True,
    )

    t2 = Task(
        id=str(uuid4()),
        pet_id=pet2.id,
        description="Feed breakfast",
        task_type=TaskType.FEEDING,
        priority=3,
        duration_minutes=10,
        due_date=datetime.combine(today, time(7, 30)),
        recurring=True,
    )

    t3 = Task(
        id=str(uuid4()),
        pet_id=pet1.id,
        description="Grooming appointment",
        task_type=TaskType.GROOMING,
        priority=1,
        duration_minutes=45,
        due_date=datetime.combine(today, time(9, 0)),
        recurring=False,
    )

    pet1.add_task(t1)
    pet1.add_task(t3)
    pet2.add_task(t2)

    # Add a couple of tasks out of chronological order to simulate messy input
    t4 = Task(
        id=str(uuid4()),
        pet_id=pet2.id,
        description="Evening play",
        task_type=TaskType.ENRICHMENT,
        priority=1,
        duration_minutes=20,
        due_date=datetime.combine(today, time(19, 0)),
        recurring=False,
    )

    t5 = Task(
        id=str(uuid4()),
        pet_id=pet1.id,
        description="Midday meds",
        task_type=TaskType.MEDICATION,
        priority=5,
        duration_minutes=5,
        due_date=datetime.combine(today, time(12, 15)),
        recurring=True,
    )

    # Intentionally add in a non-chronological order
    pet2.add_task(t4)
    pet1.add_task(t5)

    # Add two tasks at the exact same time to demonstrate conflict warnings
    t6 = Task(
        id=str(uuid4()),
        pet_id=pet1.id,
        description="Training session",
        task_type=TaskType.ENRICHMENT,
        priority=2,
        duration_minutes=30,
        due_date=datetime.combine(today, time(15, 0)),
        recurring=False,
    )

    t7 = Task(
        id=str(uuid4()),
        pet_id=pet1.id,
        description="Vet call",
        task_type=TaskType.APPOINTMENT,
        priority=4,
        duration_minutes=15,
        due_date=datetime.combine(today, time(15, 0)),
        recurring=False,
    )

    pet1.add_task(t6)
    pet1.add_task(t7)

    scheduler = Scheduler()

    # Generate combined owner-level plan (sorted) and detect conflicts
    items, conflicts = scheduler.generate_owner_plan(owner, today)

    pretty_print_schedule(items)

    if conflicts:
        print("\nConflicts detected:")
        for group in conflicts:
            times = [f"{g.start_time.strftime('%H:%M')} ({g.pet_name or g.task.pet_id})" for g in group]
            print(" - " + "  |  ".join(times))

    # --- Demonstrate new sorting and filtering on Task objects ---
    print("\nDemonstrating task-level sort/filter (unsorted input):")
    tasks_today = owner.get_tasks_for_date(today)
    pet_map = {p.id: p.name for p in owner.pets}

    # Print unsorted tasks
    for t in tasks_today:
        time_str = t.due_date.strftime("%H:%M") if t.due_date else "--:--"
        print(f"{time_str}  {pet_map.get(t.pet_id, t.pet_id):<8}  {t.description}  pr={t.priority}")

    # Sort by time using the new helper
    sorted_tasks = scheduler.sort_by_time(tasks_today)
    print("\nTasks sorted by time:")
    for t in sorted_tasks:
        time_str = t.due_date.strftime("%H:%M") if t.due_date else "--:--"
        print(f"{time_str}  {pet_map.get(t.pet_id, t.pet_id):<8}  {t.description}  pr={t.priority}")

    # Filter tasks for a specific pet and status
    mochis_tasks = scheduler.filter_tasks(tasks_today, owner=owner, pet_name="Mochi", status="pending")
    print("\nFiltered tasks (Mochi, pending):")
    for t in mochis_tasks:
        time_str = t.due_date.strftime("%H:%M") if t.due_date else "--:--"
        print(f"{time_str}  {pet_map.get(t.pet_id, t.pet_id):<8}  {t.description}  pr={t.priority}")

    # Generate lightweight conflict warnings and print them (non-fatal)
    warnings = scheduler.generate_conflict_warnings(items)
    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print("WARNING:", w)


if __name__ == "__main__":
    main()
