# Security Policy

## Supported Versions

Use this section to tell people about which versions of your project are currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of our software seriously. If you believe you've found a security vulnerability in the F1 MCP Server, please follow these steps:

1. **Email**: Send a report to info@machinetomachine.ai with the details of the vulnerability.
2. **Subject Line**: Use "F1 MCP Server Security Vulnerability" as your subject line.
3. **Details**: Please provide as much information as possible about the vulnerability, including:
   - Steps to reproduce
   - Potential impact
   - Suggested fixes (if any)
4. **Response Time**: We aim to acknowledge receipt of your report within 48 hours.
5. **Disclosure**: We request that you do not publicly disclose the issue until we've had a chance to address it.

## Security Measures

The F1 MCP Server implements several security measures:

1. **Input Validation**: All user inputs are validated before processing.
2. **Rate Limiting**: API requests are rate-limited to prevent abuse.
3. **Error Handling**: Error messages are sanitized to prevent information leakage.
4. **Dependency Scanning**: Regular scanning for vulnerabilities in dependencies.
5. **Access Control**: Proper file permissions and access controls for cache files.

## Security Considerations for Users

When running the F1 MCP Server, consider the following security practices:

1. **Run with Least Privileges**: Always run the server with the minimum necessary privileges.
2. **Restrict Network Access**: Configure firewalls to restrict access to the server.
3. **Keep Updated**: Regularly update the package to receive security fixes.
4. **Monitor Logs**: Watch server logs for unusual patterns that might indicate abuse.
