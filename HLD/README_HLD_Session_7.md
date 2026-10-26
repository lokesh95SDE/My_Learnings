# Caching Strategies and CAP Theorem

A beginner-friendly guide to cache design, cache consistency, eviction policies, and distributed-system trade-offs.

## Table of Contents

1. [Caching: Purpose and Fundamentals](#1-caching-purpose-and-fundamentals)
2. [Local Cache vs. Global Cache](#2-local-cache-vs-global-cache)
3. [TTL-Based Caching](#3-ttl-based-caching)
4. [Cache Hits, Misses, and Eviction](#4-cache-hits-misses-and-eviction)
5. [Cache Eviction Policies](#5-cache-eviction-policies)
6. [Cache Write Strategies](#6-cache-write-strategies)
7. [Keeping Cache Data in Sync](#7-keeping-cache-data-in-sync)
8. [Database Caching and Temporary Tables](#8-database-caching-and-temporary-tables)
9. [Choosing a Caching Strategy at Scale](#9-choosing-a-caching-strategy-at-scale)
10. [CAP Theorem](#10-cap-theorem)
11. [Understanding Distribution with a Diary Example](#11-understanding-distribution-with-a-diary-example)
12. [Replication and Network Partitions](#12-replication-and-network-partitions)
13. [Consistency vs. Availability During a Partition](#13-consistency-vs-availability-during-a-partition)
14. [Applying CAP to Real Products](#14-applying-cap-to-real-products)
15. [Quick Reference](#15-quick-reference)

---

## 1. Caching: Purpose and Fundamentals

Caching avoids repeatedly fetching or calculating expensive data. Frequently requested information is stored in a faster layer—usually memory—so subsequent requests can reuse it.

### Why caching helps

A rough storage-speed order is:

**Memory (RAM) > SSD > HDD**, while network access also introduces latency.

For example, a frequently requested leaderboard can be calculated once and cached rather than regenerated for every request. This reduces repeated database reads, network overhead, and computation.

### Main cache approaches

- **Local cache:** Stored inside an application server.
- **Global cache:** Stored in a separate shared service, such as Redis.
- **TTL/invalidation-based cache:** Cached entries expire or are invalidated and then refreshed.

**Key takeaway:** Caching moves frequently used data closer to the application to make repeated reads cheaper.

## 2. Local Cache vs. Global Cache

| Aspect | Local cache | Global cache |
|---|---|---|
| Location | Inside each application server | Separate shared cache service |
| Read speed | Very fast; no separate cache network call | Requires a call to the cache service |
| Sharing | Each server has its own copy | Multiple servers share the same cache |
| Main advantage | Low-latency access | Easier to share a common cached view |
| Main drawback | Data can be duplicated or diverge between servers | Adds a network hop and shared-service dependency |
| Example | In-process memory cache | Redis |

Use a local cache when very low latency is important and duplicated/stale copies are acceptable. Consider a global cache when many application servers need to reuse the same cached values.

## 3. TTL-Based Caching

**TTL (Time to Live)** defines how long a cached entry is considered valid.

### Example: A score with a 5-second TTL

1. The application reads the score from the cache.
2. While the entry is valid, requests can reuse it.
3. After five seconds, the entry expires.
4. The next request fetches the current value from the database and repopulates the cache.

TTL provides freshness through expiry; it does **not** synchronize the cache and database immediately. A cached value may be stale until it expires or is invalidated.

**Key takeaway:** TTL is simple and useful when a short period of staleness is acceptable.

## 4. Cache Hits, Misses, and Eviction

- **Cache hit:** The requested item is already in the cache.
- **Cache miss:** The requested item is not in the cache.

### Basic read-through flow

1. Check the cache.
2. If the item is present, return it.
3. If it is missing, fetch it from the database.
4. Store the fetched value in the cache.
5. Return the value to the caller.

For example, the first request for key `93` may miss and fetch the value from the database. The application then caches it. Later requests for key `93` can become cache hits and avoid another database read.

### Why cache capacity is limited

Memory is expensive and finite. A cache cannot always hold every possible item. When it becomes full, a system generally either ignores a new item or evicts an existing item to make room.

**Key takeaway:** Eviction is necessary because cache capacity is limited.

## 5. Cache Eviction Policies

| Policy | Rule | Useful when | Limitation |
|---|---|---|---|
| **LRU — Least Recently Used** | Evict the item that has not been accessed for the longest time | Recently used items are likely to be used again | Needs recency/access metadata |
| **LFU — Least Frequently Used** | Evict the item with the fewest accesses | Frequently accessed items should remain cached | Needs frequency metadata; older popularity can influence decisions |
| **FIFO — First In, First Out** | Evict the item inserted earliest | Older entries are less useful than newer entries | Ignores how often or recently an item was accessed |
| **LIFO — Last In, First Out** | Evict the most recently inserted item | Only when the workload specifically benefits from this behavior | Less common for typical application caches |

There is no universally best eviction policy. Choose based on the workload and measure which policy reduces cache misses.

### Worked example: IPL match winners

Imagine a cache that can store only 10–20 entries, while the league has 40–50 matches. If users mostly ask about the newest match results, older entries may be less useful. FIFO can be a reasonable choice because it removes the oldest inserted entries and makes room for newer results.

This is a workload-specific heuristic, not a universal rule: if users repeatedly look up older matches, LRU or another policy may be more suitable.

**Rule of thumb:** Optimize for the common access pattern rather than a rare edge case.

## 6. Cache Write Strategies

A write can mean creating, updating, or deleting data. Cache write strategies determine how writes interact with the database and cache.

| Strategy | Write path | Main benefit | Main trade-off |
|---|---|---|---|
| **TTL-based caching** | Write to database; cache expires later | Simple write path | Cached data may remain stale until expiry |
| **Write-through** | Update cache and database as part of the write path | Updated cache values are available promptly after a successful write | Writes are slower because both layers must be updated |
| **Write-back** | Write to cache first; database is updated asynchronously | Very fast acknowledgement | Risk of data loss if pending database writes fail; cache and database can temporarily disagree |
| **Write-around** | Write directly to database; cache is populated on reads | Avoids caching data that may never be read | A later read may miss the cache and need a database fetch |

### TTL-based caching

Writes go directly to the database. Reads check the cache first and fetch from the database on a miss. If the cache contains an older value, it may be returned until expiry or invalidation.

### Write-through

The cache and database are updated during the write operation. This can keep the cached value aligned with the database at write time, assuming the implementation handles failures correctly. The extra work can increase write latency.

### Write-back

The application writes to the cache first and the database is updated later. The caller may receive success before the database has been updated. This improves write latency but requires careful handling of retries, failures, and durability.

### Write-around

Writes bypass the cache and go directly to the database. The cache is populated only when data is read. This is useful for write-heavy data that is unlikely to be read immediately or frequently.

### Consistency terminology

- **Consistent/up to date:** The value being served meets the system's required freshness guarantee.
- **Eventual consistency:** Replicas or cached copies may temporarily differ but are expected to converge.
- **Temporary inconsistency:** Components are out of sync at a particular moment.

These terms describe application/distributed-data behavior here; they are not the same as **ACID database consistency**.

**Key takeaway:** Cache write strategies trade off speed, freshness, and durability. Write-through favors prompt cache updates; write-back favors write speed but has greater durability risk; TTL permits stale values until refresh; write-around avoids filling the cache on every write.

## 7. Keeping Cache Data in Sync

Cached data can drift from its source of truth. The synchronization approach should follow the application's requirements:

- **Immediate freshness:** Use a write/invalidation design that updates or invalidates cached values as part of the relevant operation.
- **Eventual refresh:** TTL may be sufficient if temporary staleness is acceptable.
- **Temporary inconsistency by design:** Some systems accept delayed updates in exchange for speed or resilience.

No single synchronization policy fits every system. Decide what level of staleness the product can tolerate.

## 8. Database Caching and Temporary Tables

Databases already use internal optimizations, including caches and metadata about pages, indexes, and access paths. These are not necessarily the same as an application-level cache of complete query results.

### Internal database optimizations vs. application caching

| Internal database optimizations | Application-level/custom caching |
|---|---|
| May cache internal pages or metadata | Stores reusable results for repeated application requests |
| Helps the database execute operations efficiently | Can avoid a database read entirely when a cached result is valid |
| Managed by the database engine | Usually requires application-level design and invalidation/expiry rules |

### Temporary tables

A temporary table can help when the same subset of a large dataset is reused repeatedly within a transaction or workflow.

Typical pattern:

1. Create a temporary table.
2. Populate it with the required subset.
3. Reuse that subset for multiple operations.
4. Drop the table or allow it to disappear according to its lifecycle.

Temporary tables and custom caching introduce lifecycle and cleanup responsibilities. Use them when repeated work is a demonstrated bottleneck, not automatically.

## 9. Choosing a Caching Strategy at Scale

When the access pattern is unclear, observe real usage before committing to a complex design.

For example, during a large sale, monitor:

- Which products are browsed most often.
- Which searches repeat.
- Which pages receive frequent requests.
- Which cached items produce the most hits and misses.

A good design decision should include alternatives, explain their pros and cons, and justify the best fit for the requirements. Trial, measurement, and refinement are often necessary.

**Key takeaway:** Choose caching policies based on observed access patterns, not guesswork.

---

## 10. CAP Theorem

CAP stands for:

- **Consistency (C):** Nodes do not expose conflicting outcomes for the relevant operation; in the common simplified explanation, clients see a consistent view of data.
- **Availability (A):** Every request to a non-failing node receives a response, though that response need not always be a success.
- **Partition tolerance (P):** The system continues operating despite communication failures that split nodes into groups that cannot communicate.

A **network partition** is a communication break between parts of a distributed system. Partition tolerance is the ability to keep operating in the presence of such a break.

### The core CAP trade-off

When a network partition occurs, a distributed system cannot guarantee both consistency and availability for every request. It must decide whether to reject or delay some operations to preserve consistency, or respond using the reachable portion of the system and risk stale or conflicting data.

| Choice during a partition | Typical behavior |
|---|---|
| **Consistency + Partition tolerance (CP-style choice)** | Some requests may be rejected or delayed rather than risk conflicting state |
| **Availability + Partition tolerance (AP-style choice)** | Requests may be served by reachable nodes, potentially with stale or divergent data |

CAP is about behavior **during a partition**, not a blanket claim that a system can never provide consistency and availability during normal operation.

**Important distinction:** A response does not have to be successful for the service to have responded. For example, an error response is still a response; availability is not the same as guaranteed success.

## 11. Understanding Distribution with a Diary Example

Imagine a reminder service:

1. A customer tells Sumit a note, and Sumit writes it in his diary.
2. The service grows, so Garima joins and keeps a separate diary.
3. The customer tells Sumit something, but the note is written only in Sumit's diary.
4. Later, the customer asks Garima, who does not have the note.

This illustrates a distributed-system problem: one node has data that another node has not received. Once data is distributed across nodes, each node cannot assume that it has the complete, current state.

A shared notebook does not automatically solve the ongoing problem. The system still needs a way to coordinate updates and handle situations where nodes cannot communicate.

**Key takeaway:** Distribution creates coordination challenges because different nodes can temporarily see different versions of the data.

## 12. Replication and Network Partitions

Suppose Sumit must write to both diaries before confirming that a reminder was saved.

If Sumit writes locally but the network connection fails before Garima's diary is updated, the system must decide what to do:

- **Reject or delay the request:** Do not confirm until the required replicas are updated.
- **Accept the request locally:** Respond immediately, even though another replica has not yet received the update.

The first approach protects the chosen consistency guarantee but may reduce availability during a partition. The second keeps the service responsive but can leave replicas temporarily inconsistent.

**Key takeaway:** Replication makes communication failures part of the product's behavior, not merely an infrastructure concern.

## 13. Consistency vs. Availability During a Partition

### If consistency is prioritized

The system may refuse a write unless the required components can be updated. During a partition, this can mean returning an error or waiting rather than risking conflicting state.

### If availability is prioritized

The system may accept a request and write to the nodes it can reach. It remains responsive, but replicas may temporarily disagree. Reconciliation or replication can bring them back into sync later, depending on the design.

A similar issue can occur with a load balancer, two application servers, and separate databases: one server may save a write locally but lose connectivity before propagating it to the other database. The second server may then report that it does not have the data.

**Key takeaway:** During a partition, decide deliberately whether correctness guarantees or responsiveness should take priority for the operation.

## 14. Applying CAP to Real Products

The right trade-off depends on what correctness means for the product.

| Product/use case | Typical priority | Reasoning |
|---|---|---|
| **Banking and money transfers** | Strong consistency for critical monetary operations | A debit without the corresponding credit, or a duplicated transfer, is unacceptable. Rejecting or delaying a transaction can be safer than accepting conflicting state. |
| **Discussion/content apps** | Often favor availability for non-critical reads | Showing the available comments or content can be more useful than blocking the entire page because one item is unavailable. |
| **Social feeds** | Availability with eventual consistency is often acceptable | A feed can show available content while updates propagate in the background. Small delays may be acceptable to users. |
| **Messaging apps** | Prioritize correct delivery, recipient, ordering, and trustworthy acknowledgements | Messages should not be corrupted, sent to the wrong recipient, or presented in a confusing order. Presence/status may have different freshness requirements from message delivery. |

### Messaging: product context matters

Consumer messaging and corporate collaboration tools may have different fallback options and user expectations. For example, users of a workplace collaboration tool may have email or another channel available, while consumer users may depend more heavily on the messaging app. These are design considerations, not universal classifications: actual behavior depends on the product's architecture and guarantees.

### Design questions to ask

When choosing a consistency/availability approach, ask:

1. What must never be wrong?
2. Is stale data acceptable, and for how long?
3. Can a request be rejected or delayed safely?
4. What should the user see during a network partition?
5. How will replicas recover or reconcile after connectivity returns?

---

## 15. Quick Reference

### Cache strategies

| Concept | Quick definition |
|---|---|
| Local cache | Fast, per-application-server cache; copies can diverge |
| Global cache | Shared external cache, such as Redis |
| TTL | Entry expires after a configured time; refresh is not immediate |
| Write-through | Update cache and database as part of the write path |
| Write-back | Cache first, database asynchronously; fast but durability-sensitive |
| Write-around | Write to database; populate cache on reads |

### Cache states and eviction

| Concept | Quick definition |
|---|---|
| Cache hit | Requested data is present |
| Cache miss | Requested data is absent |
| LRU | Evict least recently used |
| LFU | Evict least frequently used |
| FIFO | Evict oldest inserted |
| LIFO | Evict newest inserted |

### CAP theorem

| Concept | Quick definition |
|---|---|
| Consistency | Preserve the required consistent view of data |
| Availability | Requests receive responses from non-failing nodes |
| Partition tolerance | Continue operating despite communication breaks |
| CP-style behavior | During a partition, some requests may be rejected/delayed to preserve consistency |
| AP-style behavior | During a partition, respond from reachable nodes while tolerating possible stale/divergent data |

### Final takeaways

- Cache frequently accessed data to reduce repeated work and database load.
- Select eviction and write strategies based on access patterns and freshness requirements.
- TTL provides refresh by expiry, not instant synchronization.
- Write-back needs special attention to durability and failed asynchronous writes.
- CAP trade-offs become critical during network partitions.
- Banking operations often need stronger consistency; feeds can often tolerate eventual consistency.
- Always explain alternatives and trade-offs when designing a system.

---

*Prepared from the session notes on caching strategies and CAP theorem.*
