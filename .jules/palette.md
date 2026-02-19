## 2024-05-23 - The Void Stares Back
**Learning:** Users lose confidence when "File Mode" shows an empty preview while "Paste Mode" shows content. Empty states should preemptively load context.
**Action:** Always populate preview widgets with selected file content immediately. Empty space is wasted space.

## 2024-05-23 - The Scrollbar Fallacy
**Learning:** Fixed pixel/line heights in TUIs force users to resize their terminal/font, breaking accessibility. A 10-line log area on a 24-line screen is a design failure.
**Action:** Use percentages (`20%`) and constrained weights (`min/max-height`) for secondary UI elements. Compact vertical padding is crucial for CLI tools.

## 2024-05-24 - The Invisible Shortcuts
**Learning:** Textual apps define key bindings in code but hide them from users unless a `Footer` widget is explicitly yielded. This makes keyboard navigation undiscoverable.
**Action:** Always yield `Footer()` in the `compose` method for any screen with `BINDINGS` to ensure accessibility.

## 2024-05-24 - The Misleading Welcome
**Learning:** Showing a generic welcome screen when a user enters an invalid path creates confusion. Specific error states build trust.
**Action:** Distinguish between "initial state" (empty) and "error state" (invalid input) in previews.

## 2024-05-24 - The Silent Footer
**Learning:** Textual `BINDINGS` without explicit descriptions default to raw action names in the `Footer`, confusing users with internal terminology.
**Action:** Always provide the 3rd argument (description) in `Binding` definitions to ensure user-friendly labels.

## 2024-05-25 - The Frozen Interface Fallacy
**Learning:** Users interpret a lack of immediate visual feedback during long-running operations as a system freeze or ignored input, leading to repeated clicks.
**Action:** Always toggle button states (disable/label change) at the start of an async operation and restore them in a `finally` block to ensure resilience.
