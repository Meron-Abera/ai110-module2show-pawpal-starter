"""PawPal system logic layer - dataclass skeletons and scheduler stubs.

This file contains the core domain classes for the PawPal+ project
implemented as lightweight dataclasses and class skeletons. Methods are
stubs intended to be filled in during implementation phases.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date, time, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple
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
    # human-friendly priority label (e.g. 'low', 'medium', 'high') kept for UI display
    priority_label: Optional[str] = None
    duration_minutes: int = 0
    completed: bool = False
    due_date: Optional[datetime] = None
    # recurring kept for backward compatibility (boolean), but prefer using
    # `recurrence` to specify 'daily' or 'weekly' recurrence rules.
    recurring: bool = False
    recurrence: Optional[str] = None  # e.g. 'daily' or 'weekly'
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def mark_complete(self) -> Optional["Task"]:
        """Mark this task complete.

        If the task is recurring, return a new Task representing the
        next occurrence. Otherwise return None.
        """
        self.completed = True
        self.updated_at = datetime.now()
        # Determine recurrence rule. Backwards-compat: if `recurrence` is not
        # set but `recurring==True`, assume daily recurrence.
        rule = self.recurrence
        if not rule and self.recurring:
            rule = "daily"

        if rule and self.due_date:
            # Use timedelta to compute next occurrence accurately:
            # - daily -> +1 day
            # - weekly -> +7 days
            # If more rules are added later, extend here.
            if rule == "daily":
                next_due = self.due_date + timedelta(days=1)
            elif rule == "weekly":
                next_due = self.due_date + timedelta(days=7)
            else:
                # Unknown recurrence rule — do not auto-create.
                return None

            new_task = Task(
                id=str(uuid4()),
                pet_id=self.pet_id,
                description=self.description,
                task_type=self.task_type,
                priority=self.priority,
                duration_minutes=self.duration_minutes,
                completed=False,
                due_date=next_due,
                recurring=bool(rule),
                recurrence=rule,
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
            "recurrence": self.recurrence,
            "priority_label": self.priority_label,
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
            priority_label=data.get("priority_label"),
            duration_minutes=int(data.get("duration_minutes", 0)),
            completed=bool(data.get("completed", False)),
            due_date=due,
            recurring=bool(data.get("recurring", False)),
            recurrence=data.get("recurrence"),
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
    # include pet_name to avoid mutating Task.pet_id when presenting schedules
    pet_name: Optional[str] = None

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

    def generate_daily_plan(self, pet: Pet, for_date: date, status_filter: Optional[str] = "pending") -> List[ScheduleItem]:
        """Produce a list of ScheduleItem objects for one pet on a date."""
        tasks = pet.get_tasks(filter={"date": for_date, "status": status_filter})
        items: List[ScheduleItem] = []
        for t in tasks:
            if not t.due_date:
                continue
            start = t.due_date
            duration = t.duration_minutes or 30
            end = start + timedelta(minutes=duration)
            items.append(ScheduleItem(task=t, start_time=start, end_time=end, pet_name=pet.name))
        # basic resolution: sort by priority (desc) then start time and then attempt to resolve collisions
        items = sorted(items, key=lambda i: (-int(i.task.priority), i.start_time))
        items = self.resolve_conflicts(items)
        return items

    def generate_owner_plan(self, owner: "Owner", for_date: date,
                            pet_filter: Optional[str] = None,
                            status_filter: Optional[str] = "pending") -> Tuple[List[ScheduleItem], List[List[ScheduleItem]]]:
        """Produce a combined, sorted schedule for an Owner across pets.

        Args:
            owner: Owner whose pets' tasks will be aggregated.
            for_date: date for which to generate the plan.
            pet_filter: optional pet id or pet name (case-insensitive) to limit results.
            status_filter: optional status filter matching Pet.get_tasks values
                ("pending" or "completed"). Defaults to "pending".

        Returns:
            A tuple (items, conflict_groups) where `items` is a list of
            ScheduleItem objects sorted by start_time and `conflict_groups`
            is a list of groups (each group a list of ScheduleItems) that
            overlap according to `detect_conflicts`.
        """
        items: List[ScheduleItem] = []
        for p in owner.pets:
            if pet_filter:
                pf = pet_filter.lower()
                if not (p.id == pet_filter or p.name.lower() == pf):
                    continue
            items.extend(self.generate_daily_plan(p, for_date, status_filter=status_filter))

        # owner-level sorting: prioritize higher-priority tasks first, then by start time
        items = sorted(items, key=lambda i: (-int(i.task.priority), i.start_time))

        # detect conflicts across pets
        conflict_groups = self.detect_conflicts(items)
        return items, conflict_groups

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

    def sort_by_time(self, tasks: List[Task]) -> List[Task]:
        """Return tasks sorted by their due time (time-of-day).

        Tasks without a `due_date` are placed at the end of the list. The
        sort key uses the task's `due_date.time()` where available so that
        ordering is by clock time (HH:MM) regardless of the date component.

        Args:
            tasks: list of Task objects to sort.

        Returns:
            A new list of Task objects sorted by time-of-day.
        """
        return sorted(tasks, key=lambda t: (t.due_date.time() if t.due_date else time(23, 59)))

    def filter_tasks(self, tasks: List[Task], owner: Optional["Owner"] = None,
                     pet_name: Optional[str] = None, status: Optional[str] = None) -> List[Task]:
        """Filter a list of Task objects by pet name and/or completion status.

        Args:
            tasks: list of Task objects to filter.
            owner: optional Owner required when filtering by `pet_name` so
                that pet names can be mapped to pet ids.
            pet_name: optional pet name to include (case-insensitive).
            status: optional status string, either 'pending' or 'completed'.

        Returns:
            A filtered list of Task objects matching the provided criteria.
        """
        result = list(tasks)
        if status:
            if status == "completed":
                result = [t for t in result if t.completed]
            elif status == "pending":
                result = [t for t in result if not t.completed]

        if pet_name:
            if not owner:
                # can't map names without owner; return empty list to signal misuse
                return []
            pn = pet_name.lower()
            pet_map = {p.id: p.name.lower() for p in owner.pets}
            allowed_ids = [pid for pid, name in pet_map.items() if name == pn]
            result = [t for t in result if t.pet_id in allowed_ids]

        return result

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

    def generate_conflict_warnings(self, items: List[ScheduleItem]) -> List[str]:
        """Generate human-friendly warning messages describing schedule conflicts.

        This is a lightweight conflict detection helper intended for UI/CLI
        presentation. It does not modify tasks or schedules; it returns
        strings that callers can display to users.

        The current strategy reports two kinds of warnings:
        1. Exact-start collisions: two or more ScheduleItems with identical
           `start_time` values.
        2. Overlapping groups: any groups found by `detect_conflicts`.

        Args:
            items: list of ScheduleItem objects to analyze.

        Returns:
            A list of formatted warning strings (empty if no issues found).
        """
        warnings: List[str] = []
        if not items:
            return warnings

        # Exact same start_time collisions
        start_map: Dict[datetime, List[ScheduleItem]] = {}
        for it in items:
            start_map.setdefault(it.start_time, []).append(it)

        for st, group in start_map.items():
            if len(group) > 1:
                pets = [g.pet_name or g.task.pet_id for g in group]
                descs = [g.task.description for g in group]
                warnings.append(
                    f"{len(group)} tasks start at the same time {st.strftime('%Y-%m-%d %H:%M')}: "
                    + "; ".join([f"{p}: {d}" for p, d in zip(pets, descs)])
                )

        # Overlapping groups (non-exact overlaps)
        groups = self.detect_conflicts(items)
        for group in groups:
            # present a compact summary: earliest start - latest end, with involved pets
            earliest = min(g.start_time for g in group)
            latest = max(g.end_time for g in group)
            pets = {g.pet_name or g.task.pet_id for g in group}
            warnings.append(
                f"Overlap between {len(group)} tasks from {earliest.strftime('%H:%M')} to {latest.strftime('%H:%M')} (pets: {', '.join(pets)})"
            )

        return warnings

    def resolve_conflicts(self, items: List[ScheduleItem]) -> List[ScheduleItem]:
        """Attempt to resolve conflicts and return an adjusted schedule."""
        if not items:
            return []
        # Do not reorder items here; respect the ordering provided by the
        # caller (which may be priority-first). Only adjust overlapping
        # items by shifting them forward. Sorting here would erase the
        # caller's ordering (e.g., priority-based sorting), so avoid it.
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
