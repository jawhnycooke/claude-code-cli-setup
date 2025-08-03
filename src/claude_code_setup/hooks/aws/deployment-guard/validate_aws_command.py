#!/usr/bin/env python3
import json
import os
import re
import sys


def validate_aws_operation(command: str) -> dict[str, str]:
    """Validate AWS operations for safety."""

    # Check for production operations
    prod_keywords = ["production", "prod", "prd", "live"]
    if any(keyword in command.lower() for keyword in prod_keywords):
        if os.environ.get("ALLOW_PRODUCTION", "false").lower() != "true":
            return {
                "decision": "block",
                "reason": "Production operations require manual approval. Set ALLOW_PRODUCTION=true to allow.",
            }

    # Dangerous AWS operations
    dangerous_operations = [
        (r"aws\s+.*\s+delete", "delete operation"),
        (r"aws\s+.*\s+terminate", "terminate operation"),
        (r"aws\s+.*\s+remove", "remove operation"),
        (r"aws\s+cloudformation\s+delete-stack", "stack deletion"),
        (r"aws\s+s3\s+rb", "S3 bucket removal"),
        (r"aws\s+rds\s+delete-db", "RDS database deletion"),
        (r"aws\s+dynamodb\s+delete-table", "DynamoDB table deletion"),
        (r"aws\s+iam\s+delete", "IAM resource deletion"),
        (r"terraform\s+destroy", "Terraform destroy"),
        (r"cdk\s+destroy", "CDK destroy"),
        (r"sam\s+delete", "SAM delete"),
    ]

    for pattern, operation in dangerous_operations:
        if re.search(pattern, command, re.IGNORECASE):
            return {
                "decision": "block",
                "reason": f"Dangerous AWS operation detected: {operation}. This operation must be run manually.",
            }

    # Validate Lambda resource limits for junior developers
    if "lambda create-function" in command or "lambda update-function" in command:
        # Check memory size
        memory_match = re.search(r"--memory-size\s+(\d+)", command)
        if memory_match:
            memory = int(memory_match.group(1))
            max_memory = int(os.environ.get("MAX_LAMBDA_MEMORY", "1024"))
            if memory > max_memory:
                return {
                    "decision": "block",
                    "reason": f"Lambda memory exceeds limit ({memory}MB > {max_memory}MB). Adjust MAX_LAMBDA_MEMORY to increase.",
                }

        # Check timeout
        timeout_match = re.search(r"--timeout\s+(\d+)", command)
        if timeout_match:
            timeout = int(timeout_match.group(1))
            max_timeout = int(os.environ.get("MAX_LAMBDA_TIMEOUT", "300"))
            if timeout > max_timeout:
                return {
                    "decision": "block",
                    "reason": f"Lambda timeout exceeds limit ({timeout}s > {max_timeout}s). Adjust MAX_LAMBDA_TIMEOUT to increase.",
                }

    # Check for deployment without confirmation
    deploy_commands = ["sam deploy", "cdk deploy", "aws cloudformation deploy"]
    for deploy_cmd in deploy_commands:
        if deploy_cmd in command and "--no-confirm" in command:
            return {
                "decision": "block",
                "reason": "Deployments must not skip confirmation. Remove --no-confirm flag.",
            }

    # Check for force flags
    if "--force" in command or "-f" in command.split():
        return {
            "decision": "block",
            "reason": "Force flags are not allowed in AWS operations. Remove --force or -f flag.",
        }

    return {"decision": "allow"}


def main() -> None:
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)
        tool_input = input_data.get("tool_input", {})
        tool_name = input_data.get("tool_name", "")

        # Only check Bash commands
        if tool_name != "Bash":
            sys.exit(0)

        command = tool_input.get("command", "")

        # Check if this is an AWS-related command
        aws_tools = ["aws", "sam", "cdk", "terraform", "serverless", "amplify"]
        if not any(tool in command for tool in aws_tools):
            sys.exit(0)

        # Validate the command
        result = validate_aws_operation(command)

        if result["decision"] == "block":
            print(f"BLOCKED: {result['reason']}", file=sys.stderr)
            sys.exit(2)

        # Command is allowed
        sys.exit(0)

    except Exception as e:
        print(f"Hook error: {str(e)}", file=sys.stderr)
        # Allow operation on hook error
        sys.exit(0)


if __name__ == "__main__":
    main()
