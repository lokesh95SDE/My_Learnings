# Session Overview

These notes cover asynchronous messaging and Kafka’s core building blocks: topics, brokers, partitions, replicas, and ordering. They also explain capacity planning for traffic spikes and compare monolithic and microservices architectures.\
The final sections cover API gateways, service-to-service communication, RPC, Protocol Buffers, and service data ownership.

## Messaging queues: decoupling essential work from follow-up work

A **messaging queue** lets you complete the must-have operation first, then handle additional work asynchronously. A producer publishes an event; one or more subscribers consume it and perform follow-up tasks. This keeps optional work from delaying the primary user-facing operation.

For example, when placing an order, saving the order is essential. Notifying the warehouse and sending a confirmation email can happen afterward. Similarly, for a WhatsApp-style message, saving the message is essential; notifications and analytics can be separate tasks. The discussion also raised sending an email if the recipient has been unavailable for 72 hours.

> *Use the queue to separate what must succeed now from what can be processed later.*

A basic queue is often explained as processing events in first-in, first-out (FIFO) order. In a distributed system, though, ordering guarantees depend on the messaging system and how the data is divided.

**Key takeaway:** Keep the primary operation focused; send non-essential follow-up work to subscribers for asynchronous processing.

## Kafka foundations: topics and brokers

**Kafka** is a distributed, persistent messaging system. Its core concepts—producers, consumers, and event grouping—are shared in spirit with other messaging systems, though names and details can differ.

A **topic** is a named category or stream of events. Examples include `user-created`, `order-placed`, `order-refund`, `user-login`, and `user-logout`. A topic gives consumers a way to focus on relevant event categories.

> *Think of a Kafka topic roughly like a database table: it groups related data. The analogy is about grouping, not about topics behaving exactly like tables.*

A **broker** is a machine in a Kafka cluster that stores and serves message data. A cluster uses multiple brokers to distribute the system’s work; the four-broker diagram was a simplified illustration, not a required cluster size. A broker can host data from multiple topics.

**Key takeaway:** Topics organize events logically; brokers are the machines that store and serve Kafka data.

## Partitions: distributing a topic’s data

A topic can be divided into **partitions**. A partition is a subdivision of a topic’s event stream, allowing its data and workload to be spread across brokers rather than kept on one machine.

For example, `user-created` could have two partitions. The partitions contain different events, not duplicate copies of every event. A broker can host multiple partitions, including multiple partitions from the same topic, if it has capacity.

Partitioning helps address capacity and traffic bottlenecks: a topic may grow beyond what one broker can store or handle, or receive enough traffic to overload one machine. Existing brokers can share the workload; adding brokers can provide more capacity.

Partitioning is analogous in some ways to database sharding: both divide data or workload across machines. The partition count and broker count do not need to match one-to-one.

**Key takeaway:** Partitions divide a topic’s workload so it can be distributed across brokers.

## Replicas: resilience and write acknowledgments

A **replica** is a copy of a partition. Partitioning distributes data; replication keeps copies of partition data so the system can better tolerate broker failures.

Replicas of the same partition must be placed on **different brokers**. If two copies are on the same broker, both may be lost or unavailable when that broker fails. A topic’s partition count and replication factor are separate configuration choices.

A replication factor of three across three brokers is a common guideline, not a universal rule. The right configuration depends on workload, reliability needs, and the number of available brokers. A new replica can be added while a system is running, but it must catch up before it is ready for its intended role.

An illustrative layout:

```text
Broker A                         Broker B
--------                         --------
user-created: partition 1        user-created: partition 1, replica 2
user-logout: partition 1         order-refund: partition 1, replica 2
                                 order-refund: partition 1, replica 3

```

“Partition 1, replica 2” means the second copy of partition 1 for that topic. The diagram is conceptual, not required notation.

In a leader–follower replication model, writes go to the leader, which coordinates replication to followers. The system’s acknowledgment policy determines when a write is considered successful. Waiting for replication acknowledgments before responding can improve durability; responding as soon as the leader accepts a write can be faster, but carries more risk if the leader fails before replication completes.

> ***Key insight:** Partitioning helps distribute data; replication helps protect it from broker failure. These solve different problems.*

**Key takeaway:** Choose partitions for distribution and replicas for resilience, then set write acknowledgments to match durability and latency needs.

## Routing events and preserving order

When a topic has multiple partitions, a **partitioner** decides which partition receives each event. For keyed events, the system commonly uses the key to select a partition. The key should reflect which events need to stay together—for example, a user ID for events belonging to the same user.

Kafka preserves order **within a partition**, not across an entire topic. If events A, B, and C are produced in that order, but A and C go to one partition while B goes to another, the A/C partition preserves A before C. The topic does not guarantee one global ordering between that partition and the partition containing B.

For unrelated users, that may be fine. For events from the same user, order may matter. If a user places three orders—for an iPhone, an AC, and an air fryer—in that order, out-of-order notifications could make it seem as though one order was missed.

```text
partition key = user ID

```

Using the same key routes related events to the same partition, where their order is preserved.

**Watch out:** A partition key does not create global topic ordering. It keeps keyed events together so their order can be maintained within their partition.

**Key takeaway:** If a group of events must remain ordered, route them to the same partition using a shared key.

## Capacity planning: load testing, autoscaling, and pre-scaling

Different topics can have very different traffic patterns. Orders might spike during a sale while user-creation events remain comparatively low. Capacity decisions should be based on **load testing, volume testing, and historical traffic data**, rather than assuming every topic needs the same resources.

**Autoscaling** adjusts the number of machines in response to demand. It can help, but it is not a complete scaling strategy on its own: sudden spikes may arrive faster than new capacity can be made ready.

For predictable, high-stakes events, **pre-scaling** means preparing additional capacity before the spike. A live sports event is a useful example: if traffic rises sharply just as a popular player comes to bat, a scaling delay may mean users miss part of the action.

A practical planning approach:

1. Run load or volume tests to estimate the system’s capacity and the event’s likely needs.
2. Use historical traffic patterns when available.
3. Choose a capacity level for expected demand, with a buffer in case this year’s traffic is higher.
4. Weigh the cost of temporarily idle capacity against the cost of poor service during the event.

> ***Key insight:** For sudden, predictable spikes, autoscaling may react too late. Pre-scaling prepares capacity before demand arrives.*

**Key takeaway:** Use tests and past traffic to plan for uneven demand; pre-scale when a predictable spike is too important to risk handling reactively.

## Monoliths and microservices: choosing an architecture

There is no universally better choice between a **monolith** and **microservices**. The fit depends on the use case and the system’s needs.

> *A monolith is defined by its deployment boundary, not by how many files it contains.*

A **monolithic application** is built and deployed as one unit. It can still be organized into modules or areas such as products, payments, orders, inventory, notifications, and authentication.

An e-commerce application might begin with relatively little traffic—about 100 users and 10 orders per day in the example—and rely on third parties for payment, inventory, or logistics. As it adds features in-house and grows (the example later reached around 10,000 users and 1,000 orders per day, then roughly 1 million users and 100,000 orders per day), its codebase grows too. At greater traffic, the application may be deployed across multiple servers. If authentication is provided by a third party, an adapter can connect the application to that external system.

### Monolith trade-offs

A monolith can be simpler to build, operate, and test as a whole:

- Related code lives in one application, which can make collaboration and end-to-end testing simpler.
- One application means less deployment and CI/CD overhead than managing many separate applications.
- Components can call one another directly, avoiding some network latency, retries, and timeouts.
- Operating one application can cost less than managing several.

As the codebase grows, though, changes may affect connected parts of the application. Developers may need to understand more dependencies and run broader regression or integration tests. A defect can have a wider potential impact when functionality shares a deployment. A shared build and release process can also make it harder to adopt a different technology for one capability.

A further limitation is **selective scaling**. If product browsing receives around 15 lakh requests per second while ordering receives only a few thousand, scaling the shared application to handle browsing traffic also deploys more copies of order, login, and other functionality. A concurrency issue such as overselling stock is a separate problem; adding servers alone does not resolve it.

### Microservices trade-offs

A **microservices architecture** divides a system into independently deployable applications. The core distinction is independent deployment, not simply separating code into more files.

In an idealized model, each service owns a distinct area of functionality and its data, and other services interact with it through an API. For example, product browsing and order management could be separate services with their own application servers.

This separation can support:

- **Selective scaling:** add capacity only to the busy service.
- **Independent builds and deployments:** update one service without rebuilding the whole system.
- **Fault isolation:** a problem in one service need not bring down unrelated functionality, though isolation is not guaranteed.
- **Technology flexibility:** a service can use a stack suited to its needs.

The trade-offs include more deployment pipelines and operational work, more coordination across teams, network overhead between services, and more involved integration testing. A new developer may be able to begin with a focused service, but cross-service work still requires understanding how those services interact.

**Key takeaway:** Choose the architecture for the use case: monoliths simplify shared operation and communication; microservices can enable independent scaling and deployment at the cost of distributed-system complexity.

## API gateways and service-to-service communication

An **API gateway** is a front door for requests entering a system of multiple services. It routes requests to the service responsible for handling them. For example:

```text
GET /products/101  → Product service
GET /users/1029    → User service

```

Routing can use information such as the path or headers. An API gateway has a front-door routing role similar to a load balancer, but it is not just another name for a load balancer. Examples mentioned include **Kong**, **AWS API Gateway**, and **NGINX**.

A user action may involve several services—for example, a product-related request followed by an order-management call and then an invoice-generation call. Service-to-service communication can be:

- **Synchronous:** the caller waits for a response.
- **Asynchronous:** the caller sends a message and does not need to wait for the receiving service to finish; a queue can support this pattern.

For incoming client traffic, the example uses HTTP/HTTPS up to the API gateway, with internal services communicating through RPC. That is an architectural example, not a requirement that every system use the same protocols.

**Key takeaway:** The gateway routes external requests; internal services can communicate synchronously or asynchronously according to the operation’s needs.

## RPC, Protocol Buffers, and service security

**RPC** (Remote Procedure Call) lets one service request that another service execute an operation, in a way that resembles calling a procedure or method over a network. RPC is not synonymous with a particular data format, and it does not inherently eliminate HTTP headers.

**Protocol Buffers (protobuf)** is a compact, language-neutral format for structured data. In a typical gRPC setup, gRPC handles RPC communication and protobuf encodes the messages. A protobuf schema and compatible generated code or libraries let services in different languages work with the same message definitions.

A service call can require encoding a message before sending it and decoding it on receipt. Protobuf does not remove those steps, but compared with JSON it can reduce message size and parsing overhead for suitable workloads. At high request volumes, small savings per request can add up: saving about 1 KB per request across 1 million requests is roughly 1 GB of data in decimal units.

A simplified request path:

```text
Client
  → HTTPS / JSON
  → API Gateway
  → internal RPC
  → Product service
  → internal RPC
  → Order service

```

The client-facing API contract and the internal service-to-service contract can differ. A service that only accepts JSON through a REST controller is not automatically an RPC endpoint; the receiving service needs an endpoint that understands the RPC protocol and message schema.

Authentication may happen at the gateway, but private networking alone does not guarantee internal calls are trusted. Internal calls may still need authentication, authorization, or identity propagation, depending on the security design. RPC can carry identity or authorization metadata.

> ***Key insight:** Protobuf is a message format, not a transport or RPC mechanism. And an internal network boundary does not automatically remove security requirements.*

**Key takeaway:** Keep the external API and internal service contract distinct, and choose message formats and security checks deliberately.

## SOA and microservices

**SOA (Service-Oriented Architecture)** is a broad approach that organizes software as services. It predates the widespread use of the term *microservices* and shares some goals, such as separating functionality into services.

The comparison discussed emphasized data ownership. In a microservices approach, each service generally owns its data, and other services access it through its API rather than reaching directly into its database. This supports clearer service boundaries. SOA is broader, however, and database-sharing practices vary; direct database access is not the sole defining difference between SOA and microservices.

**Key takeaway:** Treat service data ownership as an important boundary: in microservices, other services should generally use the owning service’s interface rather than access its database directly.

## Quick reference

- **Producer:** Publishes events.
- **Consumer/subscriber:** Reads and processes events.
- **Topic:** Named category or stream of events.
- **Broker:** Machine in a Kafka cluster that stores and serves data.
- **Partition:** Subdivision of a topic for distributing data and workload.
- **Replica:** Copy of a partition; place replicas of the same partition on different brokers.
- **Ordering:** Kafka guarantees order within a partition, not across a topic.
- **Partition key:** Use a shared key, such as user ID, when related events need to stay in order.
- **Capacity planning:** Use load tests, volume tests, and historical traffic; pre-scale for predictable spikes that autoscaling may not catch in time.
- **Monolith:** One deployment unit; simpler shared operation, but scaling is generally at the application level.
- **Microservices:** Independently deployable services; can scale separately, but add operational and communication complexity.
- **API gateway:** Front door that routes incoming requests to services.
- **RPC:** Remote service-call pattern; not a synonym for protobuf.
- **Protocol Buffers:** Compact message format commonly used with gRPC; requires compatible schemas and implementations.
- **Service data ownership:** In microservices, access another service’s data through its interface rather than directly through its database.
