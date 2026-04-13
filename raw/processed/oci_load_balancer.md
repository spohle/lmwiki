# OCI Load Balancer Service

## Overview
The OCI Load Balancer acts as a **Reverse Proxy**, distributing traffic from multiple clients to various backend servers. This architecture provides two primary benefits:
* **High Availability**: If a specific backend server fails, the application remains operational by routing traffic to healthy servers.
* **Scalability**: New backend servers can be added easily to handle increased client traffic.

---

## Layer 7 HTTP Load Balancer
This type operates at the application layer and understands HTTP/HTTPS protocols.
* **Shapes**:
    * **Flexible**: Users define a custom range (minimum and maximum bandwidth) from 10 Mbps to 8 Gbps.
    * **Dynamic**: Predefined shapes (Micro, Small, Medium, Large) that scale automatically without a "warm-up" period.
* **Visibility**: Available as **Public** (internet-facing) or **Private** (internal traffic between tiers).
* **Advanced Features**: Supports intelligent features like **Content-Based Routing** and SSL termination.

---

## Network Load Balancer (Layer 4)
The Network Load Balancer operates at Layer 3 and Layer 4, supporting TCP, UDP, and ICMP.
* **Performance**: It is significantly faster and offers lower latency than the Layer 7 version.
* **Use Case**: Choose this when raw performance is a priority; use the HTTP Load Balancer when deep packet inspection or routing intelligence is required.