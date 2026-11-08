# System Design Notes: Yelp-Like Nearby Business Search

The notes recap Kafka, monoliths, microservices, and service communication before introducing a system-design workflow through a Yelp-like product.
The case study focuses on requirements for local business discovery, then develops nearby-restaurant search from a full scan to grids and quadtrees.
Key design themes include clarifying scope, distinguishing static from dynamic locations, narrowing search space, and checking what an algorithm can actually guarantee.

## Foundations: distributed systems and service architecture

A **Kafka** cluster contains multiple brokers. A topic can be split into **partitions**, allowing its data to be distributed across brokers. **Replication** helps preserve data if a broker fails: replicas of the same partition should be placed on different brokers, though different partitions of a topic may reside on the same broker. A partitioning key can keep related events together—for example, routing events for the same order to one partition helps preserve their order within that partition.

A **monolith** is a single application or codebase. Function calls and shared testing can be straightforward, but as the codebase grows it may become slow to build, tightly coupled, harder to change safely, and difficult to scale selectively.

**Microservices** divide a system into independent applications or services. They can be developed and scaled separately, but introduce operational and communication complexity. An **API gateway** provides an entry point for client requests and routes them to backend services. Services can communicate through HTTP-based APIs or **RPC** (remote procedure call).

> ***Key insight:** Separating a system into services can make independent development and scaling easier, but it also creates new operational and communication work.*

**Key takeaway:** Know what partitions, replication, monoliths, microservices, gateways, and service-to-service communication are for—and what trade-offs they introduce.

## System-design workflow and product requirements

In a system-design interview, start by clarifying the product rather than jumping straight to architecture. A useful opening is to ask for a brief overview, then align on what the product does and who uses it.

Yelp was framed as a platform for discovering local businesses and reading or writing reviews, comparable in broad purpose to JustDial or Google Reviews. A user in an unfamiliar town might search for a service—such as a tailor—filter by location, and find relevant businesses. The businesses are listed on the platform; the platform does not own them.

A practical sequence for approaching a case study is:

1. Align on the problem statement and product overview.
2. Define **functional requirements**: what users can do.
3. Define **non-functional requirements**: how well the system must operate.
4. Make back-of-the-envelope estimates.
5. Draw a high-level system diagram.
6. Focus on the parts most distinctive or important for this problem.

Different products have different central challenges. The discussion contrasted WebSocket communication for a messenger with chunking for a video-streaming platform.

### Functional requirements and scope

The main user-facing capabilities proposed for the Yelp-like product were:

- Search for businesses by name, location, proximity, or services offered.
- View search results and business details.
- Review a business.

The audience may include everyday users and business owners. Business owners might want to promote their own business or research competitors; everyday users search for businesses and consult their details and reviews. Clarify early whether both groups are in scope, and whether the product must support web, mobile, or other devices.

Promotion versus discovery was raised as a scope question. The working assumption here is that discovery and reviews are the core capabilities; businesses receive equal exposure, and paid subscriptions do not receive greater advertising visibility.

### Non-functional requirements

Clarify operating expectations before choosing an architecture. Questions raised included:

- How many total users and peak concurrent users should the system support?
- What are the expected traffic and request rates?
- How many business registrations and reviews are expected per day and in total?
- In which regions should the product be available, and where will it be hosted?
- What latency is acceptable, especially for search?

Search latency was identified as a high priority: users should be able to find businesses quickly.

**Key takeaway:** Establish the product, users, capabilities, and operating constraints before designing the system.

## Consistency and location-update patterns

The discussion raised availability and consistency, including the **CAP theorem**, as design considerations. **Eventual consistency** was proposed as a possible fit for business registrations and reviews: a newly registered business or submitted review might not appear identically everywhere immediately. This was a proposal, not a settled design decision.

Location-based systems also differ in how frequently the locations they search change:

- **Static locations**, such as restaurants, change rarely.
- **Dynamic locations**, such as drivers or moving friends, change frequently.

Dynamic locations need more frequent location updates. Static locations generally need less frequent updates and may tolerate eventual consistency.

> ***Key insight:** Before designing location search, identify whether the locations being searched are static or dynamic; that difference affects how often updates must be handled.*

**Key takeaway:** Treat consistency as a requirement to clarify, and let the update pattern reflect whether locations are static or moving.

## Nearby-restaurant search: the baseline

A conceptual nearby-restaurant API takes a user’s latitude and longitude and returns nearby restaurants. A restaurant record might include an ID, title, rating, and latitude/longitude.

The simplest approach compares the user’s location with every restaurant:

1. Read each restaurant record.
2. Calculate its distance from the user.
3. Keep the closest `k` results.
4. Return them.

For a simplified planar-coordinate example:

```text
distance_squared = (x_user - x_restaurant)^2
                 + (y_user - y_restaurant)^2

```

When comparing distances, the square root is unnecessary because squared distances preserve the same ordering.

To keep only the closest `k` candidates while scanning, use a **max-heap** whose root is the farthest restaurant currently retained:

1. Add each restaurant and its distance.
2. If the heap grows beyond `k`, remove the farthest one.
3. After scanning all records, the heap contains the `k` closest candidates.

For the nearest 20 restaurants, use `k = 20`. For `n` restaurants, this takes `O(n log k)` time and `O(k)` space. If `k` is a small fixed constant, the time is effectively `O(n)`. The limitation is that every restaurant is still examined.

**Watch out:** A radius or database sort describes the desired result, but a brute-force implementation still needs to calculate distances for all records unless it can use an index or another way to narrow the search.

**Key takeaway:** A heap makes a full scan efficient when `k` is small, but it does not avoid scanning the whole dataset.

## Narrowing the search with boxes and grids

A first way to reduce the number of candidates is to search a region around the user rather than the whole dataset.

### Expanding bounding boxes

For a user at `(x, y)`, a rectangular region can be defined with coordinate offsets `delta_x` and `delta_y`:

```text
x - delta_x <= restaurant.x <= x + delta_x
y - delta_y <= restaurant.y <= y + delta_y

```

A database query for that box could look like:

```sql
SELECT *
FROM restaurants
WHERE coordinate_x BETWEEN :x - :delta_x AND :x + :delta_x
  AND coordinate_y BETWEEN :y - :delta_y AND :y + :delta_y;

```

If the box does not contain enough candidates, increase the offsets and search a larger box. The offsets might increase by a fixed amount or double each time. A circular radius is another natural way to describe “nearby,” while a rectangular coordinate filter is straightforward to express with independent bounds.

**Watch out:** A box is a candidate filter, not proof that its contents are the true nearest results. A restaurant near a corner of the box may be farther away than one just outside it. To return exact nearest results, rank candidates by distance and ensure that excluded points cannot be closer than the kth candidate. Also define a stopping condition for cases where fewer than `k` restaurants exist.

### Fixed-size grid cells

Another approach divides the map into fixed-size rectangular cells. A location can be mapped to a **cell ID**, such as a grid row and column, and restaurants can be looked up by their cell.

```text
User latitude/longitude
        ↓
    Cell ID
        ↓
Restaurants in that cell

```

If the user’s cell contains too few restaurants, expand the search to surrounding layers of cells, then continue outward as needed. A proposed heuristic was to tune the cell size so that a typical cell contains approximately the desired result count—for example, around 100 restaurants when the target is 100. This can be tuned iteratively: if the average count is too high, try smaller cells; if it is too low, try larger ones.

The cell size is a trade-off. Larger cells cover more area per search step; smaller cells may require more expansions. Because restaurant density varies, an average target cannot guarantee that every cell contains the same number of restaurants.

**Watch out:** Finding enough candidates in an expanding box or ring does not automatically guarantee that they are the nearest ones. Exact top-`k` search needs an appropriate stopping condition; otherwise, treat the result as approximate.

**Key takeaway:** Spatial filtering reduces the search area, but region size and stopping rules determine both efficiency and correctness.

## Variable-size regions: quadtrees

A fixed grid treats dense and sparse areas identically. A **quadtree** addresses this by recursively dividing a two-dimensional region into four smaller regions. Dense areas can be subdivided more finely, while sparse areas remain larger.

Choose a threshold `X` for the maximum number of restaurants a region should contain:

1. Count the restaurants in a region.
2. If the count is greater than `X`, divide the region into four subregions.
3. Apply the same rule recursively to each subregion.
4. Stop subdividing a region when its count is `X` or fewer; it becomes a **leaf**.

For example, with `X = 5`, a region containing more than five restaurants is subdivided, while one containing five or fewer is a leaf.

> ***Key insight:** Subdivide based on how much data a region contains, rather than dividing every part of the map to the same depth.*

### Representing a region and its nodes

An axis-aligned rectangle can be determined by two diagonally opposite corners, or by its center and one corner. The example uses the center and top-right corner. Whichever representation is chosen, use it consistently.

A node may store:

- The region’s center and the coordinates of its top-right corner.
- The restaurant count.
- A restaurant list if it is a leaf.
- Child-node references if it is subdivided.

An internal node represents its region through its descendants; the restaurant list is stored at the leaves. A subdivided node has **all four children or none**—there are no one-, two-, or three-child cases.

To locate the leaf for a user’s coordinates:

```text
current = root

while current has children:
    current = the child region containing the location

return current

```

This reaches the most specific region containing the point.

### Search cost and neighboring regions

Finding the leaf takes `O(h)`, where `h` is the quadtree’s height. If the tree is balanced, the height is around `log N`; if it is skewed, it can be as large as `N`. Tree lookup is therefore `O(h)`, not automatically `O(log N)`.

If the user’s leaf contains too few restaurants, nearby regions may need to be checked. The proposed idea was to use the region’s boundaries and small coordinate offsets to locate neighboring regions through the same location-lookup function. This is different from moving to the leaf’s parent: parent-child relationships describe subdivisions, not geographic closeness.

**Watch out:** The neighbor lookup was not fully specified. With variable-sized regions, a region can have multiple adjacent leaves along one edge, so checking a fixed set of sample points is not automatically a complete way to find every relevant neighbor. A robust neighbor-search and exact stopping rule are still needed for guaranteed nearest results.

**Key takeaway:** Quadtrees adapt region size to data density, but efficient and correct nearby search also requires a reliable way to identify adjacent regions.

## Quick reference

- **System-design order:** overview → functional requirements → non-functional requirements → estimates → high-level diagram → case-specific focus.
- **Nearby search baseline:** full scan plus max-heap of size `k`; `O(n log k)` time and `O(k)` space.
- **Spatial filtering:** boxes and grids reduce candidates; tune region size to the use case and density.
- **Quadtree:** split a region into four when its count exceeds threshold `X`; search from the root to the leaf containing the location.
- **Tree lookup:** `O(h)`; `O(log N)` only when the tree height is logarithmic.
- **Correctness check:** finding `k` candidates is not by itself proof they are the nearest `k`; use a suitable stopping condition.
- **Location updates:** static locations change rarely; dynamic locations require more frequent updates.
