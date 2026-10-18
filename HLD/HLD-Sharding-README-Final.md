# HLD - Sharding

## Senior Software Engineer Mentor Notes

> Goal: Understand sharding deeply enough to **derive the design**, not
> memorize formulas.

This README consolidates the learning path discussed around:

-   Sharding key selection
-   API/query-driven shard-key decisions
-   Modular/hash-based sharding
-   Range-based sharding
-   Why modulo remaps many keys when shard count changes
-   Combining strategies
-   Consistent hashing
-   Hash space / ring
-   Physical servers vs virtual nodes
-   Data hash vs server hash
-   Efficient lookup with binary search
-   Virtual nodes for better distribution
-   Adding/removing servers
-   Hotspots and nested sharding
-   Fan-out patterns such as social feeds
-   Ordering/sorting after sharding
-   Production trade-offs and failure scenarios

------------------------------------------------------------------------

## Learning Path: Beginner → Advanced

Use this order when learning or revising. The links are intentionally ordered so that each concept answers a question created by the previous one.

| Level | Topic | Context |
|---|---|---|
| 🟢 Beginner | Core sharding problem | [Go to §1](#1-the-core-problem) |
| 🟢 Beginner | Sharding key, hash value, shard | [Go to §2](#2-the-three-things-you-must-not-confuse) |
| 🟢 Beginner | Choosing a sharding key from APIs | [Go to §3](#3-why-user_id-can-be-a-good-sharding-key) |
| 🟢 Beginner | Sharding-key decision checklist | [Go to §4](#4-sharding-key-decision-checklist) |
| 🟢 Beginner | Modular / hash sharding | [Go to §5](#5-modular-sharding) |
| 🟢 Beginner | Why modulo is fast | [Go to §6](#6-why-modulo-is-fast) |
| 🟡 Intermediate | Modulo remapping problem | [Go to §7](#7-the-major-problem-with-modulo) |
| 🟡 Intermediate | Range-based sharding | [Go to §9](#9-range-based-sharding) |
| 🟡 Intermediate | Range splitting and workload | [Go to §11](#11-range-shardings-major-problem) |
| 🟡 Intermediate | Modular vs range-based | [Go to §14](#14-modular-vs-range-based) |
| 🟡 Intermediate | Why consistent hashing exists | [Go to §15](#15-why-consistent-hashing-exists) |
| 🟡 Intermediate | Hash space | [Go to §16](#16-hash-space) |
| 🟡 Intermediate | Server + data placement on the ring | [Go to §17](#17-how-does-a-machine-get-a-position-on-the-ring) |
| 🟡 Intermediate | Complete consistent-hashing dry run | [Go to §21](#21-complete-consistent-hashing-dry-run) |
| 🟠 Advanced | Virtual nodes | [Go to §25](#25-virtual-nodes) |
| 🟠 Advanced | Virtual-node creation and token mapping | [Go to §26](#26-virtual-node-example) |
| 🟠 Advanced | Binary-search lookup | [Go to §29](#29-consistent-hashing-lookup-optimization) |
| 🟠 Advanced | Lookup complexity | [Go to §31](#31-important-complexity-correction) |
| 🟠 Advanced | Production-level virtual-node design | [Go to §34](#34-production-level-virtual-node-dry-run) |
| 🔴 Senior | Hotspots / nested sharding | [Go to §37](#37-hotspot-problem) |
| 🔴 Senior | Fan-out and ordering | [Go to §39](#39-fan-out-different-problem) |
| 🔴 Senior | Hybrid / bucket-based designs | [Go to §43](#43-combining-modular-and-range-ideas) |
| 🔴 Senior | Production monitoring and routing metadata | [Go to §50](#50-production-monitoring) |
| 🔴 Interview | Full API → DB routing dry run | [Go to §53](#53-consistent-hashing-full-dry-run-from-api-to-db) |
| 🔴 Interview | Decision framework | [Go to §60](#60-senior-engineer-decision-framework) |
| 🔴 Interview | Complexity cheat sheet | [Go to §63](#63-final-complexity-cheat-sheet) |
| 🔴 Interview | Answer template | [Go to §64](#64-interview-answer-template) |
| 🔴 Mastery | Derivation questions | [Go to §65](#65-questions-you-should-be-able-to-derive) |
| 🔴 Mastery | Final mental model | [Go to §66](#66-final-senior-level-mental-model) |

### How to use the links

Do **not** memorize §15–§66 first. Start at §1 and move downward.

The recurring mental chain is:

```text
API / Query pattern
      ↓
Choose Sharding Key
      ↓
Choose Routing Strategy
      ↓
Hash / Range / Bucket
      ↓
Logical position / partition
      ↓
Physical machine
      ↓
Query
      ↓
Scale / rebalance / handle hotspots
```

> 🎯 **Interview principle:** If you can derive the next step in this chain, you understand sharding. If you can only repeat definitions, you are memorizing it.

------------------------------------------------------------------------

# 1. The Core Problem
> ↳ **Context:** [where this fits in the learning path](#1-the-core-problem)

A single database machine eventually becomes a bottleneck.

Suppose we have:

``` text
Application
    |
    v
Single DB
    |
    +-- 1 TB data
    +-- 100K writes/sec
    +-- 500K reads/sec
```

Eventually:

-   storage becomes large
-   CPU becomes high
-   memory becomes constrained
-   disk I/O becomes a bottleneck
-   connection count increases
-   one machine becomes a single scaling boundary

Sharding means:

> **Split the logical dataset across multiple independent database
> machines/shards.**

``` text
                 Application
                      |
                 Shard Router
          ____________|____________
         |            |            |
         v            v            v
       Shard 0      Shard 1      Shard 2
       Machine A    Machine B    Machine C
```

The most important question is not:

> "How do I split the database?"

The more important question is:

> **"Given this request, how can I determine exactly which shard
> contains the required data?"**

That is the purpose of the **sharding key + routing function**.

------------------------------------------------------------------------

# 2. The Three Things You Must Not Confuse
> ↳ **Context:** [where this fits in the learning path](#2-the-three-things-you-must-not-confuse)
> 🚨 **INTERVIEW CATCH — 3 different things**
>
> Never say “the hash is the server.” Keep this exact chain:
>
> ```text
> Sharding key → hash/key transformation → ring/partition position → owner shard → physical machine
> ```
>
> The **hash value is a routing coordinate**, not a machine.


A beginner often mixes these three:

``` text
Sharding Key
      |
      v
Hash / Routing Function
      |
      v
Shard / Machine
```

Example:

``` text
user_id = 42
       |
       v
hash(user_id)
       |
       v
routing decision
       |
       v
Machine M2
```

### Sharding key

The field used to decide where a row belongs.

Examples:

``` text
user_id
tenant_id
customer_id
order_id
region
```

### Hash value

A numeric value generated from the sharding key.

``` text
hash(user_id=42) = 781234
```

The hash value is **not the server**.

### Shard / physical machine

The actual storage location.

``` text
Shard 2 -> DB Machine M2
```

------------------------------------------------------------------------

# 3. Why `user_id` Can Be a Good Sharding Key
> ↳ **Context:** [where this fits in the learning path](#3-why-userid-can-be-a-good-sharding-key)
> ⚠️ **BEGINNER MISTAKE:** Choosing a sharding key because it “looks unique.”
>
> A good sharding key is chosen from the **access pattern**:
> - Can the API usually provide it?
> - Can it route to one shard?
> - Does it distribute storage and write traffic?
> - Does the choice create hotspots?
>
> 🚨 **INTERVIEW CATCH:** “Unique” and “good shard key” are not synonyms.


Consider:

``` text
bookmarks
------------------------------------------------
title | url | user_id | timestamp
```

Typical APIs might be:

``` text
GET /users/{userId}/bookmarks
POST /users/{userId}/bookmarks
DELETE /users/{userId}/bookmarks/{bookmarkId}
```

If most operations contain `user_id`, then `user_id` is attractive
because:

1.  It is usually present in the request.
2.  A user's bookmarks can stay together.
3.  `GET bookmarks by user_id` can target one shard.
4.  Writes can target one shard.
5.  The router can determine the shard before querying the database.

Mental model:

``` text
API request
    |
    | user_id = 42
    v
Routing function
    |
    v
Shard M2
    |
    v
Query only M2
```

### Important correction

The sharding key is **not chosen only from the table**.

It is chosen from:

``` text
Data distribution
      +
Access patterns / APIs
      +
Write distribution
      +
Growth
      +
Operational behavior
```

A column can have excellent uniqueness but still be a poor shard key if
important APIs do not provide it.

------------------------------------------------------------------------

# 4. Sharding-Key Decision Checklist
> ↳ **Context:** [where this fits in the learning path](#4-sharding-key-decision-checklist)

Before selecting a sharding key, ask:

## ① Can the request identify the shard?

Example:

``` text
GET /users/42/bookmarks
```

Yes:

``` text
user_id = 42
```

Good.

But:

``` text
GET /bookmarks?title=ABC
```

does not provide `user_id`.

That may require:

-   another index
-   a secondary lookup
-   a fan-out query
-   a denormalized lookup table
-   a different API design

------------------------------------------------------------------------

## ② Is the data evenly distributed?

Ask:

> Could one shard contain 80% of the rows?

If yes, the key may create a hotspot.

------------------------------------------------------------------------

## ③ Is write traffic evenly distributed?

Ask:

> Could most new writes go to one shard?

Sequential IDs are a classic thing to investigate.

------------------------------------------------------------------------

## ④ What happens when a machine is added?

Ask:

> How much existing data must move?

------------------------------------------------------------------------

## ⑤ What happens when a machine is removed?

Ask:

> How much data must move and where does it go?

------------------------------------------------------------------------

## ⑥ What happens as the application grows?

Ask:

> Will today's distribution still work after 10x growth?

This is the senior-level question.

------------------------------------------------------------------------

# 5. Modular Sharding
> ↳ **Context:** [where this fits in the learning path](#5-modular-sharding)
> 🚨 **INTERVIEW CATCH:** `hash(SK) % N` is a **routing formula**. It is not the same thing as consistent hashing.
>
> ```text
> hash(SK) % number_of_shards
> ```
>
> is extremely simple and fast, but changing `N` can change the destination for many keys.


The simplest hash/modulo strategy is:

``` text
shard = hash(shardingKey) % numberOfShards
```

For simplicity, suppose:

``` text
hash(user_id) = user_id
```

and:

``` text
3 shards

M0
M1
M2
```

Then:

``` text
user 10 -> 10 % 3 = 1 -> M1
user 11 -> 11 % 3 = 2 -> M2
user 12 -> 12 % 3 = 0 -> M0
user 13 -> 13 % 3 = 1 -> M1
```

Distribution:

``` text
M0 <- 12
M1 <- 10,13
M2 <- 11
```

With a good hash function and many keys, modulo can distribute keys
reasonably well.

------------------------------------------------------------------------

# 6. Why Modulo Is Fast
> ↳ **Context:** [where this fits in the learning path](#6-why-modulo-is-fast)

Routing is essentially:

``` text
hash(key)
   |
   v
hash % N
   |
   v
shard number
```

Time:

``` text
O(1)
```

There is no search across shards.

This is why modulo hashing is attractive when:

-   shard count is stable
-   simple routing is important
-   data movement during topology changes is acceptable

------------------------------------------------------------------------

# 7. The Major Problem With Modulo
> ↳ **Context:** [where this fits in the learning path](#7-the-major-problem-with-modulo)
> ⚠️ **BEGINNER MISTAKE:** Saying “only the new shard gets new data.”
>
> With ordinary modulo sharding, changing the shard count changes the modulo result for many existing keys. That can require large-scale movement.
>
> 🚨 **INTERVIEW CATCH:** Always dry-run **N = 3 → N = 4** with a few keys. It immediately demonstrates the remapping problem.


Suppose:

``` text
N = 3
```

Mappings:

``` text
key 10 -> 10 % 3 = 1 -> M1
key 11 -> 11 % 3 = 2 -> M2
key 12 -> 12 % 3 = 0 -> M0
key 13 -> 13 % 3 = 1 -> M1
key 14 -> 14 % 3 = 2 -> M2
key 15 -> 15 % 3 = 0 -> M0
```

Now add one machine:

``` text
N = 4
```

Recalculate:

``` text
10 % 4 = 2 -> M2
11 % 4 = 3 -> M3
12 % 4 = 0 -> M0
13 % 4 = 1 -> M1
14 % 4 = 2 -> M2
15 % 4 = 3 -> M3
```

Compare:

``` text
Key     Before       After
10      M1           M2   <-- moved
11      M2           M3   <-- moved
12      M0           M0
13      M1           M1
14      M2           M2
15      M0           M3   <-- moved
```

A large fraction of keys can change ownership.

This is the core weakness:

> **The shard count is part of the routing formula. Changing the shard
> count changes the formula for many keys.**

------------------------------------------------------------------------

# 8. Why "Many Keys Get Remapped" Matters
> ↳ **Context:** [where this fits in the learning path](#8-why-many-keys-get-remapped-matters)

Remapping is not just a mathematical problem.

It can cause:

``` text
Many keys change shard
        |
        +--> data migration
        +--> network traffic
        +--> disk I/O
        +--> cache misses
        +--> temporary load spikes
        +--> operational complexity
```

Example:

``` text
1 TB database
4 shards -> 5 shards
```

Even if only a portion logically needs to move, a modulo-based design
may cause a large remapping set.

------------------------------------------------------------------------

# 9. Range-Based Sharding
> ↳ **Context:** [where this fits in the learning path](#9-range-based-sharding)
> 🚨 **INTERVIEW CATCH:** Range sharding gives you a natural answer to **range queries**, but it does not automatically give you uniform load.
>
> A range is a **logical ownership boundary**. The physical machine can change without changing the business meaning of the range.


Instead of:

``` text
hash(key) % N
```

define explicit ranges.

Example:

``` text
0 - 999       -> M0
1000 - 1999   -> M1
2000 - 2999   -> M2
3000 - 3999   -> M3
```

Request:

``` text
user_id = 2750
```

Router asks:

``` text
Is 2750 in 2000-2999?
```

Yes:

``` text
M2
```

Only M2 is queried.

This is why range routing can be extremely fast when the routing
metadata is known.

------------------------------------------------------------------------

# 10. Range-Based Sharding Dry Run
> ↳ **Context:** [where this fits in the learning path](#10-range-based-sharding-dry-run)

Assume:

``` text
M0 -> 0-999
M1 -> 1000-1999
M2 -> 2000-2999
M3 -> 3000-3999
```

Request:

``` text
GET /users/2750/bookmarks
```

### Step 1

Extract shard key:

``` text
user_id = 2750
```

### Step 2

Find the range:

``` text
2000 <= 2750 <= 2999
```

### Step 3

Routing:

``` text
2750 -> M2
```

### Step 4

Query only M2:

``` sql
SELECT *
FROM bookmarks
WHERE user_id = 2750;
```

No need to query:

``` text
M0
M1
M3
```

------------------------------------------------------------------------

# 11. Range Sharding's Major Problem
> ↳ **Context:** [where this fits in the learning path](#11-range-shardings-major-problem)

Suppose IDs are sequential:

``` text
1000
1001
1002
...
3999
4000
4001
...
```

New users continuously receive higher IDs.

If:

``` text
3000-3999 -> M3
4000-4999 -> M4
```

new writes may concentrate on the newest range.

This creates a **write hotspot**.

Another issue is historical skew.

Suppose:

``` text
M0 -> users 0-999
```

Old users generate much more data:

``` text
M0 = 800 GB
M1 = 200 GB
M2 = 150 GB
M3 = 100 GB
```

The numeric range is equal, but the workload is not equal.

This is a critical production lesson:

> **Equal key range does not mean equal workload.**

------------------------------------------------------------------------

# 12. Splitting a Range
> ↳ **Context:** [where this fits in the learning path](#12-splitting-a-range)

Suppose:

``` text
M2 -> 2000-2999
```

but M2 becomes overloaded.

You can split the range:

``` text
2000-2499 -> M2
2500-2999 -> M4
```

Only the affected range needs migration.

This is one reason range systems can support controlled local
rebalancing.

But the split should be based on:

-   data size
-   request rate
-   write rate
-   storage
-   CPU
-   latency

not merely the number of numeric IDs.

------------------------------------------------------------------------

# 13. Range Split Is Not Always a Numeric Split
> ↳ **Context:** [where this fits in the learning path](#13-range-split-is-not-always-a-numeric-split)

Beginner thought:

> "Split 0-999 into 0-499 and 500-999."

Production thinking:

> "Where is the actual workload boundary?"

For example:

``` text
0-999

0-100       10 GB
101-200     12 GB
201-300     11 GB
301-400     10 GB
401-500     12 GB
501-600     250 GB  <-- hotspot
601-700     11 GB
701-800     10 GB
801-900     12 GB
901-999     10 GB
```

A naive half split does not solve the real problem.

You may need a more targeted split or another sharding strategy.

------------------------------------------------------------------------

# 14. Modular vs Range-Based
> ↳ **Context:** [where this fits in the learning path](#14-modular-vs-range-based)

  -----------------------------------------------------------------------
  Property                Modular                 Range
  ----------------------- ----------------------- -----------------------
  Routing                 Very simple             Simple with range
                                                  metadata

  Typical lookup          O(1)                    O(log R) with ordered
                                                  ranges

  Ordering/range queries  Poor                    Strong

  Sequential IDs          Usually distributed     Can create hotspots
                          after hashing           

  Adding shard            Many keys may remap     Can split/move selected
                                                  ranges

  Removing shard          Many keys may remap     Move selected ranges

  Local rebalancing       Harder                  Natural

  Range scans             Poor                    Good

  Hotspot control         Hashing can help        Requires
                                                  monitoring/splitting
  -----------------------------------------------------------------------

Neither is universally correct.

------------------------------------------------------------------------

# 15. Why Consistent Hashing Exists
> ↳ **Context:** [where this fits in the learning path](#15-why-consistent-hashing-exists)
> 🚨 **INTERVIEW CATCH:** Consistent hashing does **not** mean “no data movement.”
>
> The important property is that adding/removing a node changes ownership for a **limited set of neighboring ring intervals**, rather than forcing a full modulo-style remap.


We want:

1.  Fast routing
2.  Good distribution
3.  Adding a server should not remap everything
4.  Removing a server should not remap everything
5.  Ability to rebalance

This leads to:

# Consistent Hashing

The central idea:

> **Put both servers and data into the same hash space.**

------------------------------------------------------------------------

# 16. Hash Space
> ↳ **Context:** [where this fits in the learning path](#16-hash-space)
> ⚠️ **BEGINNER MISTAKE:** Thinking the ring is created from the number of servers.
>
> The ring comes from the **hash function's output space**.
>
> If the hash output is `b` bits:
>
> ```text
> Hash space = [0, 2^b - 1]
> ```
>
> For learning, a 32-bit space is convenient:
>
> ```text
> 0 ... 2^32 - 1
> ```
>
> The end connects back to the beginning, which makes it a ring.


Imagine a hash function produces values:

``` text
0 ... 2^32-1
```

For teaching, use:

``` text
0 ... 20
```

Now make it circular:

``` text
                 0
          20            1

       19                  2

     18                      3

     17                      4

     16                      5

     15                      6

       14                  7

          13            8
              12 11 10 9
```

This is the **hash ring**.

Important:

> The ring is only a representation of the hash space.

It is not a physical database.

------------------------------------------------------------------------

### Hash-space rule

The ring boundary comes from the hash function output width.

If the hash produces `b` bits:

```text
Hash space = [0, 2^b - 1]
```

Examples from the supplied notes:

```text
32-bit hash  → [0, 2^32 - 1]
128-bit hash → [0, 2^128 - 1]
256-bit hash → [0, 2^256 - 1]
```

For our dry runs, we intentionally use a tiny space such as:

```text
0 ... 20
```

so that the movement can be seen by a human.

> 🚨 **INTERVIEW CATCH:** The small `0...20` ring is only a teaching model. Real systems can use a much larger hash space.

### Same space, different roles

```text
SERVER / VN
M1#0
  ↓
hash()
  ↓
ring coordinate

DATA
user_id=101
  ↓
hash()
  ↓
ring coordinate
```

Both coordinates live in the **same hash space**.

But:

```text
Server/VN hash → creates ownership boundaries
Data/SK hash   → finds a point whose owner must be located
```

# 17. How Does a Machine Get a Position on the Ring?
> ↳ **Context:** [where this fits in the learning path](#17-how-does-a-machine-get-a-position-on-the-ring)
> 🚨 **INTERVIEW CATCH — server placement**
>
> A physical server does not need to be the ring coordinate itself.
>
> In the virtual-node design:
>
> ```text
> physical server M1
>      ↓
> M1#0, M1#1, M1#2, ...
>      ↓
> hash(each VN identifier)
>      ↓
> multiple token positions on ring
> ```
>
> Each token remembers which physical server owns it.


This was an important question.

Suppose physical servers are:

``` text
S1
S2
S3
```

Compute:

``` text
hash("S1")
hash("S2")
hash("S3")
```

Example:

``` text
hash(S1) = 17
hash(S2) = 3
hash(S3) = 10
```

So:

``` text
Ring position 3  -> S2
Ring position 10 -> S3
Ring position 17 -> S1
```

The machine itself is **not** position 3.

Rather:

``` text
server identity
      |
      v
hash(server identity)
      |
      v
ring position
      |
      v
server mapping
```

------------------------------------------------------------------------

# 18. How Does Data Get a Position?
> ↳ **Context:** [where this fits in the learning path](#18-how-does-data-get-a-position)
> 🚨 **INTERVIEW CATCH — data placement**
>
> The data uses the **same hash-space coordinate system**:
>
> ```text
> sharding key
>      ↓
> hash(SK)
>      ↓
> data position on ring
>      ↓
> find first token clockwise
>      ↓
> token → physical server
> ```
>
> Server tokens and data hashes are both positions in the same hash space, but they have different purposes.


Suppose:

``` text
user_id = 42
```

Compute:

``` text
hash(42) = 16
```

Now:

``` text
data hash = 16
```

Find the first server position clockwise at or after 16.

Server positions:

``` text
[3, 10, 17]
```

First position \>= 16:

``` text
17
```

Therefore:

``` text
user 42 -> position 16
             |
             v
       next server position
             |
             v
            17
             |
             v
            S1
```

So:

``` text
user 42 -> S1
```

------------------------------------------------------------------------

# 19. Critical Distinction: Data Hash vs Server Hash
> ↳ **Context:** [where this fits in the learning path](#19-critical-distinction-data-hash-vs-server-hash)
> ⚠️ **BEGINNER MISTAKE:** Hashing the server and hashing the data “for the same reason.”
>
> They are both mapped into the same space, but:
>
> - **Server/VN hash:** creates ownership boundaries.
> - **Data/SK hash:** creates the lookup point.
>
> This distinction is one of the most common consistent-hashing interview catches.


Yes, there are two hashes conceptually.

### Server hash

``` text
hash(server_id)
```

Used to place a server on the ring.

### Data hash

``` text
hash(sharding_key)
```

Used to place a data key on the ring.

Both produce values in the **same hash space**.

``` text
                  SAME HASH SPACE

server:
S1 --hash--> 17
S2 --hash--> 3
S3 --hash--> 10

data:
user42 --hash--> 16
```

Then the routing rule determines:

``` text
16 -> next server position -> 17 -> S1
```

------------------------------------------------------------------------

# 20. The Most Important Mental Model
> ↳ **Context:** [where this fits in the learning path](#20-the-most-important-mental-model)

Do not think:

``` text
hash(user) % numberOfServers
```

for consistent hashing.

Think:

``` text
                 HASH SPACE / RING

      server positions + data positions
                    |
                    v
          find next server clockwise
                    |
                    v
                 server
```

------------------------------------------------------------------------

# 21. Complete Consistent Hashing Dry Run
> ↳ **Context:** [where this fits in the learning path](#21-complete-consistent-hashing-dry-run)

Use a small ring:

``` text
0 ... 20
```

Physical servers:

``` text
S1
S2
S3
```

Server hashes:

``` text
hash(S1) = 17
hash(S2) = 3
hash(S3) = 10
```

Sorted:

``` text
[3, 10, 17]
```

Mapping:

``` text
3  -> S2
10 -> S3
17 -> S1
```

Now data:

``` text
D1 = user 101
D2 = user 102
D3 = user 103
D4 = user 104
```

Suppose:

``` text
hash(D1) = 2
hash(D2) = 5
hash(D3) = 12
hash(D4) = 19
```

Routing:

### D1

``` text
hash(D1) = 2

next server position >= 2
= 3

3 -> S2
```

Therefore:

``` text
D1 -> S2
```

### D2

``` text
hash(D2) = 5

next position >= 5
= 10

10 -> S3
```

Therefore:

``` text
D2 -> S3
```

### D3

``` text
hash(D3) = 12

next position >= 12
= 17

17 -> S1
```

Therefore:

``` text
D3 -> S1
```

### D4

``` text
hash(D4) = 19

No server position >= 19.

Wrap around to the first position:

3 -> S2
```

Therefore:

``` text
D4 -> S2
```

Final:

``` text
D1 -> S2
D2 -> S3
D3 -> S1
D4 -> S2
```

------------------------------------------------------------------------

# 22. Why the Ring Wraps Around
> ↳ **Context:** [where this fits in the learning path](#22-why-the-ring-wraps-around)

This is a circular space.

If:

``` text
data hash = 19
```

and server positions are:

``` text
3, 10, 17
```

there is no server after 19.

So go around:

``` text
19 -> 20 -> 0 -> 1 -> 2 -> 3
```

Therefore:

``` text
19 -> 3
```

This is the wrap-around rule.

------------------------------------------------------------------------

# 23. Adding a Server
> ↳ **Context:** [where this fits in the learning path](#23-adding-a-server)

Before:

``` text
S1 -> 17
S2 -> 3
S3 -> 10
```

Add:

``` text
S4
```

Suppose:

``` text
hash(S4) = 5
```

New sorted positions:

``` text
[3, 5, 10, 17]
```

Only the interval between:

``` text
3 -> 5
```

is newly owned by S4.

Previously:

``` text
keys in (3,10] -> S3
```

Now:

``` text
keys in (3,5] -> S4
keys in (5,10] -> S3
```

So only keys in the affected interval move.

This is the central advantage:

> **Adding a server changes ownership of a local portion of the ring
> rather than recomputing every key against a new shard count.**

------------------------------------------------------------------------

# 24. Removing a Server
> ↳ **Context:** [where this fits in the learning path](#24-removing-a-server)

Suppose:

``` text
S4 -> 5
```

is removed.

Its interval:

``` text
(3,5]
```

must move to the next server clockwise:

``` text
S3 -> 10
```

Therefore:

``` text
S4 data -> S3
```

The rest of the ring remains unchanged.

------------------------------------------------------------------------

# 25. Virtual Nodes
> ↳ **Context:** [where this fits in the learning path](#25-virtual-nodes)
> 🚨 **INTERVIEW CATCH — why VNs exist**
>
> With one token per physical machine, random token placement can produce a very uneven ring. One machine could accidentally own a very large interval while another owns a small interval.
>
> Virtual nodes solve this by giving each physical machine **many independent token positions**.


A physical server having only one position can still create uneven
ranges.

Example:

``` text
S1 -> 17
S2 -> 3
S3 -> 10
```

The intervals are not equal.

A server might accidentally own a huge portion of the ring.

Solution:

> Put multiple positions for each physical server.

These are called **virtual nodes** or **vnodes**.

------------------------------------------------------------------------

# 26. Virtual Node Example
> ↳ **Context:** [where this fits in the learning path](#26-virtual-node-example)

Suppose:

``` text
S1 -> vnodes at [2, 8, 15]
S2 -> vnodes at [4, 11, 18]
S3 -> vnodes at [6, 13, 20]
```

Ring:

``` text
2  -> S1
4  -> S2
6  -> S3
8  -> S1
11 -> S2
13 -> S3
15 -> S1
18 -> S2
20 -> S3
```

Now the ownership is interleaved.

Instead of:

``` text
one server
    |
    +---- huge interval
```

we get:

``` text
S1 -- small interval -- S2 -- small interval -- S3
 |                       |                       |
 +-----------------------+-----------------------+
```

More virtual nodes generally make the statistical distribution smoother.

------------------------------------------------------------------------

## 26A. Virtual Node Mechanics: How VN Maps Are Created

This section makes the virtual-node idea concrete before the later production dry runs.

### Step 1 — Choose a virtual-node ratio

Let:

```text
K = number of virtual nodes per physical server
```

For learning/typical examples, we may use:

```text
K = 3
K = 100
K = 128
K = 256
```

The exact production value is an engineering decision, not a universal magic number.

### Step 2 — Create unique VN identifiers

For physical server `M1`:

```text
M1#0
M1#1
M1#2
...
M1#(K-1)
```

These identifiers act as independent inputs to the hash function.

### Step 3 — Hash each VN identifier

For a 32-bit ring:

```text
position = hash("M1#i") mod 2^32
```

Example:

```text
M1#0 → hash → 31
M1#1 → hash → 184
M1#2 → hash → 391
```

The exact numbers are illustrative.

### Step 4 — Store the ownership mapping

The routing structure needs both:

```text
Token position → physical server
```

Example:

```text
31  → M1
184 → M1
391 → M1
```

For another server:

```text
M2#0 → 77
M2#1 → 240
M2#2 → 512
```

Now the ring contains many positions, while each position points back to its physical owner.

> 🚨 **INTERVIEW CATCH:** A token is a routing boundary. It is not itself a database machine.

### Step 5 — Keep token positions ordered

A sorted token structure can be represented conceptually as:

```text
[31, 77, 184, 240, 391, 512, ...]
```

with a companion mapping:

```text
31  → M1
77  → M2
184 → M1
240 → M2
391 → M1
512 → M2
```

The implementation may use a balanced search tree or a sorted array/list depending on whether the ring is frequently mutated and how routing metadata is distributed.

### Why this reduces uneven ownership

With only one token per machine:

```text
M1 -------------------------- huge interval
M2 ---- small interval
M3 -------- interval
```

With many VNs:

```text
M1 -- M2 -- M1 -- M3 -- M2 -- M1 -- M3 -- M2 ...
```

Each physical server owns many smaller intervals spread around the ring.

> ⚠️ **Do not confuse:** “many VNs” with “many databases.” VNs are logical routing tokens attached to physical servers.

# 27. Why Virtual Nodes Help
> ↳ **Context:** [where this fits in the learning path](#27-why-virtual-nodes-help)

Without vnodes:

``` text
S1 = one position
S2 = one position
S3 = one position
```

Random placement may produce:

``` text
S1 -> 60% of ring
S2 -> 20%
S3 -> 20%
```

That is undesirable.

With many vnodes:

``` text
S1 -> many small intervals
S2 -> many small intervals
S3 -> many small intervals
```

The law of large numbers helps the total ownership become more balanced.

------------------------------------------------------------------------

# 28. Virtual Nodes Do NOT Mean More Physical Machines
> ↳ **Context:** [where this fits in the learning path](#28-virtual-nodes-do-not-mean-more-physical-machines)

This is another common beginner mistake.

``` text
Physical machines:
S1
S2
S3
```

With 100 virtual nodes each:

``` text
300 ring positions
```

But still only:

``` text
3 physical machines
```

The mapping is:

``` text
virtual position -> physical server
```

Example:

``` text
17 -> S1
23 -> S1
31 -> S1

42 -> S2
55 -> S2

63 -> S3
78 -> S3
```

------------------------------------------------------------------------

# 29. Consistent Hashing Lookup Optimization
> ↳ **Context:** [where this fits in the learning path](#29-consistent-hashing-lookup-optimization)
> 🚨 **INTERVIEW CATCH — lookup is not a ring scan**
>
> Do **not** say:
>
> > “We walk around the ring until we find the server.”
>
> That is the conceptual model, not the production lookup implementation.
>
> Production routing can keep token positions sorted and use **binary search** to find the first token `>= hash(SK)`.


A naive implementation might scan clockwise:

``` text
key hash = 16

3
10
17  <-- found
```

With millions of virtual nodes, scanning is too slow.

Instead, maintain sorted ring positions:

``` text
[3, 9, 11, 17, 22, ...]
```

Then perform **binary search**.

Example:

``` text
key hash = 16
```

Find:

``` text
smallest position >= 16
```

Result:

``` text
17
```

Then:

``` text
position 17 -> mapped physical server
```

------------------------------------------------------------------------

# 30. Efficient Lookup: Complete Internal Flow
> ↳ **Context:** [where this fits in the learning path](#30-efficient-lookup-complete-internal-flow)

Production-style routing:

``` text
Request
   |
   v
Extract sharding key
   |
   v
hash(shardingKey)
   |
   v
Hy = hash value
   |
   v
Binary search sorted ring-position array
   |
   v
first position >= Hy
   |
   v
lookup mapping for that ring position
   |
   v
physical server
   |
   v
send query
```

Example:

``` text
sortedPositions = [3, 9, 11, 17, 22]

Hy = 16
```

Binary search:

``` text
16 > 11
16 < 17
```

Result:

``` text
17
```

Mapping:

``` text
17 -> S3
```

Therefore:

``` text
request -> S3
```

------------------------------------------------------------------------

# 31. Important Complexity Correction
> ↳ **Context:** [where this fits in the learning path](#31-important-complexity-correction)
> 🚨 **IMPORTANT COMPLEXITY CATCH**
>
> Do not mix up **ring construction** with **request lookup**.
>
> ```text
> Build/sort ring: O(T log T)
> Per-request lookup: O(log T)
> Token → server mapping: O(1)
> ```
>
> where:
>
> ```text
> T = total virtual-node tokens
>   = physical_servers × VNs_per_server
> ```
>
> Therefore, saying “consistent-hashing lookup is O(N log N)” is usually incorrect.


A common misunderstanding is:

> "Because binary search is used, every request is O(N log N)."

That is **not correct**.

Let:

``` text
N = number of physical servers
V = total number of virtual nodes
```

Usually:

``` text
V = N × virtualNodesPerServer
```

### Building the ring

You generate and sort all virtual-node positions:

``` text
O(V log V)
```

This happens when building/rebuilding the ring or topology metadata.

### Lookup

For each request:

``` text
hash key
    -> O(1) approximately

binary search V positions
    -> O(log V)

mapping position -> physical server
    -> O(1)
```

Therefore:

``` text
Per-request routing:
O(log V)
```

not:

``` text
O(N log N)
```

### If virtual nodes per server is a fixed constant

If:

``` text
V = kN
```

where `k` is fixed, then:

``` text
O(log V)
≈ O(log N)
```

So it is common to describe lookup as:

``` text
O(log N)
```

when the number of vnodes per server is treated as constant.

------------------------------------------------------------------------

# 32. Where O(N log N) Actually Appears
> ↳ **Context:** [where this fits in the learning path](#32-where-on-log-n-actually-appears)

Suppose:

``` text
N = physical servers
K = virtual nodes per server
V = N × K
```

Building the sorted ring:

``` text
Generate V positions
       |
       v
Sort V positions
       |
       v
O(V log V)
```

If K is constant:

``` text
O(N log N)
```

approximately.

So:

``` text
Ring construction/rebuild:
O(V log V)

Request lookup:
O(log V)
```

This distinction is extremely important in interviews.

------------------------------------------------------------------------

# 33. Data Structure for the Ring
> ↳ **Context:** [where this fits in the learning path](#33-data-structure-for-the-ring)

Conceptually:

``` text
sortedPositions = [3, 9, 11, 17, 22]
```

and mapping:

``` text
3  -> S1
9  -> S4
11 -> S2
17 -> S3
22 -> S5
```

Implementation can keep the server mapping alongside the position:

``` text
[
  (3,  S1),
  (9,  S4),
  (11, S2),
  (17, S3),
  (22, S5)
]
```

Then binary search finds:

``` text
(17, S3)
```

No second search is required.

The important idea is:

> **The ring position is not the physical server. It is a routing point
> that maps to a physical server.**

------------------------------------------------------------------------

# 34. Production-Level Virtual Node Dry Run
> ↳ **Context:** [where this fits in the learning path](#34-production-level-virtual-node-dry-run)
> 🚨 **SENIOR INTERVIEW CATCH — VNs are logical, not physical**
>
> If:
>
> ```text
> M1 → 100 VNs
> M2 → 100 VNs
> M3 → 100 VNs
> ```
>
> you still have **3 physical machines**, not 300 machines.
>
> The 300 tokens are routing points used to divide ownership into many smaller intervals.


Assume:

``` text
Hash space = 0..100
Physical servers = 3
Virtual nodes per server = 3
```

Generated positions:

``` text
S1 -> [5, 40, 75]
S2 -> [15, 50, 90]
S3 -> [25, 60, 95]
```

Sorted:

``` text
5  -> S1
15 -> S2
25 -> S3
40 -> S1
50 -> S2
60 -> S3
75 -> S1
90 -> S2
95 -> S3
```

Now:

``` text
user_id = 10025
hash(user_id) = 52
```

Binary search:

``` text
5
15
25
40
50
60  <-- first >= 52
```

Therefore:

``` text
52 -> 60 -> S3
```

The data is stored on S3.

------------------------------------------------------------------------

# 35. What Happens When S4 Is Added?
> ↳ **Context:** [where this fits in the learning path](#35-what-happens-when-s4-is-added)

Suppose S4 gets virtual nodes:

``` text
S4 -> [12, 45, 82]
```

New ring:

``` text
5  -> S1
12 -> S4
15 -> S2
25 -> S3
40 -> S1
45 -> S4
50 -> S2
60 -> S3
75 -> S1
82 -> S4
90 -> S2
95 -> S3
```

Only intervals immediately preceding S4's new positions change
ownership.

The entire dataset is not recomputed from scratch.

That is the production advantage.

------------------------------------------------------------------------

# 36. Consistent Hashing Does Not Mean "Zero Data Movement"
> ↳ **Context:** [where this fits in the learning path](#36-consistent-hashing-does-not-mean-zero-data-movement)
> ⚠️ **BEGINNER MISTAKE:** “Consistent hashing means adding a server moves no data.”
>
> Correct mental model:
>
> ```text
> Add server
>    ↓
> new token(s) appear
>    ↓
> only affected intervals change owner
>    ↓
> affected data moves
> ```
>
> The goal is **limited and localized movement**, not zero movement.


Very important.

Adding/removing a machine still requires migration of affected data.

Consistent hashing means:

> **Minimize the amount of data that must move when topology changes.**

It does NOT mean:

``` text
add machine -> zero movement
```

Correct mental model:

``` text
topology change
      |
      v
some ring intervals change owner
      |
      v
only affected data migrates
```

------------------------------------------------------------------------

# 37. Hotspot Problem
> ↳ **Context:** [where this fits in the learning path](#37-hotspot-problem)
> 🚨 **SENIOR INTERVIEW CATCH:** Uniform key distribution does not guarantee uniform **traffic**.
>
> A perfectly distributed hash ring can still have a hot key:
>
> ```text
> user_id = celebrity_user
>          ↓
> huge read/write traffic
>          ↓
> one logical owner becomes hot
> ```
>
> This is a workload problem, not simply a ring-position problem.


Even with hashing, access patterns can be skewed.

Example:

``` text
Celebrity user
user_id = 42
```

Suppose:

``` text
10 million requests/minute
```

Even if the data is perfectly distributed:

``` text
user 42 -> one shard
```

That shard may become hot.

This is called a **hot key / hotspot**.

Hashing solves:

``` text
key distribution
```

but does not automatically solve:

``` text
extreme traffic for one key
```

------------------------------------------------------------------------

# 38. Nested Sharding for Hotspots
> ↳ **Context:** [where this fits in the learning path](#38-nested-sharding-for-hotspots)

A common conceptual solution is to introduce another level of
distribution.

Example:

``` text
user_id = 42
```

Instead of:

``` text
user 42 -> one shard
```

use:

``` text
user 42
   |
   v
secondary bucket / partition
   |
   +--> bucket 0 -> shard A
   +--> bucket 1 -> shard B
   +--> bucket 2 -> shard C
```

For example:

``` text
nestedKey = hash(user_id + bucket)
```

The important idea is:

> First identify the logical owner, then split an exceptionally hot
> logical key into smaller physical buckets.

Trade-off:

``` text
less hotspot
    +
more routing complexity
    +
more reads/writes may be required
```

------------------------------------------------------------------------

# 39. Fan-Out: Different Problem
> ↳ **Context:** [where this fits in the learning path](#39-fan-out-different-problem)
> ⚠️ **IMPORTANT:** Fan-out is not a replacement definition for sharding.
>
> Sharding answers:
>
> > “Where is the data?”
>
> Fan-out answers:
>
> > “How do I efficiently gather data spread across multiple partitions?”


Fan-out is often confused with hotspot sharding.

Suppose Instagram-like feed data is distributed by user.

``` text
User A -> Shard 1
User B -> Shard 2
User C -> Shard 3
```

A feed request may need:

``` text
A + B + C
```

So the application may query multiple shards:

``` text
              Feed API
             /    |    \
            v     v     v
         Shard1 Shard2 Shard3
            \     |     /
             \    |    /
              Merge
                |
                v
             Sort
                |
                v
             Response
```

This is **fan-out**.

The goal is not necessarily to split one hot key.

The goal is to collect data distributed across multiple shards.

------------------------------------------------------------------------

# 40. Ordering After Sharding
> ↳ **Context:** [where this fits in the learning path](#40-ordering-after-sharding)
> 🚨 **INTERVIEW CATCH:** Sharding does not automatically preserve global ordering.
>
> If an API needs:
>
> ```text
> latest users across all shards
> ```
>
> you may need per-shard sorting plus a merge/top-K step.
>
> The sharding key should not be changed merely because an API needs a different presentation order.


Sharding and ordering are different problems.

Suppose users are sharded by:

``` text
hash(user_id)
```

The database distribution may be excellent.

But now you ask:

``` text
Give me users ordered by created_at DESC
```

The data may exist on:

``` text
M0
M1
M2
M3
```

Each shard can return its local top results:

``` text
M0 -> [100, 90, 80]
M1 -> [98, 95, 70]
M2 -> [101, 88, 75]
```

The application can merge them:

``` text
101
100
98
95
90
88
80
75
70
```

This is a distributed merge problem.

------------------------------------------------------------------------

# 41. When Ordering Matters
> ↳ **Context:** [where this fits in the learning path](#41-when-ordering-matters)

Ask:

> Does the API require global ordering?

If yes, you may need:

-   scatter-gather/fan-out
-   per-shard sorting
-   merge logic
-   global index
-   denormalized read model
-   time-based/range sharding if the access pattern supports it

Do not choose a poor shard key only because you want global ordering.

------------------------------------------------------------------------

# 42. Mental Model: Sharding vs Sorting
> ↳ **Context:** [where this fits in the learning path](#42-mental-model-sharding-vs-sorting)

Think:

``` text
SHARDING
"Where is the data?"

        ↓

SORTING
"In what order should I return it?"
```

These are independent concerns.

------------------------------------------------------------------------

# 43. Combining Modular and Range Ideas
> ↳ **Context:** [where this fits in the learning path](#43-combining-modular-and-range-ideas)
> 🚨 **SENIOR DESIGN CATCH:** A system can have **logical buckets/partitions** and then distribute those buckets across machines.
>
> This is different from blindly applying:
>
> ```text
> hash(SK) % machines
> ```
>
> to every request.
>
> The important design question is: **what should remain stable when machines are added or removed?**


A useful design thought is:

``` text
logical partitioning
       +
stable buckets
       +
mapping buckets to machines
```

Instead of directly mapping:

``` text
key -> machine
```

you can map:

``` text
key -> bucket
bucket -> machine
```

Example:

``` text
hash(user_id) -> bucket 731
bucket 731 -> M2
```

Now changing machine ownership can move buckets instead of changing the
hash formula for every key.

This is a useful production mental model.

------------------------------------------------------------------------

# 44. Why Bucket-Based Designs Are Powerful
> ↳ **Context:** [where this fits in the learning path](#44-why-bucket-based-designs-are-powerful)

Suppose:

``` text
10,000 logical buckets
5 machines
```

Distribution:

``` text
M0 -> 0..1999 buckets
M1 -> 2000..3999
...
```

Add a machine:

``` text
10,000 buckets
6 machines
```

You can reassign selected buckets.

The keys themselves do not need to change hash functions.

This separates:

``` text
KEY -> BUCKET
```

from:

``` text
BUCKET -> MACHINE
```

That separation can make rebalancing easier.

------------------------------------------------------------------------

# 45. A Critical Design Principle
> ↳ **Context:** [where this fits in the learning path](#45-a-critical-design-principle)

Instead of thinking:

> "Which machine owns this key forever?"

think:

> **"Which stable logical partition owns this key, and which machine
> currently hosts that partition?"**

That abstraction appears in many scalable systems.

------------------------------------------------------------------------

# 46. Complete Request Routing Mental Model
> ↳ **Context:** [where this fits in the learning path](#46-complete-request-routing-mental-model)

A production sharded request can look like:

``` text
HTTP Request
     |
     v
Extract shard key
     |
     v
Normalize key
     |
     v
Hash / partition function
     |
     v
Logical bucket / ring position
     |
     v
Routing metadata
     |
     v
Physical shard
     |
     v
Database query
```

For consistent hashing:

``` text
HTTP request
     |
     v
user_id = 42
     |
     v
hash(user_id)
     |
     v
Hy
     |
     v
binary search ring positions
     |
     v
next position
     |
     v
virtual node
     |
     v
physical server
     |
     v
DB
```

------------------------------------------------------------------------

# 47. Common Beginner Mistakes
> ↳ **Context:** [where this fits in the learning path](#47-common-beginner-mistakes)
> ### Interview Catch Summary
>
> These are the mistakes to actively avoid:
>
> 1. **Hash ≠ server.**
> 2. **Sharding key ≠ primary key automatically.**
> 3. **Unique key ≠ good sharding key automatically.**
> 4. **Modulo is fast, but shard-count changes can remap many keys.**
> 5. **Range sharding is not automatically balanced.**
> 6. **Consistent hashing does not mean zero data movement.**
> 7. **Virtual nodes are not physical machines.**
> 8. **Ring position and server identity are different values.**
> 9. **Conceptual clockwise search ≠ production linear scan.**
> 10. **Lookup is O(log T), not O(T log T).**
> 11. **Uniform data distribution ≠ uniform traffic.**
> 12. **Sorting/order requirements are separate from shard placement.**


## Mistake 1

> "The hash value is the server."

Wrong.

``` text
hash value = location in hash space
server = physical owner of that location
```

------------------------------------------------------------------------

## Mistake 2

> "Consistent hashing means no data moves."

Wrong.

Affected ranges still move.

------------------------------------------------------------------------

## Mistake 3

> "Virtual node means virtual machine."

Wrong.

A vnode is a logical ring position.

------------------------------------------------------------------------

## Mistake 4

> "Binary search makes request routing O(N log N)."

Wrong.

Per request:

``` text
O(log V)
```

Ring construction/sorting:

``` text
O(V log V)
```

------------------------------------------------------------------------

## Mistake 5

> "Equal numeric ranges mean equal load."

Wrong.

Workload can be skewed.

------------------------------------------------------------------------

## Mistake 6

> "A unique key is automatically a good shard key."

Wrong.

The access pattern matters.

------------------------------------------------------------------------

## Mistake 7

> "If data is evenly distributed, traffic is also evenly distributed."

Wrong.

A single hot key can dominate traffic.

------------------------------------------------------------------------

## Mistake 8

> "Sharding automatically preserves global ordering."

Wrong.

Global ordering may require fan-out + merge or another design.

------------------------------------------------------------------------

# 48. Production Trade-Off Table
> ↳ **Context:** [where this fits in the learning path](#48-production-trade-off-table)

  ------------------------------------------------------------------------------------
  Approach     Routing    Distribution   Add Server Remove     Range      Main Risk
                                                    Server     Query      
  ------------ ---------- -------------- ---------- ---------- ---------- ------------
  Modulo       O(1)       Good with good Many       Many       Poor       Topology
                          hash           remaps     remaps                changes

  Range        O(log R)   Depends on     Local      Local      Strong     Hot ranges
               or         ranges         range      range                 
               metadata                  movement   movement              
               lookup                                                     

  Consistent   O(log V)   Good with      Local      Local      Weak       Hot keys
  Hashing      typical    vnodes         movement   movement              
               binary                                                     
               search                                                     

  Bucket       O(1) /     Good           Reassign   Reassign   Depends    Metadata
  mapping      O(log B)                  buckets    buckets               management
  ------------------------------------------------------------------------------------

------------------------------------------------------------------------

# 49. Choosing the Strategy
> ↳ **Context:** [where this fits in the learning path](#49-choosing-the-strategy)

Ask these questions.

### Need simple routing and stable shard count?

Consider:

``` text
Modulo hashing
```

### Need range queries and controlled range splitting?

Consider:

``` text
Range sharding
```

### Need easier elasticity when servers are added/removed?

Consider:

``` text
Consistent hashing
```

### Need strong control over logical partitions?

Consider:

``` text
Bucket -> machine mapping
```

### Have hot keys?

Consider:

``` text
hashing
+
hot-key detection
+
nested sharding / bucketing / replication
```

The correct answer depends on the workload.

------------------------------------------------------------------------

# 50. Production Monitoring
> ↳ **Context:** [where this fits in the learning path](#50-production-monitoring)

A senior engineer does not stop at the routing algorithm.

Monitor:

### Data

``` text
data size per shard
disk usage
row count
```

### Traffic

``` text
requests/sec per shard
writes/sec per shard
reads/sec per shard
```

### Performance

``` text
p50 latency
p95 latency
p99 latency
```

### Hotspots

``` text
top keys
top tenants
top users
```

### Rebalancing

``` text
bytes migrated
migration rate
migration failures
remaining migration work
```

### Capacity

``` text
CPU
memory
connections
disk IOPS
network
```

------------------------------------------------------------------------

# 51. Add/Remove Server Checklist
> ↳ **Context:** [where this fits in the learning path](#51-addremove-server-checklist)

When adding a server:

``` text
1. Create server
2. Add ring/bucket metadata
3. Determine affected ownership
4. Start data migration
5. Keep routing metadata/version consistent
6. Verify new owner
7. Monitor load
8. Complete migration
9. Remove old copies when safe
```

When removing a server:

``` text
1. Mark server draining
2. Stop new writes
3. Identify owned ranges/vnodes/buckets
4. Select replacement owners
5. Migrate data
6. Update routing metadata
7. Verify reads/writes
8. Remove server
```

------------------------------------------------------------------------

# 52. Routing Metadata Is a Production Component
> ↳ **Context:** [where this fits in the learning path](#52-routing-metadata-is-a-production-component)

The application cannot magically know:

``` text
position 17 -> S1
```

It needs routing metadata.

Conceptually:

``` text
Routing Metadata
-----------------------------
ring position -> physical server
virtual node -> physical server
bucket -> physical server
range -> physical server
```

This metadata must be:

-   consistent
-   versioned
-   updated safely
-   observable
-   recoverable

A routing bug can be as serious as a database bug.

------------------------------------------------------------------------

# 53. Consistent Hashing: Full Dry Run From API to DB
> ↳ **Context:** [where this fits in the learning path](#53-consistent-hashing-full-dry-run-from-api-to-db)

Suppose API:

``` text
GET /users/42/bookmarks
```

### Step 1 --- API receives request

``` text
user_id = 42
```

### Step 2 --- Choose shard key

``` text
SK = user_id
```

### Step 3 --- Hash the shard key

``` text
hash(42) = 16
```

### Step 4 --- Hash ring

Suppose virtual-node positions are:

``` text
3  -> S2
9  -> S4
11 -> S2
17 -> S1
22 -> S3
```

### Step 5 --- Binary search

Find:

``` text
first position >= 16
```

Result:

``` text
17
```

### Step 6 --- Map ring position

``` text
17 -> S1
```

### Step 7 --- Route

``` text
Request -> S1
```

### Step 8 --- Query

``` sql
SELECT title, url, timestamp
FROM bookmarks
WHERE user_id = 42;
```

### Step 9 --- Response

``` text
S1 -> bookmarks
      |
      v
API response
```

Complete flow:

``` text
GET /users/42/bookmarks
          |
          v
      user_id=42
          |
          v
      hash(42)=16
          |
          v
 binary search [3,9,11,17,22]
          |
          v
          17
          |
          v
        S1
          |
          v
       DB query
```

------------------------------------------------------------------------

# 54. The "Same Hash Space" Mental Model
> ↳ **Context:** [where this fits in the learning path](#54-the-same-hash-space-mental-model)

This is one of the most important concepts.

Both:

``` text
server identity
```

and:

``` text
data/sharding key
```

are converted into positions in the same hash space.

``` text
Server:
S1 -> hash -> 17

Data:
user42 -> hash -> 16
```

Then:

``` text
16
 |
 | clockwise
 v
17
 |
 v
S1
```

That is consistent hashing.

------------------------------------------------------------------------

# 55. What the Ring Actually Represents
> ↳ **Context:** [where this fits in the learning path](#55-what-the-ring-actually-represents)

The ring does **not** store all rows.

It represents:

``` text
ownership boundaries
```

Example:

``` text
3  -> S2
10 -> S3
17 -> S1
```

Conceptually:

``` text
(17,3]  -> S2
(3,10]  -> S3
(10,17] -> S1
```

The actual rows are inside the physical databases.

The ring is routing metadata.

------------------------------------------------------------------------

# 56. Why Virtual Nodes Reduce Large Ownership Ranges
> ↳ **Context:** [where this fits in the learning path](#56-why-virtual-nodes-reduce-large-ownership-ranges)

Without vnodes:

``` text
S1 ------------------------- large region
S2 ----
S3 --------
```

One physical server can accidentally own a huge interval.

With vnodes:

``` text
S1 -- S2 -- S3 -- S1 -- S3 -- S2 -- S1 -- S2 -- S3
```

Each physical machine owns many small intervals.

This gives finer-grained control.

When a machine is added:

``` text
new vnodes
   |
   v
take many small intervals
   |
   v
migration is distributed
```

------------------------------------------------------------------------

# 57. Vnode Count Is a Trade-Off
> ↳ **Context:** [where this fits in the learning path](#57-vnode-count-is-a-trade-off)

More vnodes:

### Advantages

-   smoother distribution
-   finer rebalancing
-   less chance of a giant range
-   better statistical balance

### Costs

-   more routing metadata
-   larger ring
-   more memory
-   more sorting/building work
-   more topology entries to manage

Therefore:

> More vnodes is not automatically better.

Tune it based on:

``` text
number of servers
workload skew
data volume
routing metadata size
rebalancing requirements
```

------------------------------------------------------------------------

## 57A. Choosing K: Production Trade-Off

The number of virtual nodes per physical server is a balancing parameter.

Let:

```text
N = physical servers
K = VNs per server
T = N × K
```

### More VNs

Benefits:

- smaller ownership intervals
- better statistical distribution
- smoother movement when nodes are added/removed
- lower chance that one physical server accidentally owns a very large interval

Costs:

- more routing metadata
- more memory
- more ring-update/gossip/state-sync overhead
- slightly larger binary-search input

### Fewer VNs

Benefits:

- smaller routing table
- lower metadata overhead

Costs:

- larger variance in ownership
- higher chance of uneven ranges
- more sensitivity to unlucky token placement

### Capacity weighting

If machines have different capacities, the number of VNs can be weighted conceptually:

```text
K_i = K_base × capacity_weight_i
```

Example:

```text
M1: baseline capacity → 100 VNs
M2: 2× capacity       → 200 VNs
M3: 4× capacity       → 400 VNs
```

This is a design technique, not a rule that every implementation must use.

### Statistical intuition

If token placement is treated as random, increasing the number of independent tokens reduces distribution variance. A common intuition is:

```text
σ ∝ 1 / √K
```

This is useful for understanding **why more tokens improve balance**, but it should not be presented as a universal production sizing formula.

> 🚨 **INTERVIEW CATCH:** Do not confidently state “K=256 is always correct.” Explain the trade-off and say that the actual value depends on cluster size, capacity, routing metadata, workload, and implementation.

# 58. Failure Scenario
> ↳ **Context:** [where this fits in the learning path](#58-failure-scenario)

Suppose:

``` text
S2 fails
```

With replication:

``` text
S2 primary
S4 replica
```

Traffic can be redirected according to the replication/failover policy.

Without replication, consistent hashing only tells you:

``` text
where the key belongs
```

It does not magically recover lost data.

Important:

> **Sharding is about partitioning. Replication is about redundancy.**

They solve different problems.

------------------------------------------------------------------------

# 59. Sharding vs Replication
> ↳ **Context:** [where this fits in the learning path](#59-sharding-vs-replication)

``` text
Sharding
--------
Split data

A -> shard 1
B -> shard 2
C -> shard 3
```

Replication:

``` text
Copy data

Shard 1
  |
  +--> Replica 1
  +--> Replica 2
```

Production systems commonly combine them.

------------------------------------------------------------------------

# 60. Senior Engineer Decision Framework
> ↳ **Context:** [where this fits in the learning path](#60-senior-engineer-decision-framework)
> 🚨 **INTERVIEW CATCH:** Do not start an HLD answer with “I will use consistent hashing.”
>
> Start with:
>
> ```text
> Access pattern
> → shard-key candidate
> → distribution
> → query locality
> → write locality
> → scaling behavior
> → hotspot behavior
> → then choose routing strategy
> ```


When given a new sharding problem, do not immediately choose:

``` text
Modulo
Range
Consistent Hashing
```

First ask:

``` text
1. What are the dominant APIs?
2. What key appears in those APIs?
3. What is the data distribution?
4. What is the write distribution?
5. Are there hot keys?
6. Do we need range queries?
7. Do we need global ordering?
8. How often will topology change?
9. How much migration can we tolerate?
10. Do we need replication?
11. How large is the routing metadata?
12. What happens when one shard fails?
```

Then choose the routing strategy.

------------------------------------------------------------------------

# 61. One Powerful Mental Model
> ↳ **Context:** [where this fits in the learning path](#61-one-powerful-mental-model)

Think of sharding as two separate problems:

``` text
PROBLEM A
---------
Which logical partition should this key belong to?

        key
         |
         v
    hash / range
         |
         v
logical partition
```

and:

``` text
PROBLEM B
---------
Which machine currently owns that partition?

logical partition
         |
         v
routing metadata
         |
         v
physical machine
```

This separation makes many designs easier to reason about.

------------------------------------------------------------------------

# 62. One-Page Mental Model
> ↳ **Context:** [where this fits in the learning path](#62-one-page-mental-model)

``` text
                    SHARDING
                       |
          +------------+------------+
          |                         |
      SHARD KEY                ROUTING
          |                         |
     user_id/order_id          hash/range
          |                         |
          +------------+------------+
                       |
                       v
                 DATA LOCATION
                       |
          +------------+------------+
          |            |            |
        Modulo       Range     Consistent
                                  Hashing
```

### Modulo

``` text
hash(key) % N
```

Fast:

``` text
O(1)
```

but changing N can remap many keys.

### Range

``` text
0-999     -> M0
1000-1999 -> M1
```

Good for ordered/range access, but ranges can become skewed/hot.

### Consistent Hashing

``` text
hash(server) -> ring position
hash(key)    -> ring position
                    |
                    v
          next server clockwise
```

Typical lookup with sorted vnode positions:

``` text
O(log V)
```

where V = number of virtual nodes.

Ring construction:

``` text
O(V log V)
```

------------------------------------------------------------------------

# 63. Final Complexity Cheat Sheet
> ↳ **Context:** [where this fits in the learning path](#63-final-complexity-cheat-sheet)
> 🚨 **MEMORIZE ONLY THIS SMALL PART**
>
> Let:
>
> ```text
> N = physical servers
> K = virtual nodes per server
> T = N × K = total tokens
> ```
>
> Then:
>
> ```text
> Generate tokens:      O(T)
> Sort tokens:          O(T log T)
> Binary-search lookup: O(log T)
> Token → server:       O(1)
> ```
>
> If `K` is treated as a fixed constant:
>
> ```text
> T = O(N)
> lookup = O(log N)
> ```
>
> This is the complexity distinction interviewers commonly probe.


Let:

``` text
N = physical servers
K = virtual nodes per server
V = N × K
R = number of ranges
B = number of logical buckets
```

  Operation                                  Typical Complexity
  --------------------------------- ---------------------------
  Modulo routing                                           O(1)
  Range lookup with binary search                      O(log R)
  Consistent-hash lookup                               O(log V)
  Vnode ring construction/sort                       O(V log V)
  Position -\> server mapping                              O(1)
  Bucket -\> server mapping           O(1) with direct metadata
  Sequential scan of ring                                  O(V)
  Binary search of ring                                O(log V)

### Important

Do not say:

``` text
consistent hashing request = O(N log N)
```

The better explanation is:

``` text
Ring build/rebuild = O(V log V)
Lookup             = O(log V)
Position mapping   = O(1)
```

If K is constant:

``` text
V = K*N

log V ≈ log N

Therefore lookup is approximately O(log N).
```

------------------------------------------------------------------------

# 64. Interview Answer Template
> ↳ **Context:** [where this fits in the learning path](#64-interview-answer-template)

If asked:

> "How does consistent hashing work?"

Answer in this order:

### 1. Problem

Modulo hashing causes many keys to remap when shard count changes.

### 2. Core idea

Put both servers and keys into the same circular hash space.

### 3. Server placement

``` text
hash(server_id) -> ring position
```

### 4. Data placement

``` text
hash(sharding_key) -> ring position
```

### 5. Routing

Find the first server position clockwise from the data position.

### 6. Optimization

Store positions sorted and use binary search.

``` text
O(log V)
```

### 7. Virtual nodes

Give each physical server many ring positions to improve distribution.

### 8. Scaling

Adding/removing a server affects primarily the intervals around its
vnode positions rather than remapping the entire keyspace.

### 9. Caveat

Hot keys can still overload a single server; consistent hashing does not
solve hot-key traffic by itself.

------------------------------------------------------------------------

# 65. Questions You Should Be Able to Derive
> ↳ **Context:** [where this fits in the learning path](#65-questions-you-should-be-able-to-derive)

Before considering this topic understood, answer these without
memorizing.

### Q1

Why is `user_id` sometimes a better shard key than `url`?

### Q2

If the API does not contain the shard key, what happens?

### Q3

Why can modulo hashing be O(1) but still operationally expensive when
servers change?

### Q4

Why does range sharding work well for range queries?

### Q5

Why can range sharding create hotspots?

### Q6

Why does consistent hashing need a ring?

### Q7

Why are server hashes and data hashes in the same hash space?

### Q8

If data hashes to 16 and server positions are:

``` text
3, 9, 11, 17, 22
```

which server position is selected?

### Q9

Why is binary search used?

### Q10

What is the complexity of lookup?

### Q11

What is the complexity of building the sorted ring?

### Q12

Why do virtual nodes help?

### Q13

What happens if one physical server owns many vnodes?

### Q14

What happens when a server is removed?

### Q15

Does consistent hashing eliminate data migration?

### Q16

Does consistent hashing solve hot keys?

### Q17

Why is fan-out different from nested sharding?

### Q18

How can global sorting work when data is on multiple shards?

------------------------------------------------------------------------

# 66. Final Senior-Level Mental Model
> ↳ **Context:** [where this fits in the learning path](#66-final-senior-level-mental-model)

Do not memorize:

``` text
modulo
range
consistent hashing
virtual nodes
binary search
```

as isolated topics.

Derive them from the problem:

``` text
I need to locate data
        |
        v
I need a shard key
        |
        v
I need a deterministic routing function
        |
        +-----------------------+
        |                       |
   shard count stable      shard count changes
        |                       |
      modulo              minimize movement
                                |
                                v
                       consistent hashing
                                |
                                v
                         hash ring
                                |
                                v
                         virtual nodes
                                |
                                v
                    sorted ring positions
                                |
                                v
                         binary search
                                |
                                v
                         physical server
```

And always separate:

``` text
KEY
 ↓
HASH / RANGE
 ↓
LOGICAL LOCATION
 ↓
ROUTING METADATA
 ↓
PHYSICAL MACHINE
 ↓
DATABASE
```

That is the core HLD sharding mental model.


## Interview Revision: High-Value Catches

Before an interview, make sure you can explain these without memorizing a script.

### Catch 1 — Why is `user_id` a shard key?

Because the API access pattern frequently identifies the user, allowing targeted routing. Then validate distribution, write traffic, growth, hotspots, and scaling behavior.

### Catch 2 — Is the sharding key the hash value?

No.

```text
SK = input
hash(SK) = routing coordinate
owner(token) = physical destination
```

### Catch 3 — Why hash the server?

To place its token/VN on the same coordinate system used by data hashes.

### Catch 4 — Why virtual nodes?

To break one large ownership interval into many smaller intervals distributed around the ring.

### Catch 5 — What does adding a server change?

Only the intervals affected by the new token(s) change owner. Existing data in those intervals must be migrated.

### Catch 6 — Why binary search?

Because the token positions are sorted.

```text
tokens = [3, 9, 11, 17, 22]
hash(SK) = 16

first token >= 16 = 17
17 → mapped physical server
```

Lookup is:

```text
O(log T)
```

not `O(T log T)`.

### Catch 7 — What is `O(T log T)`?

Building/rebuilding the sorted ring:

```text
T = N × K
sort(T tokens) → O(T log T)
```

### Catch 8 — Does consistent hashing eliminate rebalancing?

No. It **limits** the ownership change.

### Catch 9 — Does consistent hashing guarantee uniform traffic?

No. A hot key can still overload one owner.

### Catch 10 — Does sharding preserve global ordering?

No. If an API needs global ordering, it may require a cross-shard merge/top-K operation.

### Catch 11 — What if one user becomes extremely hot?

Consider techniques such as nested/bucketed sharding, workload-aware partitioning, caching, or controlled fan-out depending on the access pattern.

### Catch 12 — When should you use range vs hash/consistent hashing?

Derive it from the workload:

```text
Need efficient range queries / ordered ranges?
        → range/bucket-oriented design may fit

Need even distribution / point lookups?
        → hash-oriented design may fit

Need elasticity with limited remapping?
        → consistent hashing may fit
```

Do not present this as a universal rule; the actual workload and operational constraints decide the design.

---

[⬆ Back to Beginner → Advanced Learning Path](#learning-path-beginner--advanced)
