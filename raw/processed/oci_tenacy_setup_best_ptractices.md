# Tenancy Setup Best Practices

## Administrator Roles
* **Tenancy Administrator**: The primary person responsible for creating the account.
* **Proxy Admins**: It is a best practice to create an "OCI admin" group for day-to-day operations rather than using the main tenancy administrator account.

## Setup Requirements
To ensure a secure and organized environment, OCI recommends three primary best practices:
1. **Dedicated Compartments**: Isolate resources into compartments based on business units, projects, or geography rather than putting everything in the Root Compartment.
2. **Multi-Factor Authentication (MFA)**: Enforce MFA to require both a password (something you know) and a device (something you have).
3. **Policy Delegation**: Write policies that grant the OCI admin group access to manage all resources and specific IAM resource types.

## Essential IAM Policies
Because the IAM service has no aggregate resource type, administrators must grant permissions for individual components. Necessary resource types for a proxy administrator include:
* `domains`, `users`, `groups`, and `dynamic-groups`.
* `policies` and `compartments`.
* `tag-namespaces` and `network-sources`.