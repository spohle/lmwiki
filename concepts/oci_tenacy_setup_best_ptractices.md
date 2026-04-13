TAGS: #oci #security #iam #access-control #governance #resource-management #cloud-computing

Links: [[oci]] [[security]] [[iam]] [[access-control]] [[governance]] [[resource-management]] [[cloud-computing]]

# OCI Tenancy Setup Best Practices

Setting up an Oracle Cloud Infrastructure (OCI) tenancy correctly from the start is crucial for security, organization, and efficient management. Adhering to best practices ensures a robust and scalable cloud environment.

## Administrator Roles

It's important to distinguish between different administrative roles and follow the principle of least privilege:

*   **Tenancy Administrator**: This is the initial account creator and holds the highest level of access. This account should be used sparingly for initial setup and critical, infrequent operations.
*   **Proxy Admins**: For day-to-day operations, it is a best practice to create a dedicated "[[OCI admin]]" group. Members of this group will act as proxy administrators, performing routine tasks without using the main tenancy administrator account. This enhances [[security]] and [[auditability]].

## Key Setup Requirements

OCI recommends three primary best practices for a secure and organized tenancy:

1.  **Dedicated [[Compartments]]**: Avoid placing all resources in the [[Root Compartment]]. Instead, isolate resources into dedicated compartments based on logical divisions such as business units, projects, or geographical regions. This facilitates [[resource-management]], [[access-control]], and [[governance]].
2.  **[[Multi-Factor Authentication]] (MFA)**: Enforce MFA for all administrative users. MFA adds an essential layer of security by requiring two forms of verification: something the user knows (password) and something the user has (a device).
3.  **[[Policy Delegation]]**: Implement granular [[IAM policies]] that grant the "OCI admin" group appropriate access. These policies should allow the group to manage all necessary resources while adhering to the principle of least privilege.

## Essential [[IAM Policies]] for Proxy Administrators

Since the [[IAM]] service in OCI does not have an aggregate resource type, administrators must explicitly grant permissions for individual components. For a proxy administrator group to effectively manage the tenancy, policies must include permissions for the following essential IAM resource types:

*   `domains`
*   `users`
*   `groups`
*   `dynamic-groups`
*   `policies`
*   `compartments`
*   `tag-namespaces`
*   `network-sources`

These policies ensure that proxy administrators have the necessary permissions to manage user identities, access policies, and the organizational structure within the OCI tenancy.