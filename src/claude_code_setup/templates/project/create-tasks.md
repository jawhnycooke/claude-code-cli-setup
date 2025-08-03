Ultrathink and create parallel subagents to break down and plan the following goal into manageable tasks:

$ARGUMENTS

Have one subagent focus on high-level project structure, one on technical implementation details, one on timeline/dependencies, and one on potential risks and mitigations. Then synthesize their findings into a comprehensive TASKS.md file.

Follow these steps:
1. Create four parallel subagents to analyze different aspects of the goal:
   - Architecture Subagent: Identify major components and their relationships
   - Implementation Subagent: Break down technical implementation details
   - Planning Subagent: Establish timeline and task dependencies
   - Risk Subagent: Identify potential challenges and mitigations

2. Have each subagent independently generate their part of the plan

3. Synthesize their outputs into a structured TASKS.md with:
   - A heading with the goal statement
   - A progress summary showing percentage complete
   - Organized task sections with proper Markdown formatting
   - A legend explaining status indicators
   - Dependencies between tasks clearly marked

4. For each task, include:
   - A clear description
   - Estimated completion date
   - Status indicator (NOT_STARTED, IN_PROGRESS, COMPLETED)
   - Dependencies on other tasks (if applicable)

5. Verify the tasks collectively achieve the stated goal and address identified risks

Use the following status indicators:
- [ ] NOT_STARTED
- [~] IN_PROGRESS
- [x] COMPLETED

Include at least 10-15 tasks, depending on the complexity of the goal, ensuring comprehensive coverage.
