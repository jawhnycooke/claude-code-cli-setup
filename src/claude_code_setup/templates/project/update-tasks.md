Think hard and use independent subagents to verify the updated status of tasks in the TASKS.md file.

Follow these steps:
1. Read the current TASKS.md file
2. Create a verification subagent to analyze the codebase to determine:
   - Which tasks have been completed
   - Which tasks are in progress
   - Which tasks haven't been started
3. Have the verification subagent provide evidence for each task status change
4. Update status indicators for each task:
   - [ ] NOT_STARTED
   - [~] IN_PROGRESS
   - [x] COMPLETED
5. Recalculate the overall project completion percentage
6. Update the progress summary at the top of the file
7. Write the updated content back to TASKS.md
8. Summarize what's been completed and what remains to be done

If tasks have changed significantly or new tasks have emerged, use another subagent to analyze the changes and integrate them into the task list with proper status indicators and descriptions.
