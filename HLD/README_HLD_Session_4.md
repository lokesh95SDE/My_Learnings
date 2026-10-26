# Caching in System Design

A practical guide to caching fundamentals, consistent hashing, cache placement, TTL, invalidation, eviction, and cache write strategies.

## Table of Contents

- [1. Session Overview](#1-session-overview)
- [2. Consistent Hashing and Its Optimization](#2-consistent-hashing-and-its-optimization)
- [3. Caching Fundamentals](#3-caching-fundamentals)
- [4. Browser Caching and CDN Caching](#4-browser-caching-and-cdn-caching)
- [5. Local Caching](#5-local-caching)
- [6. Global Caching](#6-global-caching)
- [7. Cache Trade-offs](#7-cache-trade-offs)
- [8. Cache Invalidation vs. Eviction](#8-cache-invalidation-vs-eviction)
- [9. TTL-Based Cache Validity](#9-ttl-based-cache-validity)
- [10. Choosing the Right TTL](#10-choosing-the-right-ttl)
- [11. Read Path and Write Path](#11-read-path-and-write-path)
- [12. Cache Write Strategies](#12-cache-write-strategies)
  - [Write-Through](#write-through-cache)
  - [Write-Back](#write-back-cache)
  - [Write-Around](#write-around-cache)
- [13. Cache Freshness for Live Data](#13-cache-freshness-for-live-data)
- [14. When Approximation or Data Loss Is Acceptable](#14-when-approximation-or-data-loss-is-acceptable)
- [15. HLD Mindset: Trade-offs](#15-hld-mindset-trade-offs-not-one-correct-answer)
- [16. Distributed Writes, Triggers, and Sharding](#16-cache-distributed-writes-triggers-and-sharding)
- [17. Quick Reference](#17-quick-reference)

---

## 1. Session Overview

This guide covers the core caching toolkit used in system design:

- Consistent hashing
- Local caching
- Global/shared caching
- Cache staleness and invalidation
- Cache eviction
- TTL (Time To Live)
- Write-through, write-back, and write-around strategies

Caching is a balance between **freshness, speed, consistency, availability, and cost**. Understanding the trade-offs is more important than memorizing one implementation.

## 2. Consistent Hashing and Its Optimization

Consistent hashing distributes keys across servers while minimizing how much data must move when the server set changes.

### Basic lookup model

1. Store server positions in a sorted array.
2. Hash the key to a position on the hash ring.
3. Use binary search to find the nearest eligible server position.
4. Use a hash map to resolve that position to the actual server.

**Lookup complexity:** approximately `O(log n)` when searching a sorted array of server positions.

Hashing spreads keys across a large value range, helping distribute them reasonably evenly.

### Adding and removing servers

**Adding a server:**

- Add its position to the sorted array and hash map.
- Migrate only the keys or shards affected by the new position.

**Removing a server:**

- Keys mapped to the removed server must be reassigned to remaining servers.
- Poorly designed reassignment can overload nearby nodes and cause cascading failures.

One optimization is to use multiple hashes or virtual positions so that keys and replicas are distributed across several servers rather than relying on one nearby node. The number of hashes is a design choice; it is not fixed at three.

**Key takeaway:** Consistent hashing reduces remapping when membership changes. Replication, virtual nodes, and careful load balancing help reduce the risk of overload when a server disappears.

## 3. Caching Fundamentals

Caching stores data closer to where it is needed so the system does not repeatedly fetch the same data from its original source.

### Benefits

- Faster repeated access
- Lower load on the original data source
- Reduced repeated network and storage work

Caching is a **pattern**, not a specific technology. It can be used for database results, files, static assets, and frequently accessed backend data.

### Where a cache can live

- Browser/client
- CDN
- Application server
- Shared backend cache

A cache is temporary storage for repeated access. It is **not the source of truth**.

## 4. Browser Caching and CDN Caching

### Browser cache

A browser may cache resources such as:

- DNS-related information
- Images
- Stylesheets
- Other reusable client-facing resources

This reduces repeated network work for the client.

### CDN cache

A Content Delivery Network stores content closer to users in geographically distributed locations. It is commonly used for static content such as:

- Images
- Video and other bytes
- CSS and similar assets

Examples include Akamai and Cloudflare.

**Important distinction:** CDN caching is useful for static and edge-delivered content. It is not a general-purpose replacement for backend or database caching.

## 5. Local Caching

Local caching stores data on the application server itself, commonly in memory.

### Example: leaderboard

Imagine many users requesting the same leaderboard during a short period.

**Without a cache:**

1. A user requests the leaderboard.
2. The application queries the database.
3. The leaderboard is computed.
4. Every subsequent request repeats much of the same work.

**With a local cache:**

1. The first request fetches data from the database and computes the leaderboard.
2. The result is stored in the application server's cache.
3. Later requests reuse the cached result while it remains valid.

This can avoid repeated database network calls, disk I/O, and computation.

### Why local caching is fast

A useful high-level intuition for the cost of accessing data is:

1. Memory access
2. Disk or other I/O
3. Network calls

The exact performance depends on the system, but replacing a database network request and storage read with an in-memory lookup can substantially reduce latency.

### Limitations

- Cache contents may disappear when the application process restarts.
- A pod or node restart can wipe its local cache.
- Different application servers can hold different values.
- Cached values can become stale.

Local cache does not necessarily mean Redis. Redis is commonly used as a shared cache; a local in-process map or another temporary store can also serve as a cache.

**Best fit:** frequently repeated reads where low latency matters and temporary staleness is acceptable.

## 6. Global Caching

A global cache (shared cache) is accessible to multiple application servers.

### Typical request flow

1. The client request reaches a load balancer.
2. The load balancer sends it to an application server.
3. The application checks the shared cache.
4. If the value is missing or expired, the application fetches it from the database.
5. The fresh value is stored in the shared cache.
6. Later requests from any application server can reuse it.

### Example: popular content

Global caching is useful when many users request the same hot data, such as:

- Viral posts
- Popular tweets
- Celebrity content

Redis is a common fit because it is an in-memory key-value store.

### Trade-offs

- The application still makes a network request to reach the cache.
- A shared cache can reduce repeated database reads but does not eliminate every form of overhead.
- Cache failures, stale data, and consistency still need to be handled.

**Best fit:** hot data that must be reused across multiple application servers.

## 7. Cache Trade-offs

Caching requires balancing:

- Speed and latency
- Freshness
- RAM cost
- Consistency
- Availability

A cache contains a **copy** of data, not the authoritative source.

A useful analogy is a photocopy of a book: it is convenient to read, but it does not automatically change when the original book is updated.

RAM is fast but expensive, limited, and volatile. Therefore, a system cannot cache everything or treat the cache as durable storage.

**Key takeaway:** Caching improves performance, but the design must account for stale copies and limited memory.

## 8. Cache Invalidation vs. Eviction

These are different problems.

| Concept | Question it answers | Purpose |
|---|---|---|
| **Cache invalidation** | When is this cached value no longer trustworthy? | Preserve freshness and correctness |
| **Cache eviction** | Which entry should be removed when space is limited? | Manage cache capacity |

A cache needs both a freshness strategy and a space-management strategy.

## 9. TTL-Based Cache Validity

TTL means **Time To Live**: how long a cached entry is considered valid.

### Read flow

1. Check the cache.
2. If the entry exists and has not expired, return it.
3. If the entry is missing or expired, fetch fresh data from the database.
4. Store the fresh value in the cache with a new TTL.
5. Return the fresh value.

### Example: view count

Suppose a view count is cached with a TTL of five seconds.

- The first request misses the cache, reads the database, and caches the value.
- Requests during the next five seconds reuse the cached value.
- After expiration, a request refreshes the value from the database and stores it again.

TTL is a cache-level rule that defines how long a value may be trusted.

### When TTL is useful

- Live viewer counts
- Dashboards
- Last-known location updates
- Frequently updated data where slight staleness is acceptable

**Warning:** TTL alone is not appropriate when exact, real-time correctness is required.

## 10. Choosing the Right TTL

There is no universal TTL value. Choose it based on:

- How fresh the data must be
- How much staleness the business can tolerate
- Traffic volume
- Whether reads repeat or are mostly unique
- The cost of refreshing the data

A short TTL can work well when many requests repeatedly read the same data and a little staleness is acceptable.

If every request reads a different value, a short TTL may cause frequent refreshes without much benefit.

**System-design principle:** Do not justify a TTL only by saying the system is read-heavy. Explain the repetition pattern, refresh cost, and business freshness requirement.

## 11. Read Path and Write Path

### Read path

```text
Client
  |
  v
Application
  |
  v
Check cache
  |             \
  | hit          \ miss or expired
  v               v
Return cached    Read database
value              |
                   v
                Update cache
                   |
                   v
                Return value
```

### Write path

Create, update, and delete operations must account for the fact that a database write can make a cached copy stale.

The database is the source of truth in the model described here. The system must explicitly decide how cache entries are updated, invalidated, or refreshed after writes.

A cache miss can mean either:
- The value has never been cached.
- The cached value has expired or been removed.

## 12. Cache Write Strategies

### Write-Through Cache

In write-through caching, the write updates the cache and the database as part of the same logical operation.

**Conceptual flow:**

1. The application receives a write.
2. The cache is updated.
3. If the cache write fails, the operation fails.
4. The database is updated.
5. If the database write fails, the cache entry is rolled back or removed.

The exact ordering and failure-handling mechanism depend on the implementation; coordinating two separate systems is not automatically an atomic transaction.

**Example:** A balance value that must not casually become stale.

**Advantages**
- Keeps cache and database closely aligned when failure handling is implemented correctly.
- Can provide fast subsequent reads.

**Trade-offs**
- Writes are slower because the cache and database both need to be handled.
- Failure recovery and rollback behavior must be designed.

**Best fit:** workloads where stale values are risky and correctness is more important than minimum write latency. Critical financial operations still require authoritative database transactions and appropriate consistency controls; a cache alone does not guarantee correctness.

### Write-Back Cache

In write-back caching, the application writes to the cache first and persists the update to the database asynchronously.

**Conceptual flow:**

1. The client sends a write request.
2. The application writes to the cache.
3. The client receives success.
4. A background process writes the update to the database.

**Advantages**
- Low write latency from the client's perspective.
- Can absorb high write volumes.

**Risks**
- A background database write can fail after the cache has accepted the write.
- Cache failure before persistence can lead to inconsistency or data loss unless the design includes durable buffering and recovery.

Examples discussed include YouTube-like like counters and other high-volume counts where a small amount of loss or approximation may be acceptable.

**Avoid for:** banking transfers and other critical transactional data unless a separate durable, reliable mechanism guarantees the required persistence and correctness.

### Write-Around Cache

In write-around caching, the application writes directly to the database and skips the cache during the write.

**Conceptual flow:**

1. The client sends a write request.
2. The application updates the database.
3. The cache is not updated as part of that write.
4. A later read repopulates the cache or an invalidation mechanism removes the old value.

**Advantages**
- Avoids filling the cache with data that may not be read again soon.
- Keeps the write path focused on the database.

**Trade-offs**
- The cache may continue to hold an old value unless it is invalidated or refreshed.
- The first read after a write may require a database fetch.

**Best fit:** write-heavy workloads where recently written data is not immediately read frequently.

### Comparison of the three strategies

| Strategy | Write behavior | Main benefit | Main risk / cost |
|---|---|---|---|
| **Write-through** | Update cache and database in the write path | Cache and database can stay closely aligned | Higher write latency; cross-system failure handling |
| **Write-back** | Update cache first; database update happens asynchronously | Lowest perceived write latency | Potential inconsistency or data loss |
| **Write-around** | Write directly to database; skip cache | Avoids unnecessary cache writes | Cache can remain stale until invalidated or refreshed |

These strategies are independent of whether the cache is local or shared. Choose based on the workload's correctness, freshness, and latency requirements.

## 13. Cache Freshness for Live Data

For values such as viewer counts or location updates, the application may not need an exact value at every instant.

Examples:
- Live viewer count on a streaming app
- Ride-hailing location tracking
- Live metrics

Define an acceptable **staleness window**:

- Small staleness may be acceptable.
- Large divergence may not be acceptable.

In many systems, “live” means “recent enough” rather than mathematically exact. The business requirement should determine the allowed freshness window.

## 14. When Approximation or Data Loss Is Acceptable

Some systems can tolerate approximate results or a small amount of lost data.

### Example: search suggestions

The system may care more about the relative popularity of suggestions than exact totals. If one suggestion is clearly more popular than another, an approximate count may be sufficient.

This can allow more aggressive caching and asynchronous updates.

**Key takeaway:** The more tolerant a product is of approximation, the more flexibility the system has in caching and write design. This tolerance must be explicitly established rather than assumed.

## 15. HLD Mindset: Trade-offs, Not One Correct Answer

High-level design is trade-off driven. A caching design often balances:

- Freshness
- Latency
- Throughput
- Storage and RAM cost
- Consistency
- Availability

You generally cannot optimize all of these at once. The same caching strategy may be appropriate for one use case and wrong for another.

When explaining a design, state:
1. The data access pattern.
2. The required freshness and consistency.
3. The expected latency and throughput.
4. The cost and failure trade-offs.
5. Why the selected strategy fits the use case.

## 16. Distributed Writes, Triggers, and Sharding

Database triggers operate within their database context. In a distributed system, data may be split across shards, and a trigger on one shard does not naturally coordinate a multi-shard workflow.

Cross-shard updates can become difficult and inefficient when coordination is delegated only to database triggers.

**Guidance:** Orchestrate complex multi-entity or cross-shard write flows in application-level logic, with explicit handling for failures and consistency. Triggers may still be useful for local database responsibilities, but they are not a complete distributed transaction strategy.

## 17. Quick Reference

| Topic | Remember |
|---|---|
| **Consistent hashing** | Distributes keys while minimizing remapping when servers change |
| **Local cache** | Stored on an application server; fast but volatile |
| **Global cache** | Shared across application servers; useful for shared hot data |
| **TTL** | Defines how long a cached entry is considered valid |
| **Cache invalidation** | Determines when cached data is no longer trustworthy |
| **Cache eviction** | Removes entries when capacity is needed |
| **Write-through** | Cache and database are updated in the write path; higher write latency |
| **Write-back** | Cache first, database later; fast but requires careful durability and recovery |
| **Write-around** | Write to database while skipping cache; cached data may become stale |
| **Good cache candidates** | Repeated reads, hot data, and use cases with a defined staleness tolerance |
| **Access-cost intuition** | Memory access is generally cheaper than storage I/O and network round trips |
| **Main TTL question** | How much staleness can the business tolerate? |

---

## Final Mental Model

Before choosing a cache strategy, ask:

1. **What is being cached?** Static assets, query results, counters, or transactional data?
2. **Who needs it?** One application process or many application servers?
3. **How often is it reused?** Repeated reads or mostly unique requests?
4. **How fresh must it be?** What staleness window is acceptable?
5. **How are writes handled?** Write-through, write-back, write-around, invalidation, or refresh?
6. **What happens on failure?** Can the system recover without losing critical data?
7. **What is the trade-off?** Latency, consistency, throughput, availability, and cost.

**The best caching design is the one whose trade-offs match the product's requirements—not the one that caches the most data.**
