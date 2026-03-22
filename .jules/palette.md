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

## 2025-03-04 - Native Button Loading State in Textual
**Learning:** Textual `Button` natively supports a `loading` property that replaces the button's label with a visual spinner. This provides immediate, built-in visual feedback for blocking async tasks (like PDF/DOCX generation via Playwright) without needing custom state management or extra widgets.
**Action:** Always check if a widget has native properties (like `loading` or `tooltip`) to implement accessibility/UX feedback natively before building custom solutions. For background thread operations, always toggle this state using `self.call_from_thread` inside a `try...finally` block.

## 2024-05-23 - Async Button Feedback in Textual
**Learning:** Textual buttons natively support a `loading` property, but setting it during long-running background tasks (like Playwright renders) must be carefully guarded. If a conditionally rendered button (like `#tui-render-btn` which requires `HAS_PIXELS`) is manipulated via `query_one` inside an async worker's `call_from_thread` block, it can raise a `NoMatches` exception if the button is absent. This causes silent worker crashes and missing `finally` state cleanup.
**Action:** When connecting a button's native `loading` state to background async logic, always wrap the `query_one` mutation in a local `try/except Exception` block before calling it via `self.call_from_thread(lambda: set_loading(True))` to safely swallow unmounted-widget errors.
