# Implementation Plan

- [x] 1. Create terminal theme system and base styling
  - Implement TerminalTheme class with color scheme, fonts, and ASCII characters
  - Create terminal-specific CSS styling that overrides current styles
  - Add ASCII art generation utilities for logos and borders
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Build core terminal widget components
  - [x] 2.1 Create TerminalHeader widget with QUESTA branding
    - Implement custom header showing "QUESTA - [Screen Name]" format
    - Add user context display in top-right corner
    - Include tab navigation indicators (numbered 1-6)
    - _Requirements: 8.4_

  - [x] 2.2 Create TerminalFooter widget with command navigation
    - Implement footer showing available commands (:back, :navigate, :help, etc.)
    - Add current status information display
    - Include navigation shortcuts and help text
    - _Requirements: 8.1, 8.2, 8.3_

  - [x] 2.3 Create TerminalPanel reusable component
    - Implement panel with ASCII-style borders
    - Add header with panel title functionality
    - Create scrollable content area with consistent padding
    - _Requirements: 1.1, 1.2_

- [x] 3. Implement WelcomeScreen with terminal splash interface
  - Create large ASCII art QUESTA logo display
  - Add player level and title display (e.g., "Level 5 - Code Apprentice")
  - Implement XP progress bar with terminal styling
  - Add "Press [Enter] to continue" instruction
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 4. Create JournalScreen for activity tracking
  - [x] 4.1 Implement activity timeline with chronological display
    - Create ActivityEntry model for journal entries
    - Build timeline widget showing activities grouped by date
    - Display date, day of week, total XP earned, and quest count
    - _Requirements: 3.1, 3.2_

  - [x] 4.2 Add individual activity item rendering
    - Show difficulty level, task description, and XP earned for each task
    - Implement special formatting for achievements with badge indicators
    - Display level up notifications prominently
    - _Requirements: 3.3, 3.4, 3.5_

- [x] 5. Build NewQuestScreen with terminal-style forms
  - [x] 5.1 Create quest form with terminal input fields
    - Implement form fields for title, difficulty, category, files/paths, tags
    - Add estimated time, priority, and description input areas
    - Use terminal-styled dropdowns and text inputs
    - _Requirements: 4.1, 4.3_

  - [x] 5.2 Add difficulty and priority selection with XP display
    - Show XP values for each difficulty level in dropdown
    - Implement priority selection with visual indicators
    - Display calculated XP reward at bottom of form
    - _Requirements: 4.2, 4.5_

  - [x] 5.3 Implement multi-line description area with acceptance criteria
    - Create expandable text area for quest description
    - Add dedicated section for acceptance criteria
    - Include form validation and error display
    - _Requirements: 4.4_

- [x] 6. Create CharacterStatsScreen with achievements and progression
  - [x] 6.1 Implement level progress panel
    - Display current level progress with terminal-style XP bar
    - Show XP needed for next level and current level title
    - Add visual progress indicator with percentage
    - _Requirements: 5.1, 5.4_

  - [x] 6.2 Build achievements grid with badge display
    - Create grid layout for earned badges with titles and descriptions
    - Show locked badges in dimmed state with unlock requirements
    - Implement badge categories and filtering
    - _Requirements: 5.2, 5.5_

  - [x] 6.3 Add statistics panel with player metrics
    - Display completed tasks, total XP, current streak, and bugs fixed
    - Show task completion breakdown by difficulty
    - Add historical statistics and trends
    - _Requirements: 5.3_

- [x] 7. Enhance AllQuestsScreen with filtering and detailed view
  - [x] 7.1 Create quest list with priority indicators and XP values
    - Display tasks in terminal-styled list with color-coded priorities
    - Show XP values prominently for each quest
    - Add visual indicators for quest status and difficulty
    - _Requirements: 6.1_

  - [x] 7.2 Implement filtering system with tabs
    - Add filter tabs for Today, All, Completed, and By Tag
    - Create dynamic filtering logic for quest display
    - Implement tag-based filtering with search functionality
    - _Requirements: 6.2_

  - [x] 7.3 Build detailed quest view panel
    - Show comprehensive quest information including tags, time estimates, dependencies
    - Display assignee, notes, and creation history
    - Add action buttons for Complete, Edit, and Delete operations
    - _Requirements: 6.3, 6.4, 6.5_

- [-] 8. Create DashboardScreen for focused daily work
  - [x] 8.1 Implement today's quests sidebar
    - Display today's active quests with priority indicators
    - Show quest titles, XP values, and status
    - Add quick selection and navigation
    - _Requirements: 7.1_

  - [x] 8.2 Build main quest details panel
    - Show selected quest details including difficulty, file paths, dates
    - Display priority, status, and comprehensive description
    - Format acceptance criteria as bulleted list
    - _Requirements: 7.2, 7.3, 7.4_

  - [ ] 8.3 Add streak indicator and quick actions
    - Display current streak information prominently
    - Add quick action buttons for common operations
    - Show daily progress and motivation elements
    - _Requirements: 7.5_

- [ ] 9. Implement terminal-style navigation and command system
  - [ ] 9.1 Create command parser for terminal navigation
    - Implement command parsing for :back, :navigate, :help, :quit commands
    - Add keyboard shortcut handling for terminal-style navigation
    - Create help system showing available commands
    - _Requirements: 8.1, 8.2, 8.3_

  - [ ] 9.2 Add screen transition system
    - Implement smooth transitions between screens
    - Add screen history for back navigation
    - Create consistent screen title formatting
    - _Requirements: 8.4, 8.5_

- [ ] 10. Update main application with new screen integration
  - [ ] 10.1 Modify QUESTAApp to use new terminal screens
    - Replace existing screens with new terminal-styled versions
    - Update screen routing and navigation logic
    - Integrate new welcome screen as entry point
    - _Requirements: 1.1, 2.1, 8.4_

  - [ ] 10.2 Update CSS with complete terminal styling
    - Replace existing CSS with terminal color scheme
    - Add monospace font specifications and terminal aesthetics
    - Implement responsive design for different terminal sizes
    - _Requirements: 1.1, 1.2, 1.3_

- [ ] 11. Add comprehensive testing for terminal interface
  - [ ] 11.1 Create visual regression tests for each screen
    - Test ASCII art rendering and layout consistency
    - Verify color scheme application across all components
    - Validate font rendering and spacing
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [ ] 11.2 Implement interaction testing for terminal navigation
    - Test keyboard shortcuts and command parsing
    - Verify screen transitions and navigation flow
    - Test form submission and validation in terminal style
    - _Requirements: 8.1, 8.2, 8.3_

- [ ] 12. Polish and optimize terminal interface
  - [ ] 12.1 Fine-tune visual consistency and performance
    - Optimize rendering performance for large task lists
    - Ensure consistent spacing and alignment across screens
    - Add loading indicators and smooth animations
    - _Requirements: 1.1, 1.2_

  - [ ] 12.2 Add accessibility features and error handling
    - Implement high contrast mode support
    - Add keyboard-only navigation testing
    - Create graceful error handling with terminal-style messages
    - _Requirements: 8.1, 8.2_