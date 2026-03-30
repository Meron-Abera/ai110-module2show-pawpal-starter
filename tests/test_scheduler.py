from datetime import datetime, timedelta

from pawpal_system import Task, ScheduleItem, Scheduler, TaskType


def test_resolve_conflicts_shifts_overlapping_items():
    scheduler = Scheduler()
    # create two tasks that overlap
    t1 = Task(id="t1", pet_id="p1", description="Task 1", task_type=TaskType.WALK,
              priority=2, duration_minutes=30, due_date=datetime(2026, 3, 29, 9, 0))
    t2 = Task(id="t2", pet_id="p1", description="Task 2", task_type=TaskType.WALK,
              priority=1, duration_minutes=30, due_date=datetime(2026, 3, 29, 9, 15))

    s1 = ScheduleItem(task=t1, start_time=t1.due_date, end_time=t1.due_date + timedelta(minutes=t1.duration_minutes))
    s2 = ScheduleItem(task=t2, start_time=t2.due_date, end_time=t2.due_date + timedelta(minutes=t2.duration_minutes))

    adjusted = scheduler.resolve_conflicts([s1, s2])
    # After resolution, the second item's start should be >= first's end
    assert adjusted[1].start_time >= adjusted[0].end_time
    # And the first item's time should be unchanged
    assert adjusted[0].start_time == s1.start_time
