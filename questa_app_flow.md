## 🧭 Dev Leveler – App Flow & Navigation Map (Python + Textual)

---

### 🟢 1. Startup Screen (Splash / Welcome)

- **Name**: `WelcomeScreen`
- **Shown on launch**
- **Displays:**
  - ASCII logo of "Dev Leveler"
  - Player level, XP bar
  - Press `[Enter]` to begin

**→ Navigates to:** `HomeScreen`

---

### 🏠 2. Home Screen – Dashboard

- **Name**: `HomeScreen`
- **Displays:**
  - Player name, level, XP bar
  - Current quests (today’s tasks)
  - Streak counter
  - Footer nav hints

**Options:**

- `[Q]` – Quests (All Tasks)
- `[L]` – Leveling & Stats
- `[J]` – Journal (History)
- `[A]` – Add New Task
- `[Enter]` – Complete selected task
- `[Esc]` – Exit app

---

### 📝 3. Quests Screen – Full Task Log

- **Name**: `QuestsScreen`
- **View all tasks:**
  - Filter by: today / all / completed
  - Mark as done
  - Delete/edit task

**Navigation:**

- `[←] Back` to Home
- `[Enter]` Complete task
- `[E]` Edit selected task

---

### 🧠 4. Leveling Screen – XP & Titles

- **Name**: `LevelingScreen`
- **Displays:**
  - Current level
  - XP required to next level
  - Unlocked titles
  - Earned badges (e.g., “Bug Slayer”)

**Navigation:**

- `[←] Back` to Home

---

### 📜 5. Journal Screen – Task History

- **Name**: `JournalScreen`
- **Displays:**
  - Completed quests log
  - Daily summaries (e.g., "Aug 5: +30 XP from 3 quests")
  - Optional notes or reflections

**Navigation:**

- `[←] Back` to Home

---

### ➕ 6. Add Task Screen

- **Name**: `AddTaskScreen`
- **Form to input:**
  - Task title
  - Difficulty (Easy / Medium / Hard → XP)
  - Optional notes

**Navigation:**

- `[Enter]` Save & return to Home
- `[←] Back` to cancel

---

### 🪜 Bonus: Level Up Modal / Animation

- **Triggered when** XP crosses threshold
- Celebratory popup with sound / animation (if supported)
- Shows new title unlocked

---

### 🧭 Navigation Summary

```
WelcomeScreen
   ↓ [Enter]
HomeScreen
   ├─ [Q] → QuestsScreen
   ├─ [L] → LevelingScreen
   ├─ [J] → JournalScreen
   ├─ [A] → AddTaskScreen
   └─ [Esc] → Exit App
```

---

### 🧱 Suggested Navigation Framework

Textual supports a **Screen Stack**, so you can use:

```python
await self.app.push_screen(QuestsScreen())
await self.app.pop_screen()
```

