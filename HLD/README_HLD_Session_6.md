# System Design Notes: Caching and Consistent Hashing

> A practical summary of caching fundamentals, cache placement,
> freshness, invalidation, eviction, write strategies, and consistent
> hashing.

## Table of Contents

-   [Session Overview](#session-overview)
-   [Consistent Hashing and Its
    Optimization](#consistent-hashing-and-its-optimization)
-   [Caching
    Fundamentals](#caching-fundamentals-why-it-exists-and-where-it-can-live)
-   [Browser and CDN Caching](#browser-caching-and-cdn-caching)
-   [Local Caching](#local-caching)
-   [Global Caching](#global-caching)
-   [Cache
    Trade-offs](#cache-trade-offs-staleness-ram-cost-and-source-of-truth)
-   [Invalidation vs. Eviction](#cache-invalidation-and-cache-eviction)
-   [TTL and Choosing a TTL](#ttl-based-cache-validity)
-   [Read and Write Paths](#read-path-and-write-path-around-cache)
-   [Write-Through](#write-through-cache)
-   [Write-Back](#write-back-cache)
-   [Write-Around](#write-around-cache)
-   [Comparison of Write
    Strategies](#comparing-the-three-write-strategies)
-   [Freshness for Live Data](#cache-freshness-for-live-data)
-   [When Approximation Is Acceptable](#when-data-loss-is-acceptable)
-   [HLD Mindset](#hld-mindset-trade-offs-not-one-correct-answer)
-   [Distributed Writes and
    Triggers](#cache-distributed-writes-and-triggers)
-   [Quick Reference](#quick-reference)

## Session Overview

This section covered the core caching toolkit used in system design:
consistent hashing, local caching, global caching, and the big
trade-offs around staleness, invalidation, eviction, and write
strategies. You also saw how caching connects to performance intuition:
memory vs I/O vs network, and why cache design is always a balance
between freshness, speed, consistency, and cost. The later part
introduced TTL-based cache validity and the three main write patterns:
write-through, write-back, and write-around.

## Consistent Hashing and Its Optimization

Consistent hashing is a way to distribute keys across servers while
minimizing how much data moves when the server set changes. The core
mechanics discussed were:

Server positions are stored in an array. A binary search finds the
nearest server position. A hash map maps that position to the actual
server. Lookup is roughly O(log n). The key appeal is that keys are
spread fairly evenly because hashing adds randomness over a large value
range.

> **Key insight: The hard part is not lookup --- it is handling server
> removal without causing a chain reaction.**

Adding a server is straightforward:

-   add its position to the array and hash map
-   migrate only the affected shards Deletion is trickier because nearby
    keys may suddenly depend on remaining nodes, which can lead to
    cascading failure.

To reduce that risk, an optimized consistent hashing approach uses
multiple hashes so replicas/shards are spread across several servers
instead of depending on just one nearby node.

> ⚠️ **Watch out: The number of hashes is just a design choice; it is
> not fixed at 3.**

> **Key takeaway: Consistent hashing makes server changes less
> disruptive, and multiple hashes help make deletion safer.**

## Caching Fundamentals: Why It Exists and Where It Can Live

Caching means storing data closer to where it is needed so you don't
have to repeatedly hit the original source.

The main benefits are:

faster repeated access lower load on the original source Caching is not
limited to databases. It can be used for:

file storage static assets repeated-access backend data

> **Key insight: Cache is a pattern, not a specific technology.**

A cache can exist at several layers:

browser/client layer CDN layer application server layer shared backend
layer The important mental model is that cache is temporary storage for
repeated access, not the source of truth.

> **Key takeaway: Cache is about reducing repeated work against the
> original source.**

## Browser Caching and CDN Caching

Browser caching stores things like:

DNS values images stylesheets So the browser can reuse them without
repeated network work.

A CDN (Content Delivery Network) stores content closer to users across
the world and is mainly used for static content:

images videos / bytes CSS and similar assets Examples mentioned were
Akamai and Cloudflare.

> **Key insight: CDN caching is best understood as caching static
> assets, not general database data.**

> ⚠️ **Watch out: Do not treat CDN caching as a general-purpose
> replacement for backend caching.**

> **Key takeaway: Browser and CDN caching help with client-facing static
> content and repeated network fetches.**

## Local Caching

Local caching means caching data on the application server itself,
usually in memory.

This is useful when many users ask for the same data repeatedly. The
classic example was a leaderboard:

a user submits a solution the app server reads the data from the
database the leaderboard is computed many users request the leaderboard
in a short time window Without caching, the database gets hit repeatedly
for the same result. With local caching:

the first request fetches from the database the result is stored in
app-server cache later requests are served from memory That removes:

the database network call the database disk read / I/O a lot of response
latency

> **Key insight: Local cache is most valuable when the same data is
> requested repeatedly in a short time window.**

### Why it is fast

The rough performance order given was:

Memory I/O / disk Network The practical intuition is simple:

If you can replace a network call and disk read with a memory lookup,
you skip the slowest parts of the path.

### What local cache is not

Local cache is not necessarily Redis, and it does not have to be
memory-only in a strict sense. Anything that temporarily stores
repeated-use data to avoid fetching from the original source can play
the cache role.

### Limitations

If the cache is stored in application server memory:

a restart wipes it the cache is lost on pod/node restart \> ⚠️ **Watch
out: If the server restarts frequently, that is usually a system design
problem, not a caching feature.**

> **Key takeaway: Local caching is fast and simple, but it is volatile
> and can become stale.**

## Global Caching

Global caching means multiple application servers read from a shared
cache rather than each server repeatedly querying the database.

The typical flow is:

-   client request goes through a load balancer
-   a request reaches one of several app servers
-   the app server checks the shared cache
-   if needed, it falls back to the database This is useful for hot data
    accessed by many users, like:

viral posts popular tweets celebrity content A common flow:

first request fetches the data from the database the result is stored in
the global cache later requests reuse the cached value The main gain is
not eliminating all network cost --- the request still has to reach the
cache --- but reducing repeated database disk reads.

> **Key insight: Global caching helps most when many machines need the
> same hot data.**

A common fit for this pattern is Redis, because it is an in-memory
key-value store.

> ⚠️ **Watch out: Shared cache does not remove all overhead, and it
> still needs a plan for failures and consistency.**

> **Key takeaway: Global caching is for shared hot data and mainly saves
> repeated database reads.**

## Cache Trade-offs: Staleness, RAM Cost, and Source of Truth

Caching is always a trade-off. The main tension is between:

speed freshness memory cost consistency

> **Key insight: Cache is a copy, not the source of truth.**

That means cached data can become stale when the original data changes.
Different servers may temporarily hold different versions of the same
data.

A useful analogy given was a photocopy of a book:

it is useful but if the original changes, the photocopy does not
automatically update Most caches live in RAM because speed matters, but
RAM is:

expensive limited volatile So you cannot store everything in cache, and
you cannot rely on it as durable storage.

> **Key takeaway: Caching improves performance, but you must design for
> staleness and limited memory.**

## Cache Invalidation and Cache Eviction

Two different problems come up once you cache data:

Cache invalidation This is about deciding when cached data is no longer
trustworthy and must be refreshed.

Cache eviction This is about removing cached entries when space runs
out.

> **Key insight: Cache is useful only if you have a freshness strategy
> and a space-management strategy.**

> ⚠️ **Watch out: Invalidation is about correctness; eviction is about
> capacity.**

> **Key takeaway: Every cache needs rules for both freshness and memory
> pressure.**

## TTL-Based Cache Validity

TTL (Time To Live) is the amount of time a cached entry is considered
valid.

The read flow is:

-   check cache
-   if the entry exists and is still within TTL, return it
-   if it is missing or expired, fetch fresh data from the database
-   store the fresh value back into cache with a new TTL A walkthrough
    used a score/view-count style example:

first request misses cache app fetches data from DB value is stored in
cache with a TTL like 5 seconds a later request within TTL reuses the
cached value once TTL expires, the system refreshes it again

> **Key insight: TTL is a cache-level rule for how long a value may be
> trusted.**

This is especially useful when:

the data changes often slight staleness is acceptable backend load needs
to stay low Examples included:

live viewer counts live dashboards last-known location style updates \>
⚠️ **Watch out: Don't use TTL blindly when exact real-time correctness
is required.**

> **Key takeaway: TTL lets you trade perfect freshness for lower backend
> load.**

## Choosing the Right TTL

There is no universal TTL value. The right TTL depends on:

how fresh the data must be how much staleness is acceptable traffic
volume whether reads are repeated or unique how expensive refreshes are
A short TTL can be useful when:

many requests repeat the same data is read again and again some
staleness is fine But if every read is unique, a short TTL may force
constant refreshes and bring little benefit.

> **Key insight: "Read-heavy" alone is not enough --- you need to know
> whether the reads are repeated or unique.**

A strong system-design answer is to frame TTL as a business decision,
not a random number.

> **Key takeaway: TTL should be chosen from usage patterns and freshness
> requirements, not guesswork.**

## Read Path and Write Path Around Cache

For reads, the normal model is:

check cache first if valid, return cached value otherwise fetch from
database and repopulate cache For writes --- create, update, delete ---
the database is the source of truth. A write can make the cache stale
unless the system explicitly handles synchronization.

> **Key insight: A cached item is valid only if it exists and its TTL is
> still live.**

> ⚠️ **Watch out: A cache miss can mean either "not stored yet" or
> "expired already."**

> **Key takeaway: Read behavior is cache-first; write behavior
> determines whether cache stays in sync.**

## Write-Through Cache

In write-through caching, the system writes to the cache first, then
persists the same write to the database.

The flow is:

request reaches the app server cache is updated if cache write fails,
the operation fails database is updated if DB write fails, the cache
entry is rolled back or removed This keeps cache and database aligned
tightly.

> **Key insight: Write-through is the choice when you want cache speed
> without losing consistency.**

A read still works the usual way:

-   cache hit → return immediately
-   cache miss → read DB, store in cache, return A worked example used a
    balances table:

user 101 balance 4 lakhs cache miss on read DB returns 4 lakhs cache is
filled later reads come from cache This approach is especially suitable
when stale values are risky, such as:

banking balances financial data Trade-off: writes are slower because
every update involves both cache and database.

> **Key takeaway: Write-through gives strong consistency at the cost of
> slower writes.**

## Write-Back Cache

In write-back caching, the app writes to the cache first, returns
success immediately, and updates the database later asynchronously.

The flow is:

-   client sends write request
-   app writes to cache
-   client gets success immediately
-   database is updated in the background

> **Key insight: From the client's perspective, the write is done once
> the cache accepts it.**

This is faster because the request does not wait for the database.

### Risks

If the background DB write fails after the cache write succeeds, you can
get:

inconsistency permanent data loss That is why this only works when some
loss is acceptable.

Examples that were mentioned:

YouTube-like like counters other high-volume counts where a small loss
does not matter much \> ⚠️ **Watch out: Write-back is not suitable for
banking transfers or other critical transactional data.**

The session also linked this to availability:

99% 99.9% 99.99% The point was that if downtime or occasional loss is
acceptable, write-back may be usable. If not, it is dangerous.

> **Key takeaway: Write-back is fastest, but it is only safe when losing
> some writes is acceptable.**

## Write-Around Cache

In write-around caching, the write goes directly to the database, and
the cache is skipped.

> **Key insight: "Around" means you go around the cache, not through
> it.**

The flow is:

-   client sends write request
-   app writes directly to the database
-   cache is not updated during the write This means the cache may
    remain stale until the next read repopulates it or until
    invalidation happens.

This strategy is similar to the TTL-based behavior discussed earlier:

write hits DB cache may still hold old data next read misses or
refreshes and repopulates

> **Key takeaway: Write-around avoids cache writes during updates, but
> the cache may become stale.**

## Comparing the Three Write Strategies

Write-through cache first, then database strong consistency slower
writes Write-back cache first database later asynchronously fastest
writes weaker consistency and possible data loss Write-around write goes
directly to database cache is skipped cache may stay stale until
refreshed later

> **Key insight: The choice is really about balancing consistency vs
> speed.**

> ⚠️ **Watch out: These strategies are independent of cache type ---
> they can be used with local cache or global cache.**

> **Key takeaway: Pick the write strategy based on whether correctness
> or write latency matters more.**

## Cache Freshness for "Live" Data

For data like viewer counts or "live" metrics, the system often does not
need exact current values every second. A last known value is usually
enough.

Examples mentioned:

live viewer count on a streaming app ride-hailing location tracking The
key idea is to define an acceptable staleness window:

small staleness is okay large divergence is not

> **Key insight: In many real systems, "live" means "recent enough," not
> mathematically exact.**

> **Key takeaway: Freshness requirements are business decisions, not
> purely technical ones.**

## When Data Loss Is Acceptable

Some systems can tolerate approximate results or even small amounts of
lost data.

A useful example was search suggestions:

the system cares about relative popularity, not exact totals if one
suggestion is clearly more popular, that is enough That makes aggressive
caching acceptable because precision is less important than ranking.

> **Key insight: If your system is okay with approximate results,
> caching can be much more aggressive.**

> **Key takeaway: The more tolerant the product is of approximation, the
> more caching freedom you have.**

## HLD Mindset: Trade-Offs, Not One Correct Answer

A major theme throughout the session was that high-level design is
trade-off driven.

You usually have to balance:

freshness latency throughput storage cost consistency availability

> **Key insight: In HLD, you usually cannot optimize everything at
> once.**

That is why the same caching design may be great in one scenario and
wrong in another.

> **Key takeaway: System design is about choosing the right compromise
> for the use case.**

## Cache, Distributed Writes, and Triggers

A question came up about complex writes across tables, joins, and
triggers.

The important distinction was that database triggers are limited to one
database context. In distributed systems:

data may be sharded triggers do not naturally coordinate across shards
cross-shard updates become awkward and inefficient

> **Key insight: In distributed systems, database triggers are not
> enough to manage cross-shard consistency cleanly.**

The guidance was to handle complex write flows at the application level,
not depend solely on DB triggers.

> **Key takeaway: Cross-shard or multi-entity write orchestration
> belongs in application logic, not just database triggers.**

## Quick Reference

Consistent hashing: distribute keys across servers with minimal
remapping when nodes change Local cache: cache on the application
server; fast but volatile Global cache: shared cache for hot data across
servers TTL: how long cached data remains valid Cache invalidation:
decide when cached data is no longer trustworthy Cache eviction: remove
items when cache is full Write-through: cache first, then DB; strong
consistency, slower writes Write-back: cache first, DB later; fastest
writes, weaker consistency Write-around: write directly to DB; cache
skipped on write Best cache fit: repeated reads, acceptable staleness,
hot data Memory vs I/O vs network: memory fastest, network slowest Main
question for TTL: how much staleness can the business tolerate?
