TAGS: #oci #networking #cloud-computing #security #architecture #resource-management #access-control

Links: [[oci]] [[networking]] [[cloud-computing]] [[security]] [[architecture]] [[resource-management]] [[access-control]]

# OCI Virtual Cloud Network (VCN) Fundamentals

A [[Virtual Cloud Network]] ([[VCN]]) is a private, software-defined network established within an [[OCI]] region. It serves as the foundational network for secure communication among resources deployed in the cloud.

## Core Components
*   **Address Space**: Defined using **CIDR** (Classless Inter-Domain Routing) notation, which specifies the overall IP address range available within the VCN.
*   **Subnets**: The VCN's address space is segmented into smaller networks called [[Subnets]]. Compute instances and other resources are launched within these subnets. Subnets can be:
    *   **Public**: Directly accessible from the internet.
    *   **Private**: Isolated from direct internet access.

## Connectivity Gateways
[[OCI]] provides several types of gateways to manage traffic flow into and out of a [[VCN]], ensuring secure and controlled connectivity:

*   **[[Internet Gateway]]**: Facilitates highly available, bidirectional communication between the [[VCN]] and the public internet. Essential for public-facing applications.
*   **[[NAT Gateway]]**: Offers **unidirectional** outbound internet access for resources located in private subnets. It prevents any inbound connections initiated from the internet, enhancing security for internal resources.
*   **[[Service Gateway]]**: Enables private access to specific public [[OCI]] services (e.g., [[Object Storage]], Autonomous Database) without requiring traffic to traverse the public internet. This improves security and reduces latency.
*   **[[Dynamic Routing Gateway (DRG)]]**: Acts as a virtual router, providing a path for private traffic between the [[VCN]] and destinations other than the internet. This is primarily used for connecting the [[VCN]] to on-premises networks via [[IPSec VPN]] or [[FastConnect]], or for inter-VCN communication.