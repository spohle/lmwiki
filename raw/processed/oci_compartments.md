# OCI Compartments

## Overview
A **compartment** is a unique and powerful logical construct used to organize and isolate cloud resources. 
* **Root Compartment**: Every new tenancy (account) starts with a Root Compartment that can hold all resources.
* **Isolation**: The primary purpose of creating dedicated compartments is to control access and isolate environments (e.g., Network, Storage, Production, or Development).

## Key Features
* **Single Membership**: Each resource belongs to exactly one compartment.
* **Interaction**: Resources in different compartments can still interact with each other (e.g., a compute instance using a network in a separate compartment).
* **Mobility**: Resources can be moved from one compartment to another.
* **Global Reach**: Compartments are global constructs available across all regions in a tenancy.
* **Nesting**: Compartments can be nested up to six levels deep to mimic organizational hierarchies.

## Governance
* **Quotas**: Administrators can set quotas to limit the creation of specific resources (like bare metal or Exadata) within a compartment.
* **Budgets**: You can set financial budgets on compartments to receive notifications if usage exceeds a certain dollar amount.