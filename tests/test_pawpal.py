import pytest
from datetime import datetime

from pawpal_system import Task, Pet, TaskType


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
