# Amazon S3 Files: S3 Buckets as Shared File Systems

**Posted on:** April 7, 2026

Amazon S3 Files delivers a shared file system that connects any AWS compute resource directly with your data in Amazon S3. It makes S3 the first and only cloud object store to provide fully-featured, high-performance file system access without your data ever leaving the bucket.

---

### Key Features and Benefits

* **Full File System Semantics:** Use standard file-based tools and applications with no code changes required.
* **Built on Amazon EFS:** Leverages EFS architecture for performance and simplicity while maintaining S3’s scalability, durability, and cost-effectiveness.
* **Native S3 Integration:** No more duplicating data or cycling it between object and file storage. S3 Files translates file operations into efficient S3 requests automatically.
* **Simultaneous Access:** Thousands of compute resources (instances, containers, and functions) can connect to the same file system at once.
* **Dual-Access Architecture:** Access your data through the file system and S3 APIs simultaneously with no synchronization lag.

### High-Performance Performance

S3 Files is designed to eliminate storage bottlenecks for modern workloads:
* **Low Latency:** Caches actively used data to ensure fast response times.
* **Massive Throughput:** Supports up to multiple terabytes per second of aggregate read throughput.
* **No Migration:** Works with all new and existing data in your current S3 buckets immediately.

### Use Cases

| Workload | Benefit |
| :--- | :--- |
| **AI Agents** | Persist memory and share state across pipelines seamlessly. |
| **ML Teams** | Run data preparation directly on S3 without duplicating or staging files. |
| **Analytics** | Connect data lakes to file-based legacy applications without complex pipelines. |
| **Collaboration** | Provide teams shared access to data clusters without creating silos. |

---

### Availability
**S3 Files is now Generally Available (GA) in 34 AWS Regions.**

#### Useful Links:
* [AWS Capabilities Tool](#)
* [Product Page](#)
* [S3 Pricing Page](#)
* [Documentation](#)
* [AWS News Blog](#)
