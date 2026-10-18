# Session Overview

Reviews cache write strategies and eviction policies, then explains CAP
and PACELC trade-offs.\
Covers leader--replica database architecture, replication consistency,
and the different scaling roles of sharding and replication.\
Works through a capacity-planning example and considers availability,
failover, and replica placement.

## Caching recap

The cache strategies reviewed were **write-through**, **write-back**,
and **write-around**. Write-through updates the cache and backing store
together; write-back can leave the backing store temporarily behind; and
write-around bypasses the cache on writes. With **TTL (time-to-live)
caching**, an entry expires after a set period, so a cache may serve
stale data until it expires or is refreshed.

Eviction policies determine which entries to remove when a cache is
full. The policies reviewed were **LRU**, **LFU**, **FIFO**, and
**LIFO**.

**Watch out:** TTL can allow stale data to remain available until
expiration, but TTL alone does not guarantee eventual consistency; that
depends on how updates and refreshes are handled.

**Key takeaway:** Cache write strategies, TTL behavior, and eviction
policies address different questions: how writes propagate, how long
entries remain, and what gets removed when space runs out.

## CAP and PACELC

**CAP** stands for **Consistency, Availability, and Partition
Tolerance**. A partition occurs when components of a distributed system
cannot communicate with one another.

During a partition, a system must choose between:

-   **Consistency:** preserving a consistent view of data, rather than
    serving a response that may be stale.
-   **Availability:** continuing to respond to requests, even if a
    response may not reflect the latest data.
-   **Partition tolerance:** continuing to operate despite communication
    failures between components.

> *During a network partition, a distributed system cannot guarantee
> both consistent responses and a response to every request.*

A useful way to explain the trade-off is to imagine application servers
that cannot communicate with one another. A server that responds from
potentially stale local data favors availability; one that rejects or
delays the request to preserve consistency favors consistency.

**Key insight:** The CAP trade-off is specifically about what happens
**when a partition occurs**. Without a partition, the system may provide
both consistency and availability. Not having a partition is not the
same as lacking partition tolerance.

**PACELC** extends this framing to normal operation:

``` text
If there is a Partition (P):
    choose Availability (A) or Consistency (C)
Else (E), when there is no partition:
    choose lower Latency (L) or Consistency (C)
```

Even when components can communicate, a system may respond quickly
before all copies are up to date, or wait for coordination to provide
stronger consistency. PACELC highlights this ordinary-operation
trade-off between latency and consistency.

**Key insight:** Remember the two parts: **P → A or C; else → L or C.**

**Key takeaway:** CAP describes the consistency--availability choice
during a partition; PACELC also calls out the latency--consistency
choice during normal operation.

## Availability and "nines"

Availability targets are often described in "nines," such as 99.9% or
99.99%. Small percentage changes can mean large differences in allowable
downtime.

  **Availability**   **Approximate downtime per year**
  ------------------ -----------------------------------
  99%                3.65 days
  99.9%              8.76 hours
  99.99%             52.56 minutes
  99.999%            5.26 minutes

Availability does not describe every part of system quality. A service
can be available while returning stale data or responding too slowly.
Consistency and latency matter too.

**Key takeaway:** When comparing availability targets, translate the
percentage into downtime; each additional nine substantially reduces the
time the system can be unavailable.

## Leader--replica architecture

The architecture discussed as **master--slave** is also commonly
described using more inclusive terms such as **leader--follower** or, in
database contexts, **primary--replica**. Responsibilities vary by
system, so follow the terminology used by your team or client.

At a high level, the leader or primary handles a coordinating role,
while followers or replicas support it. In the database model covered
here:

-   Writes go to the master or primary.
-   Reads can be served by replicas.
-   The master propagates writes to replicas.
-   A replica may be promoted if the current master fails.

A service typically needs a routing layer or load balancer that knows
which machine is the master and which are replicas. Consistent hashing
can determine **which shard** owns a data item; routing then determines
**which machine in that shard's group** handles the request.

> *A shard identifies which partition of data you need; the replica set
> gives you multiple machines that can hold or serve that partition.*

**Key takeaway:** A leader--replica design separates write coordination
from read-serving capacity, but its behavior depends on how writes are
propagated and failures are handled.

## Replication consistency and write acknowledgements

When a master receives a write, the system must decide when to report
success. The more replication the system requires before acknowledging,
the more confidence it has that copies are up to date---but the longer
the write may take.

### Acknowledge before replicas catch up

The master can store a write and return success immediately, then send
the update to replicas asynchronously.

This makes the response fast, but replicas may temporarily be stale. If
the master fails before the write reaches a replica, the acknowledged
data may be lost if the remaining copies do not contain it.

This trade-off may be acceptable for some high-volume, lower-stakes
counters, such as likes or views on a very popular video. The
acceptability depends on the consequences of losing updates.

### Wait for a threshold of replicas

Another policy is to wait for a configured number of replicas to confirm
the write before returning success. For example, with three replicas, a
system might wait for two; with 100, it might wait for 80.

This can provide a middle ground: the system need not wait for every
replica, but some replicas may still be behind when success is returned.
Reads from those replicas can temporarily return stale data.

A threshold policy does not, by itself, guarantee that a replacement
master will have every acknowledged write. Safe failover depends on how
the system chooses a new leader and what replication guarantees it
provides.

### Wait for every replica

A system can require every replica to receive the write before
acknowledging it. This provides stronger confidence that all copies are
up to date, but the application must wait for the slowest replica. If a
replica is unavailable, writes may be delayed or rejected.

A simplified model may describe aborting or undoing partial writes if
one replica fails before the write completes. In a real distributed
system, that behavior requires explicit coordination; partial changes
are not automatically rolled back.

> *A fast acknowledgement can mean the system has accepted a write
> before every copy is up to date; waiting for copies improves
> consistency but takes longer.*

**Key insight:** The acknowledgement policy determines the balance among
write latency, replica consistency, and tolerance of unavailable
replicas.

**Key takeaway:** Decide how many copies must confirm a write before
success, based on how much latency, stale reads, and data-loss risk the
application can accept.

## Why databases use multiple machines

A dataset fitting on one machine does not mean one machine is
sufficient. Storage capacity, request throughput, failure risk, and user
latency are separate concerns.

-   **Single point of failure:** If the only machine fails, the service
    may become unavailable. Copies on other machines can support
    recovery or continued service.
-   **Throughput bottleneck:** A machine can be overwhelmed by requests
    even if the data is small. For example, 1 GB of data may fit
    comfortably on one machine, while 10 million requests per second may
    exceed its capacity.
-   **Latency:** Users far from the machine may experience slower
    responses. Serving data closer to users can help reduce delay.

**Key insight:** A small dataset can still be "hot" if it receives a
large number of requests.

**Key takeaway:** Size, request volume, failures, and distance from
users can each justify using more than one machine.

## Sharding and replication

**Sharding** divides a dataset into partitions and stores those
partitions on different machines. It addresses a data-size problem.

**Replication** creates multiple copies of data, allowing requests to be
spread across machines and providing additional copies for resilience.
It addresses a query-load problem and can also support recovery.

> ***Sharding divides the data; replication copies it.***

For example, a dataset might be split by ID ranges:

``` text
Shard 1: IDs 1–25
Shard 2: IDs 26–50
Shard 3: IDs 51–75
Shard 4: IDs 76–100
```

These are different portions of the dataset. If each shard has replicas,
each replica holds a copy of that shard---not a different fraction of
it.

### Worked capacity example

Suppose the requirements are:

-   100 GB of data
-   100 million queries per unit of time
-   Each machine can store 25 GB
-   Each machine can handle 1 million queries per unit of time

Work through the constraints separately:

1.  **Storage:** 100 GB ÷ 25 GB per machine = **4 shards**.
2.  **Query capacity:** 100 million ÷ 1 million per machine = **100
    query-serving instances** for the stated load.
3.  **Traffic distribution:** No distribution across shards is
    specified, so assume any one shard could receive the full 100
    million queries.
4.  **Combined design:** Provide up to 100 query-serving instances for
    each of the four shards: **4 × 100 = 400 shard-serving instances**.

This is a conservative sizing assumption: it avoids relying on traffic
being evenly distributed across shards. Each instance serving a shard
holds a copy of that shard's 25 GB. The calculation treats 100 as the
number of query-serving instances per shard group; if "replica" means
only follower machines, the leader is an additional machine.

The example also assumes the stated query load can be served by
replicas. Writes routed to a master require separate capacity planning.

**Key insight:** Storage capacity and query capacity are different
constraints. Sharding addresses the first; replication addresses the
second.

**Key takeaway:** Calculate how many partitions you need for the data,
then size serving copies for the request load---including the
possibility that traffic concentrates on one shard.

## Read scaling, write bottlenecks, and multi-master systems

Replicas can serve reads directly, rather than routing every read
through the master. This distributes read traffic and can reduce a read
bottleneck. It also means that a read routed to a replica that has not
yet received a recent write may return stale data.

In the architecture covered here, writes go through the master. A
read-heavy workload may benefit from additional read replicas, but
adding replicas does not remove a write bottleneck at the master.

A **multi-master** setup is one possible response when a single master
cannot handle the write load. Multiple masters can accept writes, but
the system then has to coordinate updates arriving at different places,
including synchronization and conflicts.

**Key insight:** Replication can help scale reads without automatically
scaling writes. Multi-master designs may distribute writes, but add
coordination complexity.

**Key takeaway:** Match the scaling strategy to the workload: replicas
can spread reads, while write-heavy systems may need a different design
and more coordination.

## Replica placement

Place replicas according to their purpose:

-   **For load distribution:** Put replicas where request demand is
    highest. Multiple copies in the same region can help serve regional
    traffic.
-   **For backup and disaster recovery:** Put copies in geographically
    separate regions so that one regional event is less likely to affect
    every copy.
-   **For user latency:** Serve data from a region close to its users
    where appropriate.

**Key insight:** A replica intended to handle traffic and a replica
intended for disaster recovery may need different placement.

**Key takeaway:** Decide whether a replica is primarily for load,
recovery, or proximity to users; that purpose should guide where it
lives.

## Quick reference

-   **Cache strategies:** write-through, write-back, write-around; TTL
    controls how long cached entries remain; LRU, LFU, FIFO, and LIFO
    are eviction policies.
-   **CAP:** During a partition, choose between consistency and
    availability.
-   **PACELC:** During a partition, **A or C**; otherwise, **L or C**.
-   **Sharding:** Splits data across machines; use it for data-size
    constraints.
-   **Replication:** Copies data across machines; use it to distribute
    request load and support resilience.
-   **Leader--replica routing:** Writes go to the leader in the model
    covered; reads can go to replicas.
-   **Write acknowledgements:** Acknowledge early for lower latency, or
    wait for more replicas for stronger consistency.
-   **Availability "nines":** Convert the target into allowable downtime
    to understand its practical impact.
-   **Replica placement:** Same-region copies can help with load;
    cross-region copies can help with disaster recovery.
