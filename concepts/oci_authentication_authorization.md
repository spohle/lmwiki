TAGS: #oci #iam #authentication #authorization #cloud-computing #security

Links: [[oci]] [[iam]] [[authentication]] [[authorization]] [[cloud-computing]] [[security]]

# OCI Authentication and Authorization

This document provides an overview of how [[Oracle Cloud Infrastructure (OCI)]] manages access to its resources through [[Authentication]] (AuthN) and [[Authorization]] (AuthZ). These are fundamental concepts for securing any cloud environment.

## Identity Principals
In OCI, an [[Identity and Access Management (IAM)]] **principal** is any entity that can interact with OCI resources. The main types include:
*   **Users**: Human individuals who log into the OCI console or use programmatic tools like the [[OCI CLI]] and [[OCI SDKs]].
*   **Resource Principals**: Non-human entities, such as compute instances or other OCI services, that need to make API calls to other OCI services (e.g., accessing [[Object Storage]]). These resources become principals themselves.
*   **Groups**: Collections of users that share common access requirements. Policies are typically applied to groups rather than individual users for easier management (e.g., a "storage admin group").

## Authentication (AuthN)
[[Authentication]] is the process of verifying a principal's identity. OCI supports several mechanisms:
1.  **Username and Password**: The standard method for console access and web-based interactions.
2.  **API Signing Keys**: A public-private [[RSA]] key pair used to cryptographically sign and authenticate API requests made via the [[OCI SDKs]] or [[OCI CLI]]. This provides a secure, non-interactive way for programmatic access.
3.  **Authentication Tokens**: Oracle-generated strings designed for authenticating with third-party APIs or tools that may not natively support OCI's primary authentication models.

## Authorization (AuthZ)
[[Authorization]] determines what actions an authenticated principal is permitted to perform on specific resources. This is primarily managed through [[IAM Policies]].
*   **Syntax**: OCI policies are explicit and always begin with an `allow` statement, reflecting OCI's "deny by default" security posture.
*   **Scope**: Policies are defined at the group level, not for individual users. They can be attached to a specific [[Compartment]] (a logical container for resources) or apply across the entire [[Tenancy]] (the root compartment representing your OCI account).
*   **Verbs**: OCI uses a set of permission verbs to define the level of access:
    *   `inspect`: View resource metadata.
    *   `read`: View resource metadata and retrieve the resource itself.
    *   `use`: Perform all `read` actions, plus update or delete resources (without creating new ones).
    *   `manage`: Full administrative control, including `read`, `use`, and the ability to create, update, and delete resources.