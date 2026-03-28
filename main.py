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
        pet_name = getattr(t, 'pet_id', '')
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

    scheduler = Scheduler()

    # generate schedule for each pet, then combine and sort
    items = []
    for p in owner.pets:
        items.extend(scheduler.generate_daily_plan(p, today))

    # Sort combined schedule by start_time
    items = sorted(items, key=lambda i: i.start_time)

    # For readability, attach pet name into task.pet_id field temporarily
    # (the system currently stores pet_id) — replace pet_id with pet name for printing
    pet_map = {p.id: p.name for p in owner.pets}
    for it in items:
        if it.task.pet_id in pet_map:
            it.task.pet_id = pet_map[it.task.pet_id]

    pretty_print_schedule(items)


if __name__ == "__main__":
    main()
