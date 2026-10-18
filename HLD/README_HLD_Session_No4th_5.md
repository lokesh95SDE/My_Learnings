# Session Overview

This session covered **consistent hashing** in depth: the ring model, efficient lookup, failure handling, and the use of multiple virtual positions per server. It then moved into **caching**: what it is, where it shows up in browsers and DNS, and how it improves performance.\
The later part focused on **streaming and CDNs**: chunk-based video delivery, live streaming, offline downloads, and why CDNs are crucial for serving static media close to users.

It also touched on **system design study strategy**, including which topic buckets and case studies to prioritize.

## Consistent Hashing

**Consistent hashing** is a strategy for assigning keys to servers so that lookups are fast, distribution is fairly uniform, and server changes cause minimal reshuffling. The core model is a **virtual circular ring**: servers are hashed onto positions on the ring, keys are hashed onto the same ring, and each key is assigned to the first server encountered when moving clockwise.

> *Think of it as: hash the key to a point, then walk clockwise until you hit responsibility.*

The basic flow is:

1. Hash the **server** onto the ring using one hash function.
2. Hash the **key / sharding key / user ID** using another hash function.
3. Move clockwise from the key’s position.
4. Assign the key to the first server position you encounter.

The ring is made very large conceptually so that hash values spread out well and distribution becomes more uniform.

> ***Key insight:** The ring is not just a picture; it is what makes the assignment deterministic, stable, and easy to update when servers change.*

### Efficient lookup on the ring

A naive clockwise scan over the ring would be too slow. The important optimization is to keep the server positions in **sorted order** and use **binary search** to find the first position greater than or equal to the key’s hash.

For example, if the sorted server positions are:

```text
[3, 9, 11, 17, 22]
```

and the key hashes to `16`, you search for the smallest value `>= 16`, which is `17`.

Then you use the mapping for that position to recover the actual server.

> ***Key insight:** First find the next ring position efficiently, then map that position to the server.*

**Watch out:** The ring position and the actual server are not the same thing. Finding `17` is only useful if you also store which server owns that position.

### Why two hash functions were used

The session used separate hash functions for server placement and key placement:

- one for servers
- one for keys

This helps preserve randomness and avoid unwanted distribution patterns.

> ***Key insight:** Decoupling server placement from key placement improves distribution quality.*

### Why consistent hashing is valuable when servers change

The major advantage is that when a server is added or removed, only a **small portion** of keys need to move. That is much better than reassigning everything.

When a server is added:

- insert the new position into the ordered ring
- add the position-to-server mapping
- migrate only the keys in the affected interval

When a server is removed:

- only the keys that used to belong to that server need to be reassigned

> ***Key insight:** The win is minimal remapping, not just lookup speed.*

**Watch out:** Linear traversal around the ring is too slow, and unsorted storage does not solve the search problem.

**Key takeaway:** Consistent hashing works because a huge hash ring plus ordered lookup gives you stable key assignment with limited movement when the cluster changes.

## Optimized Consistent Hashing with Multiple Virtual Positions

The session then addressed the failure case of the basic ring: if one server dies, its responsibility can be dumped onto a single neighbor, causing overload. The fix was **optimized consistent hashing**, where each physical server is assigned **multiple virtual positions** on the ring.

Instead of one hash per server, you use multiple hashes, such as:

- `HX1(serverID)`
- `HX2(serverID)`
- `HX3(serverID)`

This places the same physical server at several ring positions, breaking one large responsibility range into multiple smaller chunks.

> ***Key insight:** Multiple virtual positions per server spread failure load more evenly.*

For example:

- `S1` might appear at positions `2, 11, 17`
- `S2` might appear at `7, 14, 19`
- `S3` might appear at `5, 9, 16`

Now each server owns several smaller intervals instead of one large one.

### Why this helps during failure

If a server fails, its load is no longer handed to just one successor. Instead, the lost responsibility is spread across multiple nearby positions and servers.

This is not replication:

- the server is not duplicated physically
- these are **virtual nodes / positions** on the ring

> ***Key insight:** Virtual positions are a load-distribution trick, not replicas.*

### Handling collisions and choosing the number of positions

If two hashes land on the same position, that placement is avoided and a different position is chosen. The ring uses one unified structure of positions mapped to servers; you do **not** split it into multiple arrays.

The number of virtual positions per server is a practical decision:

- based on load testing
- sometimes guided by rough rules of thumb

Examples mentioned:

- around **100 shards** → maybe **3–4** hash points
- around **1,000 shards** → maybe **10** hash points

> ***Key insight:** The right number of virtual positions depends on scale and balancing needs.*

**Key takeaway:** Multiple virtual positions make consistent hashing safer under server failure because the redistributed load is spread out instead of concentrated.

## Caching

**Caching** is storing or pre-computing data so you do not have to fetch it from the original source repeatedly. The purpose is performance: less repeated work, lower latency, and less load on the source system.

> *Caching is basically a copy kept nearby so you don’t keep paying the full cost again.*

The motivating example was a user repeatedly refreshing a page. If the data has not changed, it is wasteful to keep querying the database or origin every time.

### Where caching shows up

Common examples included:

- repeated page refreshes
- DNS lookups
- browser-side reuse of values

For DNS, the client can store the resolved IP locally so it does not need to resolve the same domain every time.

> ***Key insight:** Caching matters most when the same data is requested again and again.*

### Browser-level caching and local storage

The browser can store lightweight data locally through **local storage**. This is useful for small pieces of state, not huge datasets.

Examples of browser-cached assets:

- images
- CSS
- other static resources

These are good cache candidates because they help render the page quickly even before fresh dynamic data arrives.

> ***Key insight:** The page shell can load first from cached static assets while dynamic data catches up in the background.*

**Watch out:** Local storage is lightweight and is not suitable for thousands of records.

### Cookies vs cache

Cookies are separate from cache. They are different browser mechanisms and should not be treated as the same thing.

**Watch out:** Do not confuse browser cache with cookies or with autocomplete/type-ahead behavior.

### Caching vs type-ahead

Autocomplete or search suggestions are not the same thing as caching, even if they may use cached data internally. Caching is about keeping duplicate data from the original source for faster reuse.

### Design perspective on caching

The main point was not implementation details, but how to evaluate options:

- identify possible caching approaches
- compare trade-offs
- choose what fits the use case

The session explicitly framed caching as a design topic with multiple variants, not as a single implementation pattern.

**Key takeaway:** Caching is a performance optimization that stores reusable data close to where it is needed, and the key skill is knowing when and why to use it.

## CDN and Static Content Delivery

A **CDN (Content Delivery Network)** is a distributed set of servers that keeps content physically closer to users, lowering latency. It is especially useful for **static files** such as images, videos, audio, and other directly deliverable assets.

> *The closer the content is to the user, the faster it feels.*

A CDN is not for business logic or structured application data. It is meant for content that can be served “as is.”

### Where CDN fits

The session treated CDN as a special kind of server-side caching/storage for static content. It is used to serve content before the application layer in many architectures, especially when the goal is to reduce latency and load.

Examples of when CDNs are useful:

- static images
- files
- video streaming
- global performance optimization

### Geographic routing

Users in different regions may be routed to different CDN nodes or backends depending on:

- geography
- ISP
- proximity to the best edge location

This is why two users entering the same URL may not hit the same machine.

> ***Key insight:** CDN routing is geographically aware, not just URL-based.*

### CDN providers

The session mentioned real providers such as:

- **Akamai**
- **CloudFront**
- **Cloudflare**

These services are used because building a global CDN from scratch is complex.

### CDN vs origin

The CDN is an optimization layer in front of the origin, not a replacement for the application backend. The application still owns the data and APIs.

**Watch out:** Do not treat a CDN as a place for general application data or logic.

**Key takeaway:** CDNs speed up delivery of static content by serving it from nearby edge locations instead of a faraway origin.

## Video Streaming, Chunking, and Live Content

Large media files are delivered using **chunks** rather than as one giant download. The client requests and plays the chunks sequentially, which lets playback start quickly instead of waiting for the entire file.

> *Streaming is “download a little, play a little, keep fetching in the background.”*

### How chunked streaming works

1. The client requests the first chunk.
2. The chunk is downloaded and played.
3. While it plays, the next chunk is requested.
4. Playback continues as more chunks arrive.

This is why streaming platforms can start almost immediately even for large videos.

### Seeking within a video

When you drag the progress bar to another point:

- the platform requests the chunk corresponding to that position
- it does **not** download all earlier chunks first
- if the chunk is not already available, you may see buffering

> ***Key insight:** Seeking means jumping to the right chunk, not downloading everything before it.*

### How to observe it

The session suggested using browser developer tools:

- open **Inspect**
- go to the **Network** tab
- play a video
- watch requests for fixed-duration chunks

### Live streaming

Live streaming adds a real-time ingestion step:

- the camera records the event
- the video is periodically uploaded to the cloud
- the cloud processes it
- then chunk-based playback proceeds

This is more demanding because the system has to ingest and prepare content continuously.

### Downloads for offline viewing

Even when you click download, the content is still typically transferred in chunks and stored locally. The app handles playback, often with encryption or protection, so you do not just browse raw files freely.

> ***Key insight:** “Download” still usually means chunked transfer plus local storage for offline playback.*

**Watch out:** CDNs and chunking are related but not identical ideas. Chunking is about delivery format; CDN is about geographically efficient serving.

**Key takeaway:** Streaming systems use chunking to balance fast startup, smooth playback, and efficient bandwidth use.

## Why CDNs Matter for Streaming

For streaming workloads, especially popular live events, the application server often adds little value if it only fetches already-prepared chunks and returns them. In that case, routing every request through the full application stack is wasteful.

CDNs become important because they:

- serve chunks closer to users
- reduce repeated hits on the origin
- absorb massive demand more efficiently

The session used a simplified architecture with UI, load balancer, application servers, and chunk storage to show why direct chunk delivery can become a bottleneck if handled only by the app layer.

> ***Key insight:** If the server is just handing out prepared chunks, you should ask whether a CDN can do it better.*

**Key takeaway:** For heavy media delivery, CDNs are often the right layer because they are built to serve the same static chunks at scale.

## System Design Study Focus

The session also listed the main topic buckets to prepare for system design interviews:

- **Master-slave architecture**
- **Caching**
- **Microservice architecture**
- **Messaging queues**
- **Kafka**
- **SQL vs NoSQL**
- **Types of NoSQL databases**
- **Case studies**
- at least **two end-to-end system design case studies**

> ***Key insight:** In the final stretch, case studies are often more useful than broad theory because they show how to structure answers.*

### Interview prep strategy

For limited prep time, the advice was to:

- review as many system design case studies as possible
- focus on how each one is approached
- use AI or quick references to clarify unfamiliar terms
- stick to the curated material rather than collecting random resources

**Key takeaway:** System design prep should prioritize case studies, trade-offs, and decision-making over memorizing implementation details.

## Quick Reference

- **Consistent hashing**: hash server + hash key onto a virtual ring; move clockwise to the next server.
- **Lookup**: store ring positions in sorted order; use binary search for the first position `>= key_hash`.
- **Virtual nodes**: multiple positions per server help spread failure load and improve balance.
- **Caching**: store reusable data near the consumer to avoid repeated original-source fetches.
- **Browser cache / local storage**: good for small, reusable data and static assets.
- **Cookies**: separate from cache.
- **CDN**: globally distributed cache/storage for static content like images, video, and files.
- **Streaming**: chunk-based delivery; seek by jumping to the relevant chunk.
- **Live streaming**: adds real-time ingestion and cloud processing before playback.
- **System design prep**: focus on case studies plus core buckets like caching, queues, Kafka, SQL/NoSQL, and architectures.
