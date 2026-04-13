TAGS: #oci #networking #architecture #cloud-computing #route-tables #vcn-peering #drg

Links: [[oci]] [[networking]] [[architecture]] [[cloud-computing]] [[route-tables]] [[vcn-peering]] [[drg]]

# VCN Routing and Peering in OCI

Oracle Cloud Infrastructure (OCI) Virtual Cloud Networks (VCNs) utilize **Route Tables** and **VCN Peering** to manage traffic flow, both within and between networks.

## Route Tables

[[Route Tables]] are fundamental components within a [[VCN]] that dictate how traffic destined for locations outside the immediate network segment should be directed.

*   **Route Rules**: Each route table contains a set of **Route Rules**. A rule specifies a **destination CIDR** block (the target network) and a **Route Target** (the "next hop" or gateway through which the traffic should be sent).
*   **Local Routing**: Traffic between subnets *within the same VCN* is automatically handled by OCI and does not require explicit route entries in a route table.
*   **Longest Prefix Match**: When multiple route rules could apply to a given destination IP address, the system prioritizes the rule with the most specific CIDR block (i.e., the one with the longest prefix). This ensures precise traffic direction.

## VCN Peering

[[VCN Peering]] allows two VCNs to communicate with each other using private IP addresses, as if they were in the same network. This is crucial for building complex, interconnected cloud environments.

*   **Local Peering**: Connects VCNs that reside within the *same OCI region*. This is achieved using a **[[Local Peering Gateway]] (LPG)** attached to each VCN.
*   **Remote Peering**: Connects VCNs located in *different OCI regions*. This type of peering utilizes a **[[Dynamic Routing Gateway]] (DRG)**.
*   **DRG v2**: The second version of the Dynamic Routing Gateway significantly simplifies network architectures. It allows up to 300 VCNs to communicate through a single DRG, eliminating the need for individual point-to-point peering connections between every pair of VCNs. This enhances scalability and manageability for large-scale deployments.