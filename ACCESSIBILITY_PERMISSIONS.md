# macOS Accessibility Permissions Required

The "Close frontmost app after two distractions" feature requires macOS Accessibility permissions to work.

## Why?

This feature uses AppleScript to:
1. **Get the frontmost application** (what app you're currently using)
2. **Close that application** after detecting two consecutive distractions

macOS blocks these operations for security unless the app has Accessibility permissions.

## How to Grant Permissions

### Step 1: Open System Settings
1. Click the Apple menu (🍎) in the top-left corner
2. Select **"System Settings"** (on macOS Ventura+) or **"System Preferences"** (on older macOS)

### Step 2: Navigate to Privacy Settings
1. Click **"Privacy & Security"** (or **"Security & Privacy"**)
2. Scroll down and click **"Accessibility"** (or **"Privacy"** → **"Accessibility"**)

### Step 3: Add Focus Guardian
1. Look for the lock icon 🔒 at the bottom-left
2. Click it and enter your password to make changes
3. Click the **"+"** button to add an application
4. Navigate to where you installed Focus Guardian
   - If running from source: look for `/Users/yourname/.local/bin/python` or your virtual environment's Python
   - Or add your Terminal app if running directly from terminal
5. Enable the checkbox next to Focus Guardian/Python/Terminal

### Step 4: Verify
- The checkbox should be checked ✅
- Restart the Focus Guardian application

## Alternative: Grant Permissions to Terminal

If you're running Focus Guardian from Terminal, you can grant permissions to Terminal instead:

1. Follow Steps 1-3 above
2. Add **Terminal** (or **iTerm**, **VSCode terminal**, etc.) instead of Python
3. This will allow any script run from that terminal to control other apps

## Testing Permissions

Run this command in Terminal to test:

```bash
osascript -e 'tell application "System Events" to get name of first process whose frontmost is true'
```

If it returns an app name (e.g., "Safari", "Chrome"), permissions are working! ✅

If you see an error about "not allowed assistive" or similar, permissions are not granted. ❌

## Troubleshooting

### "not allowed assistive" error
- Go to System Settings → Privacy & Security → Accessibility
- Make sure Focus Guardian, Python, or Terminal is listed and enabled
- Try restarting the application

### Still not working?
- Make sure you're using a recent version of macOS
- Some corporate/managed Macs may have additional restrictions
- Try running from Terminal with `./run_focus_guardian.sh` to see detailed logs

## What If I Don't Grant Permissions?

The app will still work for all other features, but:
- The "close app" feature will be disabled
- You'll see a log message: "macOS Accessibility permissions required!"
- Distraction detection and alerts will still work normally

## Security Note

These permissions give the application the ability to control other apps on your system. Focus Guardian only uses this power for the agentic close feature, which you explicitly enable in Settings. The app never uses these permissions for anything else.

