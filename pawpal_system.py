"""PawPal system logic layer - dataclass skeletons and scheduler stubs.

This file contains the core domain classes for the PawPal+ project
implemented as lightweight dataclasses and class skeletons. Methods are
stubs intended to be filled in during implementation phases.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date, time, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import uuid4


class TaskType(Enum):
    WALK = "WALK"
    FEEDING = "FEEDING"
    MEDICATION = "MEDICATION"
    GROOMING = "GROOMING"
    ENRICHMENT = "ENRICHMENT"
    APPOINTMENT = "APPOINTMENT"


@dataclass
class Task:
    id: str
    pet_id: str
    description: str
    task_type: TaskType
    priority: int = 0
    duration_minutes: int = 0
    completed: bool = False
    due_date: Optional[datetime] = None
    recurring: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task complete.

        If the task is recurring, return a new Task representing the
        next occurrence. Otherwise return None.
        """
        self.completed = True
        self.updated_at = datetime.now()
        if self.recurring and self.due_date:
            # simple daily recurrence for v1
            next_due = self.due_date + timedelta(days=1)
            new_task = Task(
                id=str(uuid4()),
                pet_id=self.pet_id,
                description=self.description,
                task_type=self.task_type,
                priority=self.priority,
                duration_minutes=self.duration_minutes,
                completed=False,
                due_date=next_due,
                recurring=self.recurring,
            )
            return new_task
        return None

    def reschedule(self, new_date: datetime) -> None:
        """Change the due_date/time for this task."""
        self.due_date = new_date
        self.updated_at = datetime.now()

    def is_due(self, on_date: date) -> bool:
        """Return True if this task is due on the provided date."""
        if not self.due_date:
            return False
        return self.due_date.date() == on_date

    def to_dict(self) -> Dict[str, Any]:
        """Serialize Task to a plain dictionary (JSON-safe types)."""
        return {
            "id": self.id,
            "pet_id": self.pet_id,
            "description": self.description,
            "task_type": self.task_type.value,
            "priority": self.priority,
            "duration_minutes": self.duration_minutes,
            "completed": self.completed,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "recurring": self.recurring,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create a Task instance from a dictionary (expects ISO datetimes)."""
        due = None
        if data.get("due_date"):
            due = datetime.fromisoformat(data["due_date"])  # simple ISO parsing
        return cls(
            id=data["id"],
            pet_id=data.get("pet_id", ""),
            description=data.get("description", ""),
            task_type=TaskType(data.get("task_type", "WALK")),
            priority=int(data.get("priority", 0)),
            duration_minutes=int(data.get("duration_minutes", 0)),
            completed=bool(data.get("completed", False)),
            due_date=due,
            recurring=bool(data.get("recurring", False)),
        )


@dataclass
class Pet:
    id: str
    owner_id: str
    name: str
    species: Optional[str] = None
    breed: Optional[str] = None
    dob: Optional[date] = None
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a Task to this Pet."""
        # ensure task knows its pet_id
        task.pet_id = self.id
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove a Task by id."""
        self.tasks = [t for t in self.tasks if t.id != task_id]

    def get_tasks(self, filter: Optional[Dict[str, Any]] = None) -> List[Task]:
        """Return tasks, optionally filtered by a dict of criteria."""
        result = list(self.tasks)
        if not filter:
            return result
        # filter by status: 'completed'|'pending'
        status = filter.get("status")
        if status == "completed":
            result = [t for t in result if t.completed]
        elif status == "pending":
            result = [t for t in result if not t.completed]
        # filter by date (date object)
        fdate = filter.get("date")
        if fdate:
            result = [t for t in result if t.due_date and t.due_date.date() == fdate]
        return result

    def to_dict(self) -> Dict[str, Any]:
        """Serialize Pet and its tasks to a dictionary."""
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "name": self.name,
            "species": self.species,
            "breed": self.breed,
            "dob": self.dob.isoformat() if self.dob else None,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pet":
        """Create a Pet (and nested Tasks) from a dictionary."""
        pet = cls(
            id=data["id"],
            owner_id=data.get("owner_id", ""),
            name=data.get("name", ""),
            species=data.get("species"),
            breed=data.get("breed"),
            dob=datetime.fromisoformat(data["dob"]).date() if data.get("dob") else None,
        )
        for tdata in data.get("tasks", []):
            pet.tasks.append(Task.from_dict(tdata))
        return pet


@dataclass
class Owner:
    id: str
    name: str
    email: Optional[str] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a Pet under this Owner."""
        pet.owner_id = self.id
        self.pets.append(pet)

    def remove_pet(self, pet_id: str) -> None:
        """Remove a pet by id."""
        self.pets = [p for p in self.pets if p.id != pet_id]

    def find_pet(self, pet_id_or_name: str) -> Optional[Pet]:
        """Return a Pet matching id or name, or None."""
        for p in self.pets:
            if p.id == pet_id_or_name or p.name.lower() == pet_id_or_name.lower():
                return p
        return None

    def get_tasks_for_date(self, for_date: date) -> List[Task]:
        """Aggregate tasks across pets for the given date."""
        tasks: List[Task] = []
        for p in self.pets:
            tasks.extend(p.get_tasks(filter={"date": for_date}))
        return tasks

    def to_dict(self) -> Dict[str, Any]:
        """Serialize Owner (and nested Pets) to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "preferences": self.preferences,
            "pets": [p.to_dict() for p in self.pets],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Owner":
        """Create an Owner (and nested Pets) from a dictionary."""
        owner = cls(id=data["id"], name=data.get("name", ""), email=data.get("email"))
        owner.preferences = data.get("preferences", {})
        for pdata in data.get("pets", []):
            owner.pets.append(Pet.from_dict(pdata))
        return owner


@dataclass
class ScheduleItem:
    task: Task
    start_time: datetime
    end_time: datetime

    def overlaps_with(self, other: "ScheduleItem") -> bool:
        """Return True if this schedule item overlaps the other."""
        return not (self.end_time <= other.start_time or self.start_time >= other.end_time)


class Scheduler:
    """High-level scheduler responsible for producing daily plans and
    detecting/resolving conflicts.

    This class intentionally uses a simple strategy for v1 and exposes
    stubs that can be implemented and tested incrementally.
    """

    def __init__(self, timezone: str = "UTC", max_daily_minutes: int = 24 * 60,
                 day_start: time = time(6, 0), day_end: time = time(22, 0)) -> None:
        self.timezone = timezone
        self.max_daily_minutes = max_daily_minutes
        self.day_start = day_start
        self.day_end = day_end

    def generate_daily_plan(self, pet: Pet, for_date: date) -> List[ScheduleItem]:
        """Produce a list of ScheduleItem objects for one pet on a date."""
        tasks = pet.get_tasks(filter={"date": for_date, "status": "pending"})
        items: List[ScheduleItem] = []
        for t in tasks:
            if not t.due_date:
                continue
            start = t.due_date
            duration = t.duration_minutes or 30
            end = start + timedelta(minutes=duration)
            items.append(ScheduleItem(task=t, start_time=start, end_time=end))
        # basic resolution: sort and then attempt to resolve collisions
        items = sorted(items, key=lambda i: i.start_time)
        items = self.resolve_conflicts(items)
        return items

    def score_task(self, task: Task) -> int:
        """Return an integer score used when ordering tasks."""
        # higher priority -> higher score. More recent due times slightly preferred.
        score = int(task.priority) * 100000
        if task.due_date:
            # earlier due_date increases priority (smaller timestamp -> bigger addition)
            # we invert timestamp to ensure earlier times have higher score contribution
            score += max(0, 100000 - int(task.due_date.timestamp() % 100000))
        return score

    def filter_eligible_tasks(self, tasks: List[Task], for_date: date) -> List[Task]:
        """Return tasks that are eligible to be scheduled on a given date."""
        result = []
        for t in tasks:
            if t.completed:
                continue
            if not t.due_date:
                continue
            if t.due_date.date() == for_date:
                result.append(t)
        return result

    def sort_tasks(self, tasks: List[Task]) -> List[Task]:
        """Return tasks sorted by time/priority (stable)."""
        return sorted(tasks, key=lambda t: (-int(t.priority), t.due_date or datetime.max))

    def detect_conflicts(self, items: List[ScheduleItem]) -> List[List[ScheduleItem]]:
        """Return groups of ScheduleItems that conflict with each other."""
        if not items:
            return []
        groups: List[List[ScheduleItem]] = []
        items_sorted = sorted(items, key=lambda i: i.start_time)
        current_group = [items_sorted[0]]
        for item in items_sorted[1:]:
            last = current_group[-1]
            if last.overlaps_with(item):
                current_group.append(item)
            else:
                if len(current_group) > 1:
                    groups.append(current_group)
                current_group = [item]
        if len(current_group) > 1:
            groups.append(current_group)
        return groups

    def resolve_conflicts(self, items: List[ScheduleItem]) -> List[ScheduleItem]:
        """Attempt to resolve conflicts and return an adjusted schedule."""
        if not items:
            return []
        items = sorted(items, key=lambda i: i.start_time)
        resolved: List[ScheduleItem] = [items[0]]
        for item in items[1:]:
            prev = resolved[-1]
            if prev.overlaps_with(item):
                # naive resolution: shift the current item's start to prev.end_time
                delta = prev.end_time - item.start_time
                item.start_time = item.start_time + delta
                item.end_time = item.end_time + delta
                # if shifting still overlaps with next items, further shifts will happen in later iterations
            resolved.append(item)
        return resolved


__all__ = [
    "TaskType",
    "Task",
    "Pet",
    "Owner",
    "ScheduleItem",
    "Scheduler",
]
