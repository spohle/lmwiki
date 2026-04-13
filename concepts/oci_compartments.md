TAGS: #oci #compartments #architecture #cloud-computing #security #governance #resource-management #access-control

Links: [[oci]] [[compartments]] [[architecture]] [[cloud-computing]] [[security]] [[governance]] [[resource-management]] [[access-control]]

A **compartment** in [[Oracle Cloud Infrastructure]] (OCI) is a fundamental logical construct designed for organizing and isolating [[Cloud Computing|cloud resources]]. It serves as a primary mechanism for [[Access Control|access control]] and environmental separation within an OCI [[Tenancy]].

### Key Characteristics

*   **Root Compartment**: Every new OCI tenancy automatically includes a [[Root Compartment]] at its creation. This compartment is the default container for all resources unless specified otherwise.
*   **Resource Isolation**: The core purpose of compartments is to provide logical isolation, allowing administrators to segregate different environments (e.g., [[Network]], [[Storage]], [[Production Environment]], [[Development Environment]]) and control access to them independently.
*   **Single Membership**: Each individual [[Cloud Resource|resource]] within OCI must belong to exactly one compartment at any given time.
*   **Inter-Compartment Interaction**: Despite their isolation capabilities, resources located in different compartments can still interact with each other, provided the appropriate [[IAM Policies|IAM policies]] are configured. For example, a compute instance in one compartment might utilize a virtual network in another.
*   **Mobility**: Resources are not permanently bound to a compartment and can be moved between compartments, offering flexibility in managing evolving architectures.
*   **Global Scope**: Compartments are global constructs within a tenancy, meaning they are accessible and consistent across all [[OCI Regions|regions]] associated with that tenancy.
*   **Nesting**: To facilitate complex organizational hierarchies, compartments can be nested up to six levels deep, mirroring departmental or project structures.

### Governance and Management

Compartments play a crucial role in OCI's governance framework:

*   **Quotas**: Administrators can define [[Quotas]] on compartments to limit the creation of specific resource types (e.g., bare metal instances, Exadata deployments) within them, helping manage resource consumption and costs.
*   **Budgets**: Financial [[Budgets]] can be set at the compartment level. These budgets trigger notifications when resource usage within the compartment exceeds a predefined monetary threshold, aiding in cost management and control.