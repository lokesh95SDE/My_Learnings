# Session Overview

This revision covered **load balancer basics**, then moved into the core ideas of **sharding** and **sharding-key selection** for a bookmarks-style system. The discussion then compared **sharding strategies** such as modulo-based routing and introduced the motivation for **consistent hashing**.
The second half focused on **API-driven shard-key choice**, trade-offs around **multiple access patterns**, and the difference between **high-level design knowledge** and **hands-on implementation practice**.

## Load Balancer Basics

A **load balancer (LB)** sits in front of application servers and decides where traffic should go. The main ideas reviewed were how the LB discovers servers, how it distributes requests, and how it checks whether a server is healthy.

Application servers register themselves with the LB when they come up, and if they restart they register again. The LB keeps track of the active pool of servers rather than hardcoding them.

For distributing requests, two common algorithms were revisited:

- **Round robin**: send requests to servers in turn.
- **Weighted round robin**: like round robin, but higher-capacity servers get a larger share.

> ***Key insight:** Weighted round robin is based on relative capacity, which can depend on resources like RAM and machine strength.*

Health checking was also split into two approaches:

1. **Heartbeat from server to LB**
   - The server periodically sends a signal.
   - If the LB stops receiving heartbeats within the expected interval, the server is treated as dead.
2. **LB probes the server**
   - The LB actively checks the server.
   - If the server does not respond in time, it is marked unhealthy.

**Key takeaway:** A load balancer maintains server membership, spreads traffic fairly, and removes unhealthy servers from rotation.

## Sharding: Why It Exists and What It Means

The discussion then shifted to the bookmarks app and the problem of data outgrowing a single database machine. When a dataset becomes too large for one server, the data has to be split across multiple physical machines.

That leads to **sharding**: dividing a table’s data across multiple database servers so the table is logically one dataset but physically spread out.

The core question sharding answers is:

> *Given a row, which machine should store it?*

> ***Key insight:** Sharding is not just splitting data; it is splitting data in a way that supports both distribution and future retrieval.*

A useful distinction was made between:

- **Partitioning**: splitting data in a broader sense, which may happen inside one database or across multiple places.
- **Sharding**: splitting data across different database machines.

The important conceptual rule is that sharding is about distributing records while still making them findable later.

**Key takeaway:** Sharding is the technique for spreading a table across multiple machines while preserving a deterministic way to locate each row.

## Sharding Key: The Core Rule

A **sharding key** is the attribute used to decide which shard a row belongs to. The most important rule is:

> ***All rows with the same sharding-key value must go to the same shard.***

This is the foundational idea behind sharding. It means the key is not just a label; it is the routing basis for placement.

A common misunderstanding was corrected clearly:

- A sharding key does **not** mean “one value = one shard.”
- It means “same value = same shard.”

So if `user_id` is the sharding key, all rows for the same user go together, but many different user IDs may still share one shard.

The chosen key is only the input to placement. The exact shard number comes from a separate routing function, which was introduced later as **consistent hashing**.

> ***Key insight:** The sharding key defines grouping by equal values; it does not by itself define the exact shard number.*

**Watch out:** Do not assume that every distinct key value gets its own machine. Many values can map to the same shard.

**Key takeaway:** A valid sharding key guarantees consistent placement for equal values, not uniqueness of shard per value.

## Choosing a Sharding Key from a Real Table

To make the idea concrete, the bookmarks table was used with fields like:

- `bookmark_id`
- `title`
- `url`
- `user_id`
- `timestamp`
- `tags`

The instructor treated all of these as candidate sharding keys at the beginning of the discussion. The key question was not “Which column exists?” but “Which column best fits the app’s access pattern?”

The bookmark example showed why a column like `title` is often a weak divider on its own:

- many different rows can share the same title
- titles repeat across users
- title alone does not necessarily align with the main way the application queries data

The important takeaway was that a sharding key should help distribute data in a way that still supports efficient lookup and grouping.

> ***Key insight:** Good sharding-key choice depends on how the system reads and writes data, not just on whether a column exists.*

**Key takeaway:** Start from the data model, but choose the sharding key based on access patterns.

## Sharding Key Selection Depends on APIs

A major theme of the session was that **API design drives sharding-key choice**. The best sharding key is the one that aligns with the dominant access path.

For the bookmarks design, the main APIs were:

- **GET bookmarks for a user ID**
- **POST / create a single bookmark**

The reasoning process was:

- If the main operation fetches all bookmarks for one user, then **user_id** is a strong candidate.
- If you choose a key like `title`, the user’s bookmarks are likely scattered across many shards.
- If you choose **user_id**, all bookmarks for a user stay together, so the main query can hit one shard.

> ***Key insight:** Pick the sharding key around the dominant access pattern, not around an arbitrary column.*

This also means the sharding decision is tied to the application’s endpoints. If the endpoints change later, the sharding key may need to be revisited.

**Watch out:** If two APIs want different sharding keys, you have to think about traffic volume and which path matters most.

**Key takeaway:** The API with the heaviest or most important traffic should usually shape the sharding key.

## Example: Bookmark ID vs User ID

There was an important clarification about the bookmarks system:

- If **bookmark_id** is the sharding key, then all records for the same bookmark ID go to one shard.
- If **user_id** is the sharding key, all bookmarks for the same user go to one shard.

The instructor used this to contrast query patterns:

### Fetch by `bookmark_id`

If you fetch a bookmark by its ID, the routing layer can send the request to **one shard**.

### Fetch by `user_id`

If you fetch all bookmarks for a user and the sharding key is **not** `user_id`, the system may have to check many shards and combine results.

A worked example used five shards and showed that one user’s bookmarks could be spread across shards if sharding is based on `bookmark_id`. In that setup, fetching by bookmark ID is cheap, but fetching all data for a user can be expensive.

> ***Key insight:** A user’s data can be scattered even when each individual bookmark is pinned to one shard.*

**Key takeaway:** The best sharding key depends on whether you want fast lookup by item ID or fast grouping by user.

## Sharding, Multiple Tables, and Multiple Access Patterns

Sharding is chosen **per table**, not globally for the entire system. One table can have one sharding design, while another table uses a completely different one.

That means:

- a bookmarks table can shard by one key
- an orders table can shard by another key
- a wishlist table can also choose independently

If two tables both have access patterns centered on `user_id`, they can both use `user_id` as their own sharding key. That does **not** mean they share the same physical shard layout; it just means they each independently arrived at the same useful choice.

The session also covered the harder case where one table must support **multiple high-traffic access patterns**. If traffic is small, you may optimize for one path and accept that another is slower. If traffic is huge, you may need duplicated layouts or replicated systems, which introduces consistency challenges.

> ***Key insight:** When the same logical data needs to support very different access patterns at scale, you may need replicated shard layouts, not one simple sharding scheme.*

**Watch out:** If you support the same data in multiple layouts, keeping them consistent becomes difficult.

**Key takeaway:** Sharding decisions are table-specific and driven by traffic patterns, not by a single universal rule.

## Composite Sharding Keys and API Drift

Composite sharding keys were treated cautiously. A composite key uses more than one attribute together, such as `(attribute1, attribute2)`.

The problem is that if an API later filters only on one part of that composite, routing becomes inefficient. You may have to search across multiple shards because a partial match does not identify a single destination.

> ***Key insight:** Composite sharding keys are only safe if your access patterns always use the full composite.*

A worked example showed that if `(X, Y)` determines the shard, then looking up by `X` alone does not tell you where the row lives.

The other major warning was that APIs change. If a new API becomes important later, the original sharding key may stop being the best fit. Changing the sharding key after data already exists means you need **data migration**, which is expensive and operationally sensitive.

**Watch out:** Public API changes can force shard rethinking and data movement.

**Key takeaway:** Choose sharding keys with future access patterns in mind, because changing them later is costly.

## Modulo-Based Shard Selection

Once the qualitative idea of sharding was clear, the session moved to the quantitative question: given a key, how do you map it to a shard?

A first simple solution is:

```text
shard_number = sharding_key % number_of_shards
```

This is attractive because it is:

- **fast**
- deterministic
- easy to implement

For example, with `user_id` as the sharding key and 2 machines, each user ID maps to machine 0 or 1 based on the remainder.

> ***Key insight:** Modulo is the natural first idea because it turns a large key space into a small machine set in a cheap, repeatable way.*

The distribution tends to become approximately even as the dataset grows, though not perfectly balanced at small sizes.

**Key takeaway:** Modulo gives a simple deterministic routing rule as long as the shard count stays fixed.

## Why Plain Modulo Breaks Down

The weakness of modulo sharding is that it is highly sensitive to the number of shards. If you go from 3 shards to 4 shards, the expression changes from `key % 3` to `key % 4`, and many keys are remapped.

That causes a lot of unnecessary data movement and rebalancing.

> ***Key insight:** A good sharding strategy should minimize movement when machines are added or removed.*

This is why plain modulo is not enough for real systems that must scale dynamically. It is a good starting point, but not the final answer.

**Watch out:** Adding one shard with modulo can reshuffle most of the dataset.

**Key takeaway:** Modulo is simple, but it becomes painful when the shard count changes.

## Consistent Hashing: The Motivation

The session introduced **consistent hashing** as the eventual better answer to the shard-mapping problem.

The essential idea is that once a key maps to a shard, future lookups for that same key should map to the same shard unless the system deliberately rebalances. This is the consistency part of consistent hashing.

It was framed as the more robust alternative after examining the weaknesses of modulo-based routing.

> ***Key insight:** The routing rule must stay stable enough that old data remains discoverable after writes.*

**Key takeaway:** Consistent hashing exists to preserve stable key-to-shard mapping while reducing disruption when the shard set changes.

## System Design Thinking: What Matters in HLD

The discussion closed with a broader system-design perspective. High-level design topics are not learned fully in a day or even in a few days. The goal is to build the right mental pillars so later topics are easier to absorb.

For HLD interviews, the core skills are:

- understanding architecture
- reasoning about trade-offs
- choosing components based on access patterns
- explaining consistency and scalability choices

Hands-on implementation is useful, but not usually the main thing being tested in HLD interviews.

The advice was:

- build side projects if you want implementation practice
- use open-source tools where possible
- read deeply when you need stronger intuition
- rely on case studies and architectural reasoning for interview prep

A strong reading recommendation was **Designing Data-Intensive Applications**, especially for senior or team-lead level preparation, because it rewards repeated reading.

> ***Key insight:** Reading helps you answer architecture questions; building helps you internalize the concepts.*

**Key takeaway:** For HLD interviews, architecture understanding and trade-off reasoning matter more than implementation depth.

## Quick Reference

### Load Balancers

- **Round robin**: cycle through servers in order
- **Weighted round robin**: give more requests to higher-capacity servers
- Health checks:
  - **heartbeat** from server to LB
  - **probe** from LB to server

### Sharding Basics

- **Sharding** = split a table across multiple physical machines
- **Sharding key** = attribute used to decide shard placement
- Rule: **same sharding-key value → same shard**
- One key value can map to the same shard as other key values

### Choosing a Sharding Key

- Choose based on **API access patterns**
- Favor the field used by the most important query path
- If your main API is “get all records for X,” X is often a strong sharding key
- Different tables can have different sharding keys

### Common Pitfalls

- Do not assume **one key value = one shard**
- Do not assume partitioning always means “same database”
- Composite sharding keys are risky if future queries use only part of the composite
- Changing the sharding key later may require **data migration**

### Modulo Routing

```text
shard = key % number_of_shards
```

- Fast and deterministic
- Approximate uniformity over large datasets
- Bad when shard count changes, because many keys get remapped

### Consistent Hashing

- Used to keep routing stable as shards change
- Goal: reduce data movement when machines are added or removed

### HLD Interview Focus

- Architecture
- Trade-offs
- Scaling
- Consistency vs availability
- Case-study reasoning over low-level implementation
