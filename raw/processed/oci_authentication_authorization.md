# OCI Authentication and Authorization

## Identity Principals
In Oracle Cloud Infrastructure (OCI), a **principal** is an IAM entity allowed to interact with resources. There are two primary types:
* **Users**: Human beings who log into the console or use tools like the CLI and SDKs.
* **Resource Principals**: Instances or other resources that become principals to make API calls against other OCI services, such as storage.
* **Groups**: Collections of users who share the same access requirements, such as a "storage admin group".

## Authentication (AuthN)
Authentication verifies a user's identity. OCI supports three main mechanisms:
1. **Username and Password**: Standard credentials used for website/console access.
2. **API Signing Keys**: A public-private RSA key pair used to sign and authenticate API calls via SDKs or the CLI.
3. **Authentication Tokens**: Oracle-generated strings used to authenticate with third-party APIs that do not support the native OCI model.

## Authorization (AuthZ)
Authorization determines a principal's permissions and is managed through **IAM Policies**.
* **Syntax**: Policies always start with an `allow` statement because everything is denied by default.
* **Scope**: Policies are written at the group level (not for individual users) and can be attached to a specific **compartment** or the entire **tenancy**.
* **Verbs**: There are four levels of permission verbs: `inspect`, `read`, `use`, and `manage`.