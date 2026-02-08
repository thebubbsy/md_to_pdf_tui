## 2024-05-23 - The Void Stares Back
**Learning:** Users lose confidence when "File Mode" shows an empty preview while "Paste Mode" shows content. Empty states should preemptively load context.
**Action:** Always populate preview widgets with selected file content immediately. Empty space is wasted space.

## 2024-05-23 - The Scrollbar Fallacy
**Learning:** Fixed pixel/line heights in TUIs force users to resize their terminal/font, breaking accessibility. A 10-line log area on a 24-line screen is a design failure.
**Action:** Use percentages (`20%`) and constrained weights (`min/max-height`) for secondary UI elements. Compact vertical padding is crucial for CLI tools.

## 2026-02-07 - The Phantom Bindings
**Learning:** Defining `BINDINGS` in Textual without corresponding `action_*` methods creates a "phantom UI" where shortcuts are advertised but do nothing. This erodes trust.
**Action:** Always verify that every key binding has a matching `action_` method, and use the 3-tuple format `(key, action, description)` to ensure visibility in the Footer.
