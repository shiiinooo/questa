# QUESTA - Professional TUI Task Manager

**QUESTA** is a gamified task management application built as a Terminal User Interface (TUI). It transforms your daily development tasks into an engaging RPG-like experience where you earn XP, level up, and track your progress through a beautiful, keyboard-driven interface.


## 🚀 Technology Stack

### Core Technologies
- **[Textual](https://textual.textualize.io/)** `v0.40.0+` - Modern Python framework for building sophisticated TUI applications
- **[Rich](https://rich.readthedocs.io/)** `v13.0.0+` - Rich text and beautiful formatting in the terminal
- **Python 3.8+** - Modern Python with type hints and dataclasses

### Architecture
- **MVC Pattern**: Clean separation between models, views (screens), and data management
- **Component-Based UI**: Reusable widgets built with Textual's reactive system
- **JSON Data Persistence**: Local file storage for tasks and player progress
- **Type-Safe Design**: Full type hints throughout the codebase

## 🎯 Features

- **🎮 Gamified Task Management**: Complete tasks to earn XP and level up your developer profile
- **⌨️ Professional TUI**: Beautiful, modern interface with full keyboard navigation
- **📊 Task Organization**: Categorize tasks by difficulty (Easy/Medium/Hard), priority, and status
- **📈 Progress Tracking**: Monitor your development progress, streaks, and statistics
- **🔍 Search & Filter**: Find tasks quickly with powerful search capabilities
- **💾 Data Persistence**: Automatic save/load of your progress and tasks
- **🏆 Achievement System**: Level-based progression with titles and rewards

## 🏗️ Project Structure

```
dev-leveling/
├── src/                    # Main source code
│   ├── models/            # Data models and enums
│   │   ├── __init__.py
│   │   ├── enums.py       # TaskDifficulty, TaskStatus, Priority
│   │   ├── task.py        # Task data model
│   │   └── player.py      # PlayerData model
│   ├── data/              # Data management
│   │   ├── __init__.py
│   │   └── manager.py     # DataManager class
│   ├── widgets/           # Custom widgets
│   │   ├── __init__.py
│   │   ├── status_indicator.py
│   │   ├── priority_bar.py
│   │   └── task_list_item.py
│   ├── screens/           # UI screens
│   │   ├── __init__.py
│   │   ├── welcome.py     # Welcome screen
│   │   ├── home.py        # Main dashboard
│   │   ├── quests.py      # Quest management
│   │   ├── leveling.py    # Leveling screen
│   │   ├── journal.py     # Activity journal
│   │   ├── add_task.py    # Add task form
│   │   ├── edit_task.py   # Edit task form
│   │   ├── stats.py       # Statistics screen
│   │   ├── search.py      # Search screen
│   │   ├── settings.py    # Settings screen
│   │   ├── help.py        # Help screen
│   │   └── modals.py      # Modal dialogs
│   ├── utils/             # Utilities
│   │   ├── __init__.py
│   │   └── css.py         # CSS styles
│   ├── __init__.py        # Package init
│   └── app.py             # Main application
├── tests/                 # Unit tests
├── docs/                  # Documentation
├── config/                # Configuration files
├── main.py               # Entry point
├── requirements.txt      # Dependencies
└── README.md            # This file
```

## 🛠️ Installation

### Prerequisites
- **Python 3.8 or higher**
- **Terminal with Unicode support** (most modern terminals)
- **Minimum terminal size**: 80x24 characters

### Quick Start

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd dev-leveling
   ```

2. **Create virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

### Troubleshooting
- **Unicode issues**: Ensure your terminal supports UTF-8 encoding
- **Color problems**: Use a terminal with 256-color support
- **Size issues**: Resize terminal to at least 80x24 characters

## 🎮 Usage

### Keyboard Shortcuts

#### Global Shortcuts
- `ESC` - Go back / Exit
- `Ctrl+C` - Quit application
- `?` - Show help screen

#### Home Screen
- `q` - Open Quests screen
- `l` - Open Leveling screen
- `j` - Open Journal screen
- `a` - Add new task
- `ENTER` - Complete selected task

#### Quest Management
- `ENTER` - Complete task
- `e` - Edit task
- `d` - Delete task
- `j/k` - Navigate up/down
- `/` - Search tasks

#### Forms
- `TAB` - Next field
- `Shift+TAB` - Previous field
- `Ctrl+S` - Save
- `Ctrl+C` - Cancel

### Task System

#### Difficulty & XP Rewards
| Difficulty | XP Reward | Description | Examples |
|------------|-----------|-------------|----------|
| Easy       | 15 XP     | Quick fixes, simple tasks | Documentation, small bug fixes |
| Medium     | 30 XP     | Moderate complexity | New features, refactoring |
| Hard       | 50 XP     | Complex problems | Architecture changes, major features |

#### Task Status Flow
```
Pending → Active → Completed
    ↓
  Blocked (can return to Pending/Active)
```

#### Priority Levels
- **Low**: General backlog items
- **Medium**: Standard priority tasks  
- **High**: Important tasks requiring attention
- **Critical**: Urgent items blocking progress

### Leveling System

| Level Range | Title | XP Required |
|-------------|-------|-------------|
| 1-2         | Code Novice | 0-1000 XP |
| 3-4         | Code Student | 1001-4000 XP |
| 5-6         | Code Apprentice | 4001-10000 XP |
| 7-8         | Code Journeyman | 10001-20000 XP |
| 9-10        | Code Expert | 20001-40000 XP |
| 11+         | Code Master | 40000+ XP |

## 🎨 Design Philosoph

### UX Principles
- **Keyboard-First**: All actions accessible via keyboard shortcuts
- **Minimal Clicks**: Efficient workflows with minimal navigation
- **Visual Hierarchy**: Clear information structure and priority indication
- **Responsive Design**: Adapts to different terminal sizes

### Technical Design
- **Component Architecture**: Reusable Textual widgets
- **CSS-like Styling**: Textual's CSS system for consistent theming
- **Rich Text**: Advanced formatting with Rich library integration

### Color Palette

**Base Colors**
```css
--color-bg: #181817;         /* Very dark gray background */
--color-text: #e0e0e0;       /* Main text color */
--color-muted: #9aa0b0;      /* Secondary text */
```

**Main Theme**
```css
--color-dark-blue: #0a1543;  /* Deep navy backgrounds */
--color-mid-blue: #19327f;   /* Muted royal blue accents */
--color-primary: #021fa0;    /* Rich Solo Leveling blue */
--color-accent: #1b45d7;     /* Vibrant accent blue */
```

**Status Colors**
```css
--color-success: #4caf50;    /* Completed tasks, success states */
--color-warning: #ffc107;    /* Warnings, medium priority */
--color-error: #f44336;      /* Errors, high priority */
```

## 🏗️ Technical Architecture

### Core Components

#### Models (`src/models/`)
- **`Task`**: Core task data model with difficulty, priority, and status
- **`Player`**: User progress tracking (XP, level, statistics)
- **`Enums`**: Type-safe enumerations for TaskDifficulty, TaskStatus, Priority

#### Screens (`src/screens/`)
- **Textual Screen classes** for each UI view
- **Reactive components** that update automatically
- **Keyboard shortcuts** and navigation handling

#### Widgets (`src/widgets/`)
- **Custom Textual widgets** for reusable UI components
- **StatusIndicator**: Visual task status display
- **PriorityBar**: Priority level visualization
- **TaskListItem**: Individual task representation

#### Data Management (`src/data/`)
- **DataManager**: Handles JSON persistence and data operations
- **Automatic saving/loading** of tasks and player progress
- **Data validation** and error handling

### Design Patterns
- **Observer Pattern**: Textual's reactive system for UI updates
- **Factory Pattern**: Screen and widget creation
- **Singleton Pattern**: DataManager for consistent state

## 🧪 Development

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=src tests/

# Run specific test file
python -m pytest tests/test_models.py
```

### Code Quality
The project follows modern Python practices:
- **PEP 8** style guidelines
- **Type hints** throughout the codebase
- **Docstrings** for all public methods
- **Enum classes** for type safety
- **Dataclasses** for clean data models

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt pytest pytest-cov

# Run linting (if using)
flake8 src/
mypy src/
```

### Adding New Features

1. **Models**: Add new data models in `src/models/`
   - Inherit from appropriate base classes
   - Add type hints and validation
   
2. **Screens**: Create new screens in `src/screens/`
   - Extend `textual.screen.Screen`
   - Implement compose() method for layout
   
3. **Widgets**: Add custom widgets in `src/widgets/`
   - Extend `textual.widget.Widget`
   - Use reactive attributes for state
   
4. **Data**: Extend data management in `src/data/`
   - Update DataManager for new data types
   - Maintain JSON schema compatibility
