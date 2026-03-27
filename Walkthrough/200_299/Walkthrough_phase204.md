# Phase 204 Walkthrough

Lead query rows already returned `display_name`, but the AI Agent table renderer ignored that field and only tried `first_name + last_name`. Query result rows do not include those separate fields, so the Name column rendered `-`.

The renderer now prefers `row.display_name` first. For leads, the AI Agent table will show the concatenated full name that the backend query already provides.
