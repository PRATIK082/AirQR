# AirQR Direct-Run Framework

This folder provides a **direct-run** layer for PC and mobile **without modifying the core codebase**.

## PC (direct run)
- Windows: double-click `pc\launch_sender.bat` / `pc\launch_receiver.bat`
- macOS/Linux: `bash pc/launch_sender.sh` / `bash pc/launch_receiver.sh`
- Or run directly:
  - `py airqr send <source>`
  - `py airqr receive --dest ./received`

## Mobile (direct run)
1. On PC, start the framework server:
   ```
   python framework/run.py
   ```
2. On the phone (same network for first load), open `http://<PC-IP>:8765/index.html` in Chrome.
3. Tap browser menu → **Add to Home screen** to install as an app.
4. After first load it works offline (PWA).
5. Use the web receiver (Enable Camera) to scan the PC screen.

## Notes
- Mobile web receiver supports uncompressed transfers; use `py airqr send <source> --web` on PC for compatibility.
- Native mobile apps are on the roadmap (see PLAN.md); this framework uses the web PWA for direct mobile run.
- This framework only wraps/exposes existing functionality; core code under `core/`, `sender.py`, `receiver.py` is untouched.
