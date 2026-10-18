# System Design Notes: Load Balancing, Capacity Planning, Storage Estimation, and Sharding

## Table of Contents

-   [1. Session Overview](#1-session-overview)
-   [2. Load Balancer Basics](#2-load-balancer-basics)
-   [3. Server Registration and
    Discovery](#3-server-registration-and-discovery)
-   [4. Load Balancer Routing
    Algorithms](#4-load-balancer-routing-algorithms)
-   [5. Heartbeat vs. Health Check](#5-heartbeat-vs-health-check)
-   [6. Capacity Planning and Load
    Testing](#6-capacity-planning-and-load-testing)
-   [7. Retries, Failures, and
    Idempotency](#7-retries-failures-and-idempotency)
-   [8. Storage Estimation: Bookmarks
    Example](#8-storage-estimation-bookmarks-example)
-   [9. Why Sharding Is Needed](#9-why-sharding-is-needed)
-   [10. Quick Reference](#10-quick-reference)
-   [11. System Design Interview
    Approach](#11-system-design-interview-approach)

------------------------------------------------------------------------

## 1. Session Overview

This session connects load balancing to the broader infrastructure
picture:

-   How application servers are discovered and registered.
-   How incoming requests are distributed.
-   How server failures are detected.
-   How capacity is estimated and tested.
-   How data storage requirements are calculated.
-   Why sharding becomes necessary as datasets grow.

### Recurring system-design principles

1.  **Keep headroom:** Do not design a production system to operate
    continuously at exactly 100% capacity.
2.  **Design retries carefully:** A missing response does not prove that
    a request was never processed.
3.  **Understand managed infrastructure:** Even if a managed service is
    used, understand its internal architecture and decision flow.
4.  **Separate distinct problems:** Server discovery and request
    distribution are related but different responsibilities.

------------------------------------------------------------------------

## 2. Load Balancer Basics

A **load balancer** sits in front of application servers and decides
where incoming requests should go.

``` text
Client
  |
  v
Load Balancer
  |
  +------> Application Server 1
  +------> Application Server 2
  +------> Application Server 3
```

In a production environment, application servers can be created or
removed dynamically through provisioning and autoscaling. Therefore,
maintaining a fixed list of server IP addresses is fragile.

### 2.1 Discovery vs. distribution

These are two separate problems:

  -----------------------------------------------------------------------
  Concern                 Question                Purpose
  ----------------------- ----------------------- -----------------------
  **Discovery**           How does the load       Maintains awareness of
                          balancer learn which    available servers
                          application servers     
                          exist?                  

  **Distribution**        Once servers are known, Selects a destination
                          which server should     for each request
                          receive a request?      
  -----------------------------------------------------------------------

Algorithms such as Round Robin and Weighted Round Robin solve the
**distribution** problem. They do not, by themselves, solve server
discovery.

### 2.2 Why static configuration does not scale

A fixed list of server IP addresses becomes unreliable because:

-   The number of servers changes over time.
-   Cloud environments can scale automatically based on demand.
-   New instances can be provisioned dynamically.
-   Existing instances can be removed or replaced.

A production system needs a mechanism to track active servers as the
environment changes.

> **Key takeaway:** First establish how servers become known to the load
> balancer. Then determine how requests are routed among them.

------------------------------------------------------------------------

## 3. Server Registration and Discovery

A newly provisioned server does not automatically become routable merely
because it exists. In the model discussed here, the server explicitly
registers itself with the load balancer during startup.

### 3.1 Roles and responsibilities

  -----------------------------------------------------------------------
  Component                           Responsibility
  ----------------------------------- -----------------------------------
  **Load balancer**                   Receives incoming traffic,
                                      maintains a list of available
                                      backend servers, and routes
                                      requests

  **Orchestrator / autoscaling        Monitors demand and decides when
  controller**                        additional servers should be
                                      provisioned

  **Application server**              Starts with the required
                                      configuration and registers itself
                                      with the load balancer

  **Startup / initialization code**   Loads configuration and performs
                                      the registration request
  -----------------------------------------------------------------------

### 3.2 Scale-out registration flow

1.  Existing application servers handle incoming traffic.
2.  Demand increases beyond the current capacity.
3.  The orchestration or autoscaling layer determines that more capacity
    is needed.
4.  The orchestrator provisions additional application servers.
5.  Each new server starts and runs its initialization code.
6.  The startup code calls the load balancer's registration API with the
    server's IP address.
7.  The load balancer adds the server to its backend list.
8.  Requests can now be routed to the newly registered server.

``` text
Demand increases
      |
      v
Orchestrator provisions a new server
      |
      v
Application server starts
      |
      v
Startup code loads load-balancer configuration
      |
      v
Server sends registration request with its IP
      |
      v
Load balancer adds server to backend list
      |
      v
Registration response (for example, HTTP 200 OK)
      |
      v
Server becomes eligible for routing
```

The `200 OK` response is an illustrative success response in this flow;
the actual API contract depends on the implementation.

### 3.3 Registration analogy

Think of a registration process such as registering a birth with a
government authority. The authority does not necessarily know about the
event until the required registration takes place.

Similarly, infrastructure may require an explicit registration step
before a newly created server becomes eligible to receive traffic.

> **Key takeaway:** Scaling out involves both provisioning machines and
> making those machines known to the routing system.

------------------------------------------------------------------------

## 4. Load Balancer Routing Algorithms

After discovering available servers, the load balancer needs a routing
algorithm to select a destination for each request.

Because the load balancer is on the critical path for incoming traffic,
routing should be efficient. Expensive routing logic can turn the load
balancer itself into a bottleneck.

### 4.1 Round Robin

**Round Robin** sends requests to servers in sequence and loops back to
the beginning.

Example with three servers:

  Request     Destination
  ----------- -------------
  Request 1   Server 1
  Request 2   Server 2
  Request 3   Server 3
  Request 4   Server 1
  Request 5   Server 2
  Request 6   Server 3

Conceptually, the load balancer maintains a pointer or index that
advances for each request:

``` text
Server 1 -> Server 2 -> Server 3
    ^                       |
    |_______________________|
```

**When it fits:** A straightforward starting point when servers have
broadly comparable capacity and a simple cyclic distribution is
suitable.

**Limitation:** Equal request counts do not necessarily mean equal
resource usage. Requests can differ in processing time and resource
consumption.

### 4.2 Weighted Round Robin

**Weighted Round Robin** assigns different traffic weights to servers
according to their relative capacity.

Example capacity assumptions:

  Server        RAM in the example   Relative weight
  ----------- -------------------- -----------------
  Server 1                    4 GB                 1
  Server 2                    8 GB                 2
  Server 3                   16 GB                 4
  **Total**              **28 GB**             **7**

The simplified relative ratio is:

``` text
Server 1 : Server 2 : Server 3
    1     :     2     :     4
```

Under a proportional distribution, Server 1 receives approximately 1/7
of the requests, Server 2 receives 2/7, and Server 3 receives 4/7,
subject to the algorithm's implementation and workload.

**Important:** RAM alone does not determine a server's true capacity. A
practical weighting strategy may account for CPU, memory, network
capacity, workload characteristics, and other constraints.

### 4.3 Comparison

  -----------------------------------------------------------------------
  Aspect                  Round Robin             Weighted Round Robin
  ----------------------- ----------------------- -----------------------
  Distribution            Cyclic across servers   Proportional to
                                                  assigned weights

  Assumption              Servers are broadly     Servers may have
                          comparable              different capacities

  Configuration           Simple server list      Server list plus
                                                  weights

  Main limitation         Does not account for    Weights may not reflect
                          unequal capacity        changing real-time load
  -----------------------------------------------------------------------

> **Key takeaway:** Round Robin is simple and cyclic. Weighted Round
> Robin adjusts the traffic ratio to reflect differences in server
> capacity.

------------------------------------------------------------------------

## 5. Heartbeat vs. Health Check

A load balancer needs to detect when a registered server becomes
unavailable. A server can crash unexpectedly, and it may not be able to
notify the load balancer after the failure.

Liveness is therefore inferred from expected signals rather than from a
failed server announcing its own failure.

### 5.1 Heartbeat

With a **heartbeat**, the server periodically sends a signal to the load
balancer or monitoring system.

``` text
Application Server  ---- "I am alive" ----> Monitoring / Load Balancer
Application Server  ---- "I am alive" ----> Monitoring / Load Balancer
Application Server  ---- "I am alive" ----> Monitoring / Load Balancer
```

Suppose:

-   `T` = heartbeat interval.
-   `N` = number of consecutive missed heartbeats required before the
    server is considered unavailable.

The simplified detection window is approximately:

\[ `\text{Detection window}`{=tex} `\approx `{=tex}N `\times `{=tex}T \]

A single missed heartbeat should not necessarily cause the server to be
marked down because transient network problems can occur.

### 5.2 Health check

With a **health check**, the monitoring system or load balancer
initiates the check by periodically contacting the server.

``` text
Load Balancer  ---- "Are you alive?" ----> Application Server
Load Balancer  <---- "I am alive" ------- Application Server
```

Suppose:

-   `T` = interval between checks.
-   `N` = number of consecutive failed checks required before the server
    is considered unavailable.

The simplified detection window is approximately:

\[ `\text{Detection window}`{=tex} `\approx `{=tex}N `\times `{=tex}T \]

Actual detection timing depends on scheduling, timeout configuration,
and implementation details.

### 5.3 Comparison

  -----------------------------------------------------------------------
  Aspect                  Heartbeat               Health check
  ----------------------- ----------------------- -----------------------
  Initiator               Server                  Load balancer /
                                                  monitoring system

  Direction               Server sends periodic   Monitor sends periodic
                          signals                 probes

  Expected signal         Heartbeat               Health-check response

  Failure indication      Required heartbeat      Required checks fail or
                          signals are missed      time out

  Main consideration      Signal delivery and     Probe interval,
                          missed-heartbeat        timeout, and failure
                          threshold               threshold
  -----------------------------------------------------------------------

### 5.4 Why repeated failures matter

Neither method gives absolute certainty. A missed signal can result from
a temporary network issue, while a successful check only indicates that
the server responded at that time.

> **Key takeaway:** Liveness is a best-effort judgment based on repeated
> missing signals or failed checks. Avoid declaring a server down based
> on one transient failure unless the system's requirements explicitly
> call for it.

------------------------------------------------------------------------

## 6. Capacity Planning and Load Testing

Production systems should not be designed to run continuously at exactly
100% of expected capacity. They need **headroom** to handle spikes,
absorb uncertainty, and remain reliable while scaling actions take
effect.

### 6.1 Capacity headroom example

Suppose normal demand is approximately 30 requests per second (RPS).

A system might be provisioned to handle around 45 RPS or more, based on
measured performance and the desired safety margin.

  Metric                                 Example
  ------------------------------------ ---------
  Normal expected traffic                 30 RPS
  Example provisioned capacity            45 RPS
  Absolute reserve in this example        15 RPS
  Reserve relative to normal traffic         50%

These are illustrative numbers, not universal sizing rules. Real
capacity should be based on measurements, traffic patterns,
service-level objectives, and failure scenarios.

### 6.2 Why headroom matters

-   Traffic can spike suddenly.
-   Autoscaling takes time to detect demand and provision capacity.
-   A server or dependency can fail, reducing available capacity.
-   The system needs a buffer to handle unexpected workload variation.

### 6.3 Load testing and volume testing

Use testing to determine appropriate intervals, thresholds, and capacity
assumptions instead of relying only on intuition.

A practical process:

1.  Gather historical traffic data or prepare representative test data.
2.  Define realistic workloads and expected traffic patterns.
3.  Run tests using different parameter values.
4.  Measure throughput, latency, errors, resource utilization, and
    monitoring overhead.
5.  Compare the results.
6.  Select values that meet performance and reliability requirements
    without overloading the system.

These techniques are relevant to:

-   Load balancers.
-   APIs.
-   Flash-sale systems.
-   Systems with bursty traffic.
-   Monitoring and health-check configurations.

**Important consideration:** Smaller intervals are not automatically
better. Checking or updating too frequently can create additional
processing and network overhead.

### 6.4 Multiple load balancers

A load balancer is itself a service with finite capacity and
availability requirements. Large systems may use multiple load balancers
across regions or availability zones.

``` text
Users
  |
  v
DNS / Global Routing
  |
  +------------------+
  |                  |
  v                  v
Regional LB A     Regional LB B
  |                  |
  v                  v
Application       Application
Servers A         Servers B
```

This is a conceptual illustration. Actual designs vary by provider and
architecture.

Users may be routed to an appropriate region using DNS, IP-based
routing, or other global traffic-management mechanisms.

Not every payload must pass through the application load balancer. For
example, large file uploads may use pre-signed URLs to transfer data
directly to object storage, depending on the system design.

> **Key takeaway:** Combine capacity headroom, realistic load testing,
> and appropriate distribution layers to reduce overload risk.

------------------------------------------------------------------------

## 7. Retries, Failures, and Idempotency

A health check can report that a server is healthy, but the server can
fail immediately afterward. A request or its response can also be lost
in transit.

### 7.1 The ambiguous outcome problem

If a client sends a request but receives no response, several outcomes
are possible:

1.  The server never received the request.
2.  The server received and processed the request, but the response was
    lost.
3.  The server processed part of the operation and then failed.
4.  The request is still being processed.

Therefore:

> **A missing response does not prove that the operation failed.**

### 7.2 Why blindly retrying is dangerous

Consider an order-creation request:

``` text
Client sends: Create order
        |
        v
Server creates the order
        |
        v
Response is lost
        |
        v
Client assumes failure and retries
        |
        v
A duplicate order may be created
```

The exact result depends on the API and persistence design. The central
problem is that the client cannot infer the operation's outcome from the
missing response alone.

### 7.3 Reconciliation and duplicate handling

When the outcome is unclear, the system may need to:

-   Check whether the intended change already exists.
-   Retry carefully.
-   Confirm the current state before reapplying an operation.
-   Detect and ignore duplicate requests when appropriate.
-   Use an idempotency mechanism for operations that must not create
    duplicate effects.

### 7.4 Idempotency

An operation is **idempotent** when repeating it with the same intended
input produces the same intended effect as performing it once.

For example, setting a resource's status to `ACTIVE` repeatedly can be
idempotent if every call leaves the resource in the same state.

By contrast, a request that creates a new payment or order on every
invocation may produce duplicate effects unless the API includes
suitable safeguards.

### 7.5 PUT and resource creation/update

The session discussed using `PUT` for a desired behavior in which a
resource is created if absent or updated if present.

This can be suitable when the request identifies the resource and
expresses the desired state. However, the HTTP method alone does not
guarantee safe application-level behavior; the API implementation must
preserve the intended idempotency semantics.

### 7.6 Practical retry checklist

Before retrying an operation, ask:

-   Is the operation safe to repeat?
-   Could the original request already have succeeded?
-   Does the API support an idempotency key or another
    duplicate-detection mechanism?
-   Can the current state be checked before retrying?
-   Is there a bounded retry policy with suitable backoff?
-   What happens if the operation partially succeeds?

> **Key takeaway:** Retries are normal in distributed systems. Design
> operations so that uncertain outcomes and repeated requests do not
> create unintended duplicate effects.

------------------------------------------------------------------------

## 8. Storage Estimation: Bookmarks Example

Storage estimation helps determine whether a dataset can fit on one
machine and when distributed storage may be necessary. The goal is not
perfect precision at the beginning; it is to make reasonable assumptions
and show the calculation clearly.

### 8.1 Estimate the size of one record

The example bookmark record uses these approximate field sizes:

  Field         Estimated size
  ----------- ----------------
  ID                   8 bytes
  User ID              8 bytes
  Title               20 bytes
  URL                 50 bytes
  **Total**       **86 bytes**

For easier mental calculation, round the estimate to approximately **100
bytes per bookmark**.

This is a simplified estimate of field data. Actual database storage can
be higher because of indexes, row metadata, encoding, page layout,
replication, and other overhead.

### 8.2 Estimate daily storage growth

Assumptions:

-   Daily volume: 12.5 million bookmarks.
-   Estimated size per bookmark: 100 bytes.

Calculation:

\[ 12.5`\text{ million}`{=tex} `\times 100`{=tex}`\text{ bytes}`{=tex} =
1.25`\text{ billion bytes}`{=tex} \]

Using decimal units, this is approximately **1.25 GB per day**. The
original exercise rounds this to roughly **1 GB/day** for mental
estimation.

### 8.3 Estimate yearly and five-year storage

Using the simplified estimate of approximately 1 GB/day:

  Period    Calculation                      Approximate storage
  --------- ------------------------ ---------------------------
  1 day     Given rounded estimate                          1 GB
  1 year    1 GB × 365 days            365 GB, rounded to 400 GB
  5 years   365 GB × 5                    1,825 GB, roughly 2 TB

These figures use a rounded daily estimate. Using the unrounded 1.25
GB/day estimate would produce a higher projection.

### 8.4 Unit conversion

For approximate decimal-unit calculations:

``` text
1 KB  ≈ 1,000 bytes
1 MB  ≈ 1,000 KB
1 GB  ≈ 1,000 MB
1 TB  ≈ 1,000 GB
```

Binary units such as KiB, MiB, GiB, and TiB use powers of 1,024 instead.

### 8.5 What the estimate does and does not include

A basic row-size estimate is a starting point. A production capacity
plan may also need to account for:

-   Database indexes.
-   Row and page metadata.
-   Replication and backups.
-   Data growth and retention policies.
-   Compaction and maintenance requirements.
-   Reserved disk capacity and operational headroom.

Do not assume that all advertised disk capacity is available for
application data.

> **Key takeaway:** Estimate record size, multiply by data volume,
> convert units, project over time, and account for real storage
> overhead before deciding on the architecture.

------------------------------------------------------------------------

## 9. Why Sharding Is Needed

When a dataset grows beyond the practical storage or processing capacity
of one database machine, the system may need to distribute data across
multiple machines. This is the motivation for **sharding**.

### 9.1 What is sharding?

**Sharding** divides a dataset into smaller subsets and stores those
subsets on different database machines.

Instead of one database server holding every row, multiple database
servers each hold a portion of the data.

``` text
Client
  |
  v
Load Balancer
  |
  v
Application Servers
  |
  v
Data Routing / Shard Selection
  |
  +------------------+------------------+
  |                  |                  |
  v                  v                  v
Shard 1            Shard 2            Shard 3
Database           Database           Database
```

This is a conceptual architecture. The component responsible for shard
selection may be implemented in application code, a routing layer, a
database proxy, or another part of the system.

### 9.2 Why sharding becomes an architectural decision

Splitting data is only part of the problem. The system must also decide:

1.  Which row belongs to which shard?
2.  What key or rule determines the destination?
3.  Which component performs shard selection?
4.  How are reads and writes routed to the correct shard?
5.  How can data be redistributed when capacity changes?

The choice of shard key and routing strategy affects query efficiency,
load distribution, and operational complexity.

### 9.3 Partitioning vs. sharding

  -----------------------------------------------------------------------
  Concept                             Meaning in this overview
  ----------------------------------- -----------------------------------
  **Partitioning**                    Dividing data into smaller logical
                                      or physical parts

  **Sharding**                        Distributing data partitions across
                                      separate database machines or
                                      instances
  -----------------------------------------------------------------------

Terminology can vary between database products. Some systems use the
term *partitioning* for data distribution within one database instance
as well as for other forms of partitioning.

### 9.4 When to consider sharding

Sharding may be appropriate when:

-   A single machine cannot store the growing dataset within practical
    limits.
-   One database instance cannot meet throughput or resource
    requirements.
-   The workload can be divided using a suitable shard key.
-   The team can handle the additional routing, monitoring, and
    operational complexity.

Sharding is not automatically the first solution to every database
performance problem. Indexing, query optimization, vertical scaling,
caching, and read replicas may be worth evaluating depending on the
bottleneck.

> **Key takeaway:** Sharding distributes data across machines. The core
> design challenge is determining where each row belongs and routing
> operations to the correct shard.

------------------------------------------------------------------------

## 10. Quick Reference

### Load balancers and server management

  -----------------------------------------------------------------------
  Topic                               Remember
  ----------------------------------- -----------------------------------
  Discovery                           How the load balancer learns about
                                      available servers

  Distribution                        How requests are assigned to known
                                      servers

  Registration                        New servers may register themselves
                                      during startup

  Round Robin                         Cycles through servers in order

  Weighted Round Robin                Allocates traffic according to
                                      configured weights

  Heartbeat                           Server periodically sends an "I am
                                      alive" signal

  Health check                        Monitor periodically asks the
                                      server to respond

  Headroom                            Provision reserve capacity beyond
                                      expected demand

  Multiple load balancers             Distribute traffic and reduce
                                      dependence on one routing instance
  -----------------------------------------------------------------------

### Reliability and retries

  -----------------------------------------------------------------------
  Topic                               Remember
  ----------------------------------- -----------------------------------
  Ambiguous failure                   A missing response does not prove
                                      the request was not processed

  Retry                               May repeat an operation that
                                      already succeeded

  Idempotency                         Repeating an operation does not
                                      create additional unintended
                                      effects

  Reconciliation                      Check the current state when the
                                      outcome is uncertain

  PUT                                 Can represent create-or-update
                                      behavior when the API is designed
                                      for it
  -----------------------------------------------------------------------

### Storage and sharding

  Topic                     Example / definition
  ------------------------- -----------------------------------------------------
  Approximate record size   100 bytes per bookmark
  Daily volume              12.5 million bookmarks in the example
  Rounded daily growth      Roughly 1 GB/day in the exercise
  Rounded yearly growth     Roughly 400 GB/year
  Five-year projection      Roughly 2 TB using the rounded estimate
  Partitioning              Dividing data into parts
  Sharding                  Distributing data across separate database machines

------------------------------------------------------------------------

## 11. System Design Interview Approach

A strong high-level design answer should explain the problem,
alternatives, trade-offs, and why a chosen approach fits the
requirements.

Use this sequence:

1.  **Identify the problem.** For example, a load balancer needs to know
    which servers are available.
2.  **Separate responsibilities.** Discovery, registration, routing, and
    health detection are different concerns.
3.  **List alternatives.** For example, Round Robin vs. Weighted Round
    Robin, or heartbeat vs. active health checks.
4.  **Compare trade-offs.** Consider simplicity, overhead, failure
    detection time, and uneven workloads.
5.  **State assumptions.** Define traffic volume, server capacity, data
    size, and expected growth.
6.  **Choose based on constraints.** Avoid claiming that one approach is
    best for every system.
7.  **Explain failure handling.** Include timeouts, retries, duplicate
    requests, and recovery behavior.
8.  **Plan for growth.** Estimate capacity and explain when additional
    machines or sharding may be required.

### Final mental model

``` text
Incoming traffic
      |
      v
Load balancer discovers and tracks servers
      |
      v
Routing algorithm selects a destination
      |
      v
Health monitoring detects unavailable servers
      |
      v
Capacity planning and load testing guide scaling
      |
      v
Application accesses data storage
      |
      v
Storage estimation reveals when distribution is needed
      |
      v
Sharding distributes data across database machines
```

The central lesson is to understand each component's responsibility, how
the components interact, and what happens when capacity or reliability
assumptions fail.
