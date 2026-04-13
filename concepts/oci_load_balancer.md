TAGS: #oci #load-balancer #networking #high-availability #scalability #cloud-computing #architecture

Links: [[oci]] [[load-balancer]] [[networking]] [[high-availability]] [[scalability]] [[cloud-computing]] [[architecture]]

# OCI Load Balancer Service

The [[OCI]] Load Balancer acts as a [[Reverse Proxy]], efficiently distributing incoming client traffic across multiple backend servers. This fundamental [[networking]] component is crucial for modern application architectures, primarily offering:
*   **[[High Availability]]**: Ensures application uptime by redirecting traffic away from unhealthy servers.
*   **[[Scalability]]**: Allows for seamless addition of new backend servers to accommodate increased traffic loads.

## Types of OCI Load Balancers

### Layer 7 HTTP Load Balancer
Operating at the application layer, this type understands [[HTTP]] and [[HTTPS]] protocols, enabling intelligent traffic management.
*   **Shapes**:
    *   **Flexible**: Users define a custom bandwidth range (10 Mbps to 8 Gbps).
    *   **Dynamic**: Predefined shapes (Micro, Small, Medium, Large) that automatically scale without a warm-up period.
*   **Visibility**: Can be configured as **Public** (internet-facing) or **Private** (for internal traffic between application tiers).
*   **Advanced Features**: Supports sophisticated capabilities like [[Content-Based Routing]] and [[SSL Termination]].

### Network Load Balancer (Layer 4)
This load balancer operates at Layer 3 and Layer 4, supporting [[TCP]], [[UDP]], and [[ICMP]] protocols.
*   **Performance**: Offers significantly higher performance and lower latency compared to the Layer 7 HTTP Load Balancer.
*   **Use Case**: Ideal for scenarios where raw performance is paramount. If deep packet inspection or advanced routing intelligence (like [[Content-Based Routing]]) is required, the Layer 7 HTTP Load Balancer is the more suitable choice.