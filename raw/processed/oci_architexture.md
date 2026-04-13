# OCI Architecture

## Core Physical Infrastructure
The physical architecture of Oracle Cloud Infrastructure (OCI) is built on several core constructs:
* **Regions**: A localized geographic area comprising one or more availability domains.
* **Availability Domains**: One or more fault-tolerant data centers located within a region, connected by a low-latency, high-bandwidth network. These domains are isolated from each other and are unlikely to fail simultaneously because they do not share physical infrastructure like power, cooling, or internal networks.
* **Fault Domains**: A grouping of hardware and infrastructure within an availability domain to provide anti-affinity. Each availability domain contains three fault domains, acting as logical data centers.

---

## Choosing a Region
When selecting a region, OCI recommends three key criteria:
1. **Proximity**: Choose a region closest to users for lowest latency and highest performance.
2. **Data Residency & Compliance**: Many countries have strict requirements that must be followed.
3. **Service Availability**: New services are deployed based on regional demand, regulatory reasons, and resource availability.

---

## High Availability and Redundancy
OCI provides constructs to help you avoid single points of failure:
* **Fault Domain Level**: Placing resources in different fault domains ensures they do not share single points of hardware failure like physical servers, racks, or switches.
* **Availability Domain Level**: Replicating application and database tiers across multiple ADs protects against an entire data center failure.
* **Data Synchronization**: Various technologies, such as Oracle Data Guard, can be used to keep primary and standby data synchronized.
* **Region Pairs**: In most countries of operation, OCI provides at least two data centers to assist with disaster recovery and backup.