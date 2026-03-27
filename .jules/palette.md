## 2024-05-24 - Dynamic Tooltips on Multi-State Buttons
**Learning:** In Textual TUIs, when a button's function changes dynamically (e.g., toggling between preview and edit modes), its `tooltip` property should be updated dynamically alongside its `label` and `variant` to maintain accurate accessibility context. Stale tooltips on stateful buttons create confusing UX.
**Action:** Always verify if a button's primary action changes during the application lifecycle. If it does, ensure the tooltip is updated in the corresponding event handlers.
