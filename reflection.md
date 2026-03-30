# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

This design centers on four primary classes: Task, Pet, Owner, and Scheduler. The goal is to keep the domain model simple while supporting the base user actions and later adding scheduling intelligence.

Three core user actions:

- Add a pet: create and store pet information such as name, species, and notes.
- Add or edit tasks for a pet: create tasks like feeding, walking, medication with time, priority, frequency.
- View a daily schedule: aggregate tasks across pets, sorted and filtered for today, with conflict warnings.

Class responsibilities:

- Task: A data object representing a single activity. Holds description, time, frequency, duration, priority, and completion status. Provides methods like `mark_complete()` and `reschedule()`.
- Pet: Keeps basic pet metadata and a collection of Task objects. It provides methods to add or remove tasks and list its tasks.
- Owner: Manages multiple Pet objects and provides access to all pets' tasks. It provides convenience methods like `all_tasks()`.
- Scheduler: reads tasks from an Owner and provides utilities: sorting by time, filtering by pet or status, detecting conflicts, and generating a day's schedule.

Additional design notes:

- I represented recurring tasks and priorities as simple attributes on `Task`.
- I introduced a small `ScheduleItem` wrapper (task + start/end) to make overlap detection clearer and keep `Task` focused on task data rather than scheduling semantics.
- For clarity and type safety I used a `TaskType` enum to categorize tasks (WALK, FEEDING, MEDICATION, etc.).

Copilot review (asked using `#file:pawpal_system.py`):

- Observations:
	- The core relationships (Owner -> Pet -> Task) are present and explicit via `pets`, `owner_id`, and `pet_id` fields.
	- `ScheduleItem` is a good place for overlap logic (`overlaps_with`) so `Task` remains a plain data object.

- Suggested improvements / potential bottlenecks:
	1. Recurrence detail: `Task.recurring` is currently a bool — Copilot suggested adding a recurrence specification (daily/weekly/interval) or a small Recurrence object so the Scheduler can compute next occurrences reliably.
	2. Scheduler scope: `Scheduler.generate_daily_plan` currently accepts a single `Pet`. For owner-level schedules you will need a Scheduler method that aggregates across an `Owner`'s pets (or give Scheduler an `owner_ref`).
	3. Task lookup and IDs: methods that find/remove tasks by id will scan lists O(n). For larger data sets, an index (dict mapping id -> Task) or keeping tasks in a dict would be more efficient.
	4. Time handling and timezones: Copilot recommended normalizing times to timezone-aware datetimes and validating `due_date` formats early to avoid surprises when sorting or computing recurrences.
	5. Persistence hooks: add `to_dict()`/`from_dict()` implementations early to simplify future save/load logic (JSON persistence).
	6. Conflict resolution complexity: current stubs imply a hardcoded strategy — Copilot advised making the conflict strategy pluggable or at least documenting the v1 strategy (warn, then manual resolution).

These observations helped me prioritize the next concrete changes (see 1b).

**b. Design changes**

Yes — I made a few deliberate changes while translating the UML into code. Below are the notable edits and the reasons:

1) Added `TaskType` enum
	- Why: makes task categories explicit and reduces magic strings in code. It helps the UI and any filtering logic.

2) Introduced `ScheduleItem` (task + start/end)
	- Why: moved overlap logic out of `Task` into `ScheduleItem` so `Task` stays a pure data record. This aligns with the Single Responsibility Principle and makes conflict detection simpler.

3) Included id fields and timestamps on Task, Pet, Owner
	- Why: practical needs for lookup, removal, and future persistence/versioning; timestamps make auditing and recurrence easier.

4) Kept Scheduler methods scoped per-pet for the initial skeleton but documented the need for an owner-level aggregation method
	- Why: implementing per-pet scheduling is simpler for the v1 CLI demos. Copilot suggested either adding an `owner_ref` to Scheduler or an `aggregate` method; I deferred implementing that immediately to keep the skeleton focused and to avoid premature coupling.

Planned follow-ups (based on Copilot feedback):

- Replace `Task.recurring: bool` with a small recurrence spec (enum or Recurrence dataclass) so `mark_complete()` can compute next occurrences safely.
- Implement `to_dict()` / `from_dict()` on dataclasses and add a simple JSON persistence helper on `Owner` to support Challenge 2 (persistence).
- Add an index (dict) in `Owner` for fast task/pet lookup if tests show performance problems.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

One tradeoff I made in the scheduler was keeping conflict detection simple instead of trying to automatically fix everything. Right now, it just flags exact start-time conflicts and shows overlapping tasks as warnings, instead of rescheduling them on its own. I did this on purpose it keeps the system predictable and easy to understand, especially for a CLI/demo version. Users can trust that their tasks won’t be changed behind the scenes.

The downside is that it’s not perfect. It can miss edge cases, like tasks that almost overlap but don’t technically conflict, and it doesn’t take into account user preferences for which task should move. It also puts the responsibility on the user to resolve conflicts instead of handling it automatically.

I think this is a reasonable tradeoff for v1. For a pet-owner scheduling tool, trust and transparency matter more than automation early on. It’s better for users to see what’s happening and make the decision themselves. Later, we can introduce smarter features like priority-based rescheduling or time constraints once we have more data and a better sense of what users actually want.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
