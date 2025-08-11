# Terminal UI Redesign - Design Document

## Overview

This design document outlines the complete transformation of the QUESTA task management application from its current Textual-based interface to a terminal-inspired, retro computing aesthetic. The redesign maintains all existing functionality while creating an immersive, game-like experience that aligns with the quest/RPG theme.

The new interface will feature a dark blue color scheme reminiscent of classic terminal interfaces, with monospace fonts, ASCII-style graphics, and a command-line inspired navigation system. All screens will be redesigned to match the terminal aesthetic while preserving the underlying data models and business logic.

## Architecture

### UI Framework
- **Current**: Textual TUI framework with CSS-like styling
- **New**: Enhanced Textual implementation with terminal-specific styling and custom widgets
- **Approach**: Modify existing screens and create new terminal-themed widgets while maintaining the same underlying architecture

### Screen Architecture
The application will maintain its current screen-based architecture but with completely redesigned interfaces:

1. **WelcomeScreen**: New splash screen with QUESTA logo and player stats
2. **JournalScreen**: New activity journal replacing parts of current home functionality  
3. **NewQuestScreen**: Enhanced task creation with terminal-style forms
4. **CharacterStatsScreen**: New dedicated stats and achievements screen
5. **AllQuestsScreen**: Enhanced quest management with filtering
6. **DashboardScreen**: New focused dashboard for active work

### Navigation System
- Terminal-style command navigation (`:back`, `:quit`, `:help`, etc.)
- Keyboard shortcuts consistent with terminal interfaces
- Tab-based navigation between numbered screens (1-6 as shown in mockups)
- Bottom status bar with available commands

## Components and Interfaces

### Color Scheme
```python
TERMINAL_COLORS = {
    'background': '#0a1543',      # Dark blue background
    'surface': '#181817',         # Slightly lighter surface
    'primary': '#1b45d7',         # Bright blue for headers/accents
    'secondary': '#19327f',       # Medium blue for highlights
    'text': '#e0e0e0',           # Light gray text
    'text_muted': '#9aa0b0',     # Muted text
    'accent_yellow': '#ffc107',   # Yellow for XP/rewards
    'accent_green': '#4caf50',    # Green for completed items
    'accent_red': '#f44336',      # Red for high priority/errors
    'border': '#3a3a3a'          # Border color
}
```

### Typography
- **Primary Font**: Monospace fonts (Courier New, Monaco, Consolas)
- **Logo**: Large ASCII-style block letters for "QUESTA"
- **Headers**: Bold monospace with terminal-style formatting
- **Body Text**: Regular monospace with consistent spacing

### Core Widget Components

#### TerminalHeader
Custom header widget displaying:
- Application title in terminal format: "QUESTA - [Screen Name]"
- User context in top-right corner
- Tab navigation indicators (numbered 1-6)

#### TerminalFooter  
Custom footer widget showing:
- Available commands (`:back`, `:navigate`, `:help`, etc.)
- Current status information
- Navigation shortcuts

#### TerminalPanel
Reusable panel component with:
- Terminal-style borders using ASCII characters
- Header with panel title
- Scrollable content area
- Consistent padding and spacing

#### ProgressBarTerminal
Custom progress bar with:
- ASCII-style progress indicators
- Terminal color scheme
- XP/level progression display

#### TaskListTerminal
Enhanced task list component featuring:
- Priority indicators using colored symbols
- XP values prominently displayed
- Terminal-style selection highlighting
- Difficulty badges with appropriate colors

### Screen Components

#### WelcomeScreen Components
- **QUESTALogo**: Large ASCII art logo
- **PlayerLevelDisplay**: Current level and title
- **XPProgressBar**: Progress towards next level
- **ContinuePrompt**: "Press [Enter] to continue" instruction

#### JournalScreen Components
- **ActivityTimeline**: Chronological activity display
- **DailyActivityGroup**: Grouped activities by date
- **ActivityItem**: Individual task/achievement entries
- **AchievementBadge**: Special formatting for unlocked achievements

#### NewQuestScreen Components
- **QuestForm**: Terminal-style form with labeled fields
- **DifficultySelector**: Dropdown with XP values
- **CategorySelector**: Predefined categories
- **PrioritySelector**: Priority level selection
- **TagsInput**: Space-separated tags input
- **DescriptionArea**: Multi-line text area for quest details

#### CharacterStatsScreen Components
- **LevelProgressPanel**: Current level and XP progress
- **AchievementGrid**: Grid layout for badges/achievements
- **StatisticsPanel**: Completed tasks, streaks, etc.
- **LevelProgressionList**: All levels with requirements

#### AllQuestsScreen Components
- **QuestFilterTabs**: Filter options (Today, All, Completed, By Tag)
- **QuestListPanel**: Scrollable quest list
- **QuestDetailPanel**: Detailed quest information
- **ActionButtons**: Complete, Edit, Delete actions

#### DashboardScreen Components
- **TodayQuestsSidebar**: Today's active quests
- **QuestDetailMain**: Selected quest details
- **StreakIndicator**: Current streak display
- **QuickActions**: Common action buttons

## Data Models

### Existing Models (No Changes Required)
The current data models will remain unchanged:
- **Task**: Core task model with all current properties
- **PlayerData**: Player statistics and progression
- **TaskDifficulty**: Difficulty levels with XP values
- **TaskPriority**: Priority levels
- **TaskStatus**: Task status states

### New Display Models
Additional models for terminal-specific display:

#### TerminalTheme
```python
@dataclass
class TerminalTheme:
    colors: Dict[str, str]
    fonts: Dict[str, str]
    ascii_chars: Dict[str, str]
    spacing: Dict[str, int]
```

#### ActivityEntry
```python
@dataclass
class ActivityEntry:
    date: datetime
    type: str  # 'task_completed', 'level_up', 'achievement'
    description: str
    xp_earned: int
    metadata: Dict[str, Any]
```

## Error Handling

### Terminal-Specific Error Display
- Error messages displayed in terminal-style format
- Red text on dark background for visibility
- ASCII borders around error dialogs
- Command-line style error codes and descriptions

### Input Validation
- Real-time validation feedback in terminal style
- Field-specific error messages below inputs
- Form validation summary at bottom of forms
- Clear indication of required vs optional fields

### Recovery Mechanisms
- Graceful fallback to previous screen on errors
- Auto-save functionality for form data
- Session recovery on application restart
- Data integrity checks with user notification

## Testing Strategy

### Visual Testing
- Screenshot comparison tests for each screen
- Color scheme consistency verification
- Font rendering tests across platforms
- ASCII art rendering validation

### Interaction Testing
- Keyboard navigation testing
- Command parsing and execution
- Screen transition testing
- Form submission and validation

### Accessibility Testing
- High contrast mode compatibility
- Screen reader compatibility for terminal interfaces
- Keyboard-only navigation testing
- Color-blind friendly color scheme validation

### Performance Testing
- Screen rendering performance
- Large task list handling
- Memory usage optimization
- Startup time measurement

### Integration Testing
- Data persistence across screen changes
- Player progression calculation accuracy
- Task completion workflow testing
- Achievement unlock verification

## Implementation Approach

### Phase 1: Core Terminal Infrastructure
1. Create terminal color scheme and theme system
2. Implement base terminal widgets (header, footer, panels)
3. Set up ASCII art and typography system
4. Create terminal-specific styling framework

### Phase 2: Screen Redesign
1. Implement WelcomeScreen with QUESTA logo
2. Create JournalScreen for activity tracking
3. Redesign NewQuestScreen with terminal forms
4. Build CharacterStatsScreen with achievements
5. Enhance AllQuestsScreen with filtering
6. Create DashboardScreen for focused work

### Phase 3: Navigation and Commands
1. Implement terminal-style command system
2. Add keyboard shortcuts and navigation
3. Create help system and command documentation
4. Add screen transition animations

### Phase 4: Polish and Optimization
1. Fine-tune visual consistency
2. Optimize performance for large datasets
3. Add accessibility features
4. Comprehensive testing and bug fixes

## Technical Considerations

### Textual Framework Enhancements
- Custom CSS for terminal aesthetics
- Extended widget classes for terminal behavior
- Enhanced keyboard handling for command input
- Custom rendering for ASCII art and special characters

### Data Flow
- Maintain existing DataManager interface
- Add terminal-specific display formatting
- Implement activity logging for journal
- Cache frequently accessed display data

### Configuration
- Terminal theme configuration file
- User preference storage for display options
- Customizable keyboard shortcuts
- Screen layout preferences

### Cross-Platform Compatibility
- Font fallback system for different platforms
- Color scheme adaptation for different terminals
- Unicode character support verification
- Platform-specific keyboard handling