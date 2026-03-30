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

- Design brainstorming: I used AI to iterate on the UML and to suggest alternative layouts for responsibilities (for example, moving overlap logic off Task and into a ScheduleItem wrapper).
- Implementation scaffolding: Copilot helped create method stubs, docstrings, and small helper functions (`to_dict`/`from_dict`) so I could focus on the core scheduling logic.
- Refactoring and exploration: While implementing `Scheduler` I asked for suggestions about conflict detection strategies and got a list of possible approaches (naive shift, backtracking search, optimization-based packing). That helped me pick a simple, explainable v1 approach.
- Tests: Copilot-style completions made writing small unit tests faster (it suggested test structure and assertions that I adapted).

Helpful prompts and questions:
- "Show an example implementation for detecting overlapping time intervals in Python." (led to `detect_conflicts` design)
- "How to safely create the next occurrence of a recurring task (daily/weekly)?" (guided `mark_complete` behavior)
- "Show me small pytest tests that assert task ordering by priority and time." (gave a starting point for the test file)

**b. Judgment and verification**

- One suggestion I rejected/modified: Copilot frequently suggested automatically resolving conflicts by reordering tasks (changing their scheduled times) without user confirmation. I rejected the fully-automatic variant and instead implemented a non-destructive suggestion flow: `resolve_conflicts` returns adjusted ScheduleItems and the UI presents them as suggestions the owner can accept. I rejected the auto-mutate behavior because it would silently change the user's plan and reduce trust.

- Another modification: Copilot recommended introducing a full Recurrence object immediately. I kept recurrence as a small, explicit rule (`recurrence` = 'daily' | 'weekly') for v1 so the behavior is easy to reason about and test; I documented plans to refactor into a richer recurrence model later.

- How I verified AI suggestions: for any substantive suggestion I ran the following checks before accepting it:
	1. Unit testability — can the idea be exercised in a small unit test? I wrote tests for sorting, recurrence, and conflict detection.
 2. Principle check — does the suggestion respect single responsibility and avoid surprising side effects? If a suggestion would mutate user data implicitly, I rejected or modified it.
 3. Simplicity and transparency — prefer the simpler, more explainable approach for v1 and document the design tradeoffs.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I focused testing on the behaviors that are central to the scheduler's correctness and to user trust:

- Recurrence behavior: that marking a recurring task complete creates a new Task for the next occurrence (daily/weekly). This ensures repeating care items (meds, walks) continue to appear.
- Sorting and ordering: that the scheduler orders tasks by priority first and by time when priorities match. This ensures owners see the most important tasks first.
- Conflict detection/resolution: that detect_conflicts finds overlapping items and that resolve_conflicts produces shifted suggestions where appropriate.

These tests are important because they validate the contract between the model and the UI: predictable ordering, correct recurrence behavior, and transparent conflict handling are essential for trust in a scheduling tool.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

Confidence: moderate-high for the current scope (single-owner, small task sets, simple recurrence rules). The unit tests cover the core white-box behaviors and the app demonstrates the flows end-to-end.

Edge cases to test next:

- Many overlapping tasks across several pets (stress test the conflict grouping and the suggestion algorithm).
- Tasks that span midnight or have very long durations (ensure day boundaries are respected).
- Timezone and DST transitions (ensure due_date handling remains correct across offsets).
- Complex recurrence rules (exceptions, monthly rules, or patterns like "every 2 days").
- Concurrent edits (if the app were multi-user or persisted to a shared DB).

## 5. Reflection

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I am most satisfied with producing a focused, well-tested core scheduler API (`pawpal_system.py`) and wiring a clear Streamlit demo UI that exposes the important flows: add task, generate schedule, view conflicts, accept suggestions. Keeping the core design small and testable made it straightforward to iterate safely.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

Key improvements I would prioritize in a next iteration:

- Richer recurrence model (Recurrence dataclass or rrule-like support).
- A pluggable conflict-resolution strategy (so the app can switch between "suggest only", "auto-resolve low-priority items", or "optimization-based packing").
- Persistence: persist Owner/Pet/Task records so schedules survive restarts and support multi-session testing.
- Session-state undo for applied adjustments (so owners can revert mistakes).


**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

Working with AI (Copilot-style tools) is most effective when you treat suggestions as a teammate rather than an oracle: accept scaffolded code and ideas when they improve productivity, but apply human judgment for design tradeoffs, testing, and user trust. As the lead architect you must set the system contract (inputs/outputs, side-effect policy, and error handling) and use AI to accelerate implementation within that contract. Small, testable increments + explicit decision notes (README/U ML/reflection) make it easy to iterate safely.


