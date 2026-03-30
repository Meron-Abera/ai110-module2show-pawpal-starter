import pytest
from datetime import datetime, date, timedelta

from pawpal_system import Task, Pet, TaskType, Owner, Scheduler


def test_task_completion_creates_recurring():
    t = Task(id="t1", pet_id="p1", description="Morning walk test", task_type=TaskType.WALK,
             due_date=datetime.now(), recurring=True)
    new = t.mark_complete()
    assert t.completed is True
    assert new is not None
    assert new.pet_id == t.pet_id
    assert new.completed is False


def test_pet_add_task_increases_count():
    pet = Pet(id="p1", owner_id="o1", name="Buddy")
    before = len(pet.tasks)
    t = Task(id="t2", pet_id="", description="Feed breakfast", task_type=TaskType.FEEDING)
    pet.add_task(t)
    assert len(pet.tasks) == before + 1
    assert pet.tasks[-1].pet_id == pet.id


def test_sorting_correctness():
    scheduler = Scheduler()
    pet = Pet(id="pet1", owner_id="o1", name="Fido")
    d = date(2026, 3, 29)
    # both tasks use the same priority so we can assert chronological ordering
    t_early = Task(id="t_early", pet_id=pet.id, description="Early", task_type=TaskType.WALK,
                   due_date=datetime(2026, 3, 29, 8, 0), priority=2)
    t_late = Task(id="t_late", pet_id=pet.id, description="Late", task_type=TaskType.WALK,
                  due_date=datetime(2026, 3, 29, 9, 0), priority=2)
    pet.add_task(t_late)
    pet.add_task(t_early)
    items = scheduler.generate_daily_plan(pet, d)
    assert len(items) == 2
    assert items[0].start_time < items[1].start_time
    assert items[0].start_time.hour == 8


def test_priority_sorting():
    """Verify scheduler orders by priority first, then time.

    Create a lower-priority task earlier in the day and a higher-priority task later.
    The scheduler should place the higher-priority task first.
    """
    scheduler = Scheduler()
    pet = Pet(id="pet2", owner_id="o2", name="Rex")
    d = date(2026, 3, 29)
    # lower priority (1) but earlier time
    t_low = Task(id="low", pet_id=pet.id, description="Low pr early", task_type=TaskType.ENRICHMENT,
                 due_date=datetime(2026, 3, 29, 8, 0), priority=1)
    # higher priority (3) but later time
    t_high = Task(id="high", pet_id=pet.id, description="High pr later", task_type=TaskType.ENRICHMENT,
                  due_date=datetime(2026, 3, 29, 10, 0), priority=3)
    pet.add_task(t_low)
    pet.add_task(t_high)
    items = scheduler.generate_daily_plan(pet, d)
    assert len(items) == 2
    # first item should be the high-priority task even though its time is later
    assert items[0].task.priority > items[1].task.priority


def test_recurring_mark_complete_creates_next_day():
    t = Task(id="r1", pet_id="pet1", description="Daily med", task_type=TaskType.MEDICATION,
             due_date=datetime(2026, 3, 29, 9, 0), recurring=True)
    old_due = t.due_date
    new = t.mark_complete()
    assert t.completed is True
    assert new is not None
    assert new.due_date == old_due + timedelta(days=1)


def test_conflict_detection_duplicate_times():
    owner = Owner(id="o1", name="Owner One")
    pet1 = Pet(id="p1", owner_id=owner.id, name="Alpha")
    pet2 = Pet(id="p2", owner_id=owner.id, name="Beta")
    d = date(2026, 3, 29)
    same_time = datetime(2026, 3, 29, 10, 0)
    t1 = Task(id="a1", pet_id=pet1.id, description="Walk A", task_type=TaskType.WALK,
              due_date=same_time, duration_minutes=30)
    t2 = Task(id="b1", pet_id=pet2.id, description="Walk B", task_type=TaskType.WALK,
              due_date=same_time, duration_minutes=30)
    pet1.add_task(t1)
    pet2.add_task(t2)
    owner.pets.append(pet1)
    owner.pets.append(pet2)
    scheduler = Scheduler()
    items, conflict_groups = scheduler.generate_owner_plan(owner, d)
    assert any(len(group) >= 2 for group in conflict_groups)
    warnings = scheduler.generate_conflict_warnings(items)
    assert any("start at the same time" in w for w in warnings)
