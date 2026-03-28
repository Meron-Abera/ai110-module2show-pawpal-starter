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

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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
