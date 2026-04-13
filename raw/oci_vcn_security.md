# VCN Security Mechanisms

## Security Lists
Security Lists act as virtual firewalls associated with a **subnet** and apply to all instances within that subnet.
* **Rules**: Define the type of allowed ingress (incoming) or egress (outgoing) traffic.
* **Statefulness**:
    * **Stateful**: If traffic is allowed in, the response is automatically allowed out.
    * **Stateless**: Response traffic must be explicitly allowed by its own rule.

---

## Network Security Groups (NSG)
NSGs provide a more granular security construct than Security Lists.
* **Vnic-Level**: Unlike Security Lists, NSGs apply to specific **Virtual Network Interface Cards (VNICs)** within a single VCN.
* **Flexibility**: This allows two different instances in the *same* subnet to have entirely different security rules.
* **Rule Syntax**: NSGs can use other NSGs as a source or destination in their rules, whereas Security Lists are restricted to using CIDR blocks.