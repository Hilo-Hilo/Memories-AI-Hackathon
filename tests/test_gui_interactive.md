# Focus Guardian GUI - Interactive Test Guide

## ✅ GUI Test Checklist

### **Window & Layout**
- [ ] Main window visible with title "Focus Guardian - ADHD Distraction Analysis"
- [ ] Window has minimum size of 900x600
- [ ] Three tabs visible: Dashboard, Reports, Settings

### **Dashboard Tab**
- [ ] "Focus Session Dashboard" header displayed
- [ ] Session status shows "No active session"
- [ ] Timer displays "00:00:00"
- [ ] Task label shows "Task: None"
- [ ] Three control buttons visible:
  - [ ] Green "Start Focus Session" button (enabled)
  - [ ] Orange "Pause" button (disabled/grayed out)
  - [ ] Red "Stop Session" button (disabled/grayed out)
- [ ] Session statistics displayed (Snapshots: 0, Distractions: 0, Focus: 0%)

### **Interactive Tests**

#### Test 1: Start Session Button
1. Click the green "Start Focus Session" button
2. Expected results:
   - [ ] Button becomes disabled (grayed out)
   - [ ] "Pause" button becomes enabled (orange)
   - [ ] "Stop Session" button becomes enabled (red)
   - [ ] Session status changes to "Session Active"
   - [ ] Task label shows "Task: Focus Work"
   - [ ] Status bar at bottom shows "Focus session started"

#### Test 2: Pause/Resume
1. After starting session, click orange "Pause" button
2. Expected results:
   - [ ] Button text changes to "Resume"
   - [ ] Status bar shows "Session paused"
3. Click "Resume" button
4. Expected results:
   - [ ] Button text changes back to "Pause"
   - [ ] Status bar shows "Session resumed"

#### Test 3: Stop Session
1. Click red "Stop Session" button
2. Expected results:
   - [ ] Confirmation dialog appears: "Are you sure you want to stop the current session?"
   - [ ] Two options: "Yes" and "No"
3. Click "Yes"
4. Expected results:
   - [ ] Session status returns to "No active session"
   - [ ] Timer resets to "00:00:00"
   - [ ] Task returns to "Task: None"
   - [ ] "Start" button re-enabled, "Pause" and "Stop" disabled
   - [ ] Status bar shows "Session stopped"

#### Test 4: Stop Session (Cancel)
1. Start a session again
2. Click "Stop Session" button
3. In the confirmation dialog, click "No"
4. Expected results:
   - [ ] Dialog closes
   - [ ] Session continues running
   - [ ] No changes to session state

### **Reports Tab**
- [ ] "Session Reports" header visible
- [ ] Placeholder text: "Session history will appear here"

### **Settings Tab**
- [ ] "Settings" header visible
- [ ] "API Configuration" section visible
- [ ] Three API status lines:
  - [ ] OpenAI: ✓ Configured (green) or ✗ Not configured (red)
  - [ ] Hume AI: ✓ Configured (green) or ✗ Not configured (red)  
  - [ ] Memories.ai: ✓ Configured (green) or ✗ Not configured (red)

### **Menu Bar**
- [ ] "File" menu contains:
  - [ ] "New Session" option
  - [ ] Separator line
  - [ ] "Quit" option
- [ ] "Help" menu contains:
  - [ ] "About" option

#### Test 5: About Dialog
1. Click "Help" → "About"
2. Expected results:
   - [ ] Dialog appears with title "About Focus Guardian"
   - [ ] Shows: "Focus Guardian v0.1.0"
   - [ ] Shows description about ADHD distraction analysis
   - [ ] Shows: "Snapshot-based AI detection with K=3 hysteresis voting"
   - [ ] Shows: "© 2025 Focus Guardian Team"

#### Test 6: Quit from Menu
1. Click "File" → "Quit"
2. Expected results:
   - [ ] If session active: Confirmation dialog appears
   - [ ] If no session: Application quits immediately

#### Test 7: Window Close Button
1. Start a session
2. Click the window close button (X)
3. Expected results:
   - [ ] Confirmation dialog: "A session is active. Are you sure you want to quit?"
   - [ ] Options: "Yes" and "No"
4. Click "No"
5. Expected results:
   - [ ] Window stays open
   - [ ] Session continues
6. Try closing again, click "Yes"
7. Expected results:
   - [ ] Application quits

### **Status Bar**
- [ ] Status bar visible at bottom of window
- [ ] Shows current status messages:
  - [ ] "Ready" when idle
  - [ ] "Focus session started" when starting
  - [ ] "Session paused" when paused
  - [ ] "Session resumed" when resumed
  - [ ] "Session stopped" when stopped

## 🎨 **Visual Appearance Check**

### Colors
- [ ] Start button: Green (#27ae60)
- [ ] Pause button: Orange (#f39c12)
- [ ] Stop button: Red (#e74c3c)
- [ ] Disabled buttons: Gray (#95a5a6)
- [ ] Session info box: Light gray background (#ecf0f1)
- [ ] Timer: Blue (#3498db)

### Fonts
- [ ] Main header: 24px, bold
- [ ] Timer: 48px, bold
- [ ] Buttons: 16px, bold
- [ ] Session status: 18px
- [ ] Task label: 16px

### Layout
- [ ] Elements are centered properly
- [ ] Adequate spacing between elements
- [ ] Buttons are same size
- [ ] No visual glitches or overlapping text

## 🐛 **Known Issues (To Fix)**

- [ ] Timer doesn't actually count (placeholder - needs session manager integration)
- [ ] Statistics don't update (needs database queries)
- [ ] No task input dialog yet (uses hardcoded "Focus Work")
- [ ] Alert overlays not implemented yet
- [ ] System tray icon disabled (no icon file)
- [ ] Session doesn't actually start recording (needs session manager)

## ✅ **What Should Work**

✓ Window launches and displays properly
✓ UI is responsive and interactive
✓ Buttons change state correctly
✓ Tabs can be switched
✓ Menu items are accessible
✓ Dialogs appear correctly
✓ Status bar updates
✓ Settings show API configuration status
✓ Visual styling is professional and clean

## 🚀 **Next Steps After Testing**

If GUI looks good:
1. Integrate session manager (Phase 6)
2. Add alert overlay components
3. Implement task input dialog
4. Connect timer to actual session time
5. Wire up database for real-time stats

