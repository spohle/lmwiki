# VCN Routing and Peering

## Route Tables
VCNs use **Route Tables** to direct traffic to destinations outside the network.
* **Route Rules**: Consist of a destination CIDR and a **Route Target** (the "next hop").
* **Local Routing**: Traffic between subnets within the same VCN is handled automatically and does not require manual route entries.
* **Longest Prefix Match**: When multiple rules exist, the more specific CIDR block (the one with the longer prefix) takes priority.

---

## VCN Peering
* **Local Peering**: Connects VCNs within the same OCI region using a **Local Peering Gateway (LPG)**.
* **Remote Peering**: Connects VCNs in different regions using a **Dynamic Routing Gateway (DRG)**.
* **DRG v2**: A newer version that simplifies complex environments, allowing up to 300 VCNs to communicate through a single DRG without needing individual point-to-point peering.