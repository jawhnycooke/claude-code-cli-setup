Ultrathink and use parallel subagents to analyze and fix GitHub issue #$ARGUMENTS using the following approach:

1. Create four specialized subagents to work in parallel:
   - Analysis Subagent: Deeply understand the issue description and identify root causes
   - Implementation Subagent: Draft implementation solutions
   - Testing Subagent: Design test cases to verify the fix
   - Review Subagent: Evaluate proposed solutions for side effects

2. Have the Analysis Subagent:
   - Review the issue description using 'gh issue view $ARGUMENTS'
   - Identify affected files and code paths
   - Determine the root cause of the issue

3. Have the Implementation Subagent:
   - Propose multiple potential solutions
   - Evaluate tradeoffs between approaches
   - Draft code changes for the optimal solution

4. Have the Testing Subagent:
   - Create test cases that verify the fix
   - Consider edge cases that might be affected
   - Ensure regression tests are in place

5. Have the Review Subagent:
   - Identify potential side effects or performance implications
   - Check for adherence to project coding standards
   - Ensure backward compatibility

6. Synthesize the findings of all subagents into an integrated solution:
   - Implement the fix with comprehensive comments
   - Add or update tests to validate the fix
   - Ensure all tests pass
   - Create a descriptive commit message that references the issue

7. Present a summary of what was fixed, how it was fixed, and why the chosen approach was selected
