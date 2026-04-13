# OCI Virtual Cloud Network (VCN) Fundamentals

## Introduction to VCN
A Virtual Cloud Network is a private, software-defined network created within an OCI region for secure communication.
* **Address Space**: Defined using **CIDR** (Classless Inter-Domain Routing) notation.
* **Subnets**: The VCN range is divided into smaller networks called subnets, where compute instances are launched. These can be **Public** (internet-accessible) or **Private**.

---

## Connectivity Gateways
OCI uses several gateways to manage traffic in and out of a VCN:
* **Internet Gateway**: Provides highly available, bidirectional communication between the VCN and the internet.
* **NAT Gateway**: Provides **unidirectional** outbound internet access for private subnets, blocking any inbound connections initiated from the internet.
* **Service Gateway**: Enables private access to public OCI services (like Object Storage) without traversing the public internet.
* **Dynamic Routing Gateway (DRG)**: A virtual router providing a path for private traffic between the VCN and destinations other than the internet, such as on-premises environments.