# Project Documentation Generator

Analyze the codebase at $ARGUMENTS to create comprehensive, factual documentation that accurately describes the project as it exists today.

Write documentation in a clear narrative style without bullet points or embellishments. Focus on explaining what the code does, how it's structured, and how to use it effectively.

Structure the documentation as follows:

1. Begin with a README.md that includes:
   - Project name and concise description
   - Purpose and key functionality
   - Main technologies used
   - Basic usage instructions

2. Create an ARCHITECTURE.md that describes:
   - Overall system design and organization
   - Component relationships and interactions
   - Data flow through the system
   - Include Mermaid diagrams to illustrate architecture where helpful

3. Create a SETUP.md with:
   - Prerequisites and dependencies
   - Installation process
   - Configuration options
   - Environment setup

4. Create a USAGE.md with:
   - Common use cases
   - Code examples demonstrating key functionality
   - Options and parameters

For each document:
- Use a factual, straightforward tone
- Avoid speculation about future features
- Document only what is present in the code
- Present information in paragraph form rather than lists when possible
- Use code snippets to illustrate actual usage
- Use Mermaid diagrams when helpful to illustrate concepts

Adapt documentation based on what's actually in the project - if there are no APIs, don't create API documentation. If the project is simple, consolidate into fewer documents as appropriate.