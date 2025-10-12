# Focus Guardian - Quick Start Guide

## 🚀 How to Launch the Application

### **Method 1: Using the Launcher Script (Easiest)**

Simply double-click or run:
```bash
./run_focus_guardian.sh
```

### **Method 2: Terminal Command**

```bash
# Navigate to project directory
cd "/Users/james/Documents/memories ai hackathon"

# Activate virtual environment
source .venv/bin/activate

# Run the application
python -m focus_guardian.main
```

### **Method 3: Background Mode**

To run in background (frees up terminal):
```bash
python -m focus_guardian.main &
```

## 🛑 How to Stop the Application

### **If Running in Foreground:**
- Press `Ctrl+C` in the terminal

### **If Running in Background:**
```bash
# Find the process
ps aux | grep focus_guardian

# Kill it (replace XXXX with the process ID)
kill XXXX
```

### **From the GUI:**
- Click `File → Quit`
- Or just close the window (X button)

## 📝 What You Should See

When launched successfully, you'll see:
```
22:XX:XX | INFO     | focus_guardian | FOCUS GUARDIAN - Starting Application
22:XX:XX | INFO     | focus_guardian.core.config | Configuration loaded
22:XX:XX | INFO     | focus_guardian.core.database | Database initialized
22:XX:XX | INFO     | focus_guardian.ui.main_window | Main window initialized
22:XX:XX | INFO     | focus_guardian | Main window created, entering event loop
```

And a window will appear with:
- Title: "Focus Guardian - ADHD Distraction Analysis"
- Three tabs: Dashboard, Reports, Settings
- Green "Start Focus Session" button

## 🎯 Quick Test

1. **Launch the app** using one of the methods above
2. **Check Settings tab** - you should see:
   - ✓ OpenAI: Configured (green)
   - ✓ Hume AI: Configured (green)
   - ✓ Memories.ai: Configured (green)
3. **Try starting a session**:
   - Click green "Start Focus Session" button
   - Watch the buttons change state
   - Click "Stop Session" to end

## 📂 Project Structure

```
memories ai hackathon/
├── run_focus_guardian.sh    ← Use this to launch!
├── .venv/                    ← Virtual environment
├── src/focus_guardian/       ← Application code
├── data/                     ← Database and sessions
├── config/                   ← Configuration files
└── tests/                    ← Test scripts
```

## 🔧 Troubleshooting

### **"Command not found" error:**
Make sure you're in the project directory:
```bash
cd "/Users/james/Documents/memories ai hackathon"
```

### **"No module named focus_guardian":**
Activate the virtual environment first:
```bash
source .venv/bin/activate
```

### **Camera permission error:**
- Go to **System Settings → Privacy & Security → Camera**
- Enable for **Terminal** or **your IDE**

### **Window doesn't appear:**
Check the terminal for error messages. Most likely:
- PyQt6 not installed: `uv pip install -e .`
- Display issue: Make sure you're not in SSH session

## ✅ Current Status

**Working Features:**
- ✅ GUI launches and displays
- ✅ Button interactions work
- ✅ Tab navigation
- ✅ Menu system
- ✅ Settings show API configuration

**Coming Soon:**
- ⏳ Actual session recording
- ⏳ Real-time distraction detection
- ⏳ Alert notifications
- ⏳ Session reports

## 🆘 Need Help?

If something isn't working:
1. Check terminal output for error messages
2. Make sure all dependencies are installed: `uv pip install -e .`
3. Verify API keys in `.env` file
4. Try running tests: `python tests/test_components.py`

## 🎉 Next Steps

Once the GUI is working:
1. Test all the buttons and tabs
2. Check the Settings tab for API status
3. Ready to continue development with Phase 6 (Session Management)!

