# Session Overview

These notes cover unreliable network requests and idempotency, plus database sharding trade-offs in a messaging system.\
They then build from WebSocket delivery to synchronous versus asynchronous work, message queues, Pub/Sub, event design, and downstream failure handling.

## Retries and idempotency

A network request can be delayed or lost even when the application usually appears seamless. The client sends a request and waits for an acknowledgement. If no acknowledgement arrives before a timeout—perhaps eight seconds—it may retry so it does not wait indefinitely.

A timeout does **not** reveal exactly what happened to the original request. Two cases are possible:

1. **The request was lost before reaching the server.** The retry reaches the server and the request is processed once.
2. **The server processed the request, but its acknowledgement was lost.** The client retries because it does not know the request succeeded; the server may process it again.

> *A timeout tells the client that it did not hear back in time; it does not prove that the server never processed the request.*

**Idempotency** means that repeating the same operation does not repeat its effect. It is useful when a client may retry a request that the server has already processed.

A common approach is to attach a unique **idempotency key** to each logical request. The server records the key and uses it to recognize repeated attempts. A retry of the *same* operation must reuse its key; a genuinely new operation needs a different one.

In a WhatsApp-style messaging example, identifiers such as the conversation ID and user ID were considered. The proposed key combination was:

```text
timestamp + user ID + device ID

```

Including the device ID helps distinguish requests from different devices belonging to the same user.

**Key insight:** Idempotency prevents duplicate effects; it does not mean the network delivers a request exactly once.

**Key takeaway:** A retry may repeat a request the server already handled, so use a consistent idempotency key to prevent duplicate effects.

## Sharding a messaging system

**Sharding** splits data across database partitions. The **sharding key** affects how many shards an API must access. A good key keeps commonly accessed data together, limiting fan-out for important reads and writes.

The messaging APIs considered were:

- `SEND_MESSAGE`
- `GET_MESSAGES`
- `GET_RECENT_CONVERSATIONS`

The central trade-off was whether to shard message data by **conversation ID** or **user ID**.

### Sharding by conversation ID

Keeping a conversation’s messages on one shard makes conversation-oriented operations straightforward:

- `SEND_MESSAGE` can target one shard using the conversation ID.
- `GET_MESSAGES` can retrieve a conversation’s history from one shard.
- `GET_RECENT_CONVERSATIONS` starts from a user ID and may need to check all shards.

This layout is attractive when reading or writing messages by conversation is the priority, but it makes a user’s recent-conversation list harder to retrieve efficiently.

### Sharding by user ID

Sharding by user ID makes it easier to find conversations associated with a user. But a conversation can involve people whose data is on different shards, so sending a message may require multiple writes or broader fan-out.

For one-to-one conversations, the design considered storing message data for both participants. This duplicates data, but was treated as an acceptable storage trade-off for the query patterns being optimized.

Group conversations make the trade-off more pronounced:

- With **conversation-ID sharding**, a group’s message history stays together, but finding a user’s recent conversations may require work across shards.
- With **user-ID sharding**, group participants may be spread across many shards, so a message write can fan out to multiple locations.

### Separating message history from recent-conversation data

A proposed compromise used two tables with different sharding keys:

1. **Main message data**, sharded by conversation ID. This keeps a conversation’s messages together, so sending and retrieving history can target one shard.
2. **Recent-conversation data**, sharded by user ID. This organizes each user’s conversation summaries or latest-message details for efficient retrieval.

This improves locality for both message history and recent-conversation lists. The trade-off is more writes: sending a message requires writing the message and updating relevant participants’ recent-conversation records.

The additional or duplicated storage was estimated at roughly **6 TB**, with a rounded planning estimate of about **10 TB**. The rationale was that the extra storage was acceptable if it substantially improved important read and write paths.

> *Organize message history around conversations and recent-conversation lists around users: the two datasets serve different access patterns.*

**Key takeaway:** Choose a shard key around the query pattern you need to make efficient; if one key cannot serve both patterns well, consider separating the data.

## WebSocket delivery and notification services

A **WebSocket** is a persistent, two-way connection between a client and an application server. When the recipient is connected, the server can send a message over that connection instead of repeatedly polling the database.

The application server needs a way to map clients to their active connections—for example, a mapping from client IDs to WebSocket connections. A basic message flow is:

1. The sender sends a message to the server.
2. The server stores the message in the database.
3. The server uses the recipient’s connection mapping to deliver the message, if the recipient is connected.
4. The server responds to the sender.

A notification requirement does not automatically mean the system needs a queue. First consider what the existing server already knows and can do while handling the message-send request. It may be able to dispatch a notification directly. If the question does not ask you to design notification infrastructure, treat it as an existing service—a **black box**—and show how the application uses it.

For example:

```text
Sender → Application server → Database
                          → Notification service
                          → Response to sender

```

The notification service might handle push notifications. Its internal implementation need not be designed unless it is in scope.

**Key insight:** Start with the existing request flow. Don’t assume that database polling or a queue is necessary simply because a recipient needs a notification.

**Key takeaway:** Use an active WebSocket connection for direct delivery when available; model a notification service as an existing dependency unless its design is required.

## Synchronous work and the request path

A request may trigger several sub-operations. Classify each by whether the user-facing action is valid without it:

- **Must-have:** The operation is not correct or useful unless this work completes.
- **Good-to-have or deferrable:** The work matters, but can happen later without invalidating the user-facing result.

For sending a message, writing it to the database is must-have. The recipient needs to be able to retrieve the message; confirming success before it is stored could leave the sender believing a message was sent when the recipient cannot find it. Notifications and analytics are examples of work that may be deferred.

If the server waits for every follow-up task before responding, the request becomes slower and more dependent on downstream services. A practical flow is:

1. Complete the work required for correctness—for example, persist the message.
2. Return a response once that required work succeeds.
3. Perform deferrable work, such as notifications or analytics, later.

This principle also applies to placing an order. Saving the order details is essential before confirming that the order was placed. Other tasks may include reducing product quantity, checking delivery feasibility, sending an email or push notification, notifying a warehouse, contacting a logistics provider, updating analytics, and generating an invoice. Some of these may be required by a particular product design; others can happen later.

> *Keep the response’s critical path as short as correctness allows. Don’t make the user wait for work that can safely happen later.*

Whether work is synchronous or asynchronous concerns **when it happens relative to the response**. It does not, by itself, determine whether one operation depends on another. Likewise, classifying an operation as critical and deciding what the API should return when it fails are related but separate design questions.

**Watch out:** Moving work out of the request path reduces latency, but “record it for later” is not enough if the work must not be lost. Critical deferred work needs an appropriate mechanism for processing and failure recovery.

**Key takeaway:** Complete the work required to make the action valid before responding; defer other work when the requirements allow it.

## Queues and asynchronous event processing

A **message queue** can move delay-tolerant work out of a request’s response path. For example, after an order is saved, an order service can create an `OrderPlaced` event and put it on a messaging system. The API can respond without waiting for every downstream task.

```text
Order request
    |
    v
Save order to database
    |
    +----> Return OK response
    |
    v
Create and publish OrderPlaced event
    |
    v
Process follow-up work later

```

The queued event might lead to a confirmation email, a warehouse notification, or a logistics request. The event is the item being handed off; it is not necessarily the work itself, such as an SQL query.

A queue is a holding area for work that is waiting to be processed. This can help separate accepting a request from completing all its follow-up tasks, including during periods of higher traffic. It does **not** make the work disappear or automatically make it parallel: downstream services still need to process the events.

### Ordering and processing

**FIFO** means *first in, first out*: the earliest item added is the earliest item removed. An implementation may use operations and bookkeeping—such as indices in an array—to maintain that behavior.

However, ordering guarantees depend on the messaging system and its configuration. Not every queue provides ordering in every configuration; for example, SQS ordering requirements need an appropriate queue setup.

A queue’s delivery and processing model also matters. In a log-style persistent system, a consumer may track its position using an offset or pointer. Processing an event advances that position, but does not necessarily erase the record immediately. The record may remain until its configured **retention period** expires.

> *Think of a log-style consumer as moving a pointer through stored records—not necessarily deleting each record as soon as it reads it.*

Retention can support recovery or replay, but it is not an absolute guarantee against every kind of data loss. Guarantees depend on the system and its configuration.

**Key takeaway:** A queue decouples production of work from processing it; ordering, retention, and delivery guarantees depend on the specific system and setup.

## Publishers, subscribers, and topics

The **publisher–subscriber (Pub/Sub) model** separates the production of messages from their consumption:

- A **producer** or **publisher** creates and publishes messages.
- A **consumer** or **subscriber** receives or processes messages it is interested in.

The producer and consumer do not need to be the same application or run at the same time. For example, an order service can publish an `OrderPlaced` event while separate services handle email, warehouse, or logistics work.

> *The producer records what happened; interested consumers decide what to do about it.*

A **topic** is a named stream or category through which events are organized and made available to subscribers. It helps group and route events, but it is not necessarily the same thing as an event type:

- One topic can contain multiple event types.
- One event type can be published to multiple topics.
- Not every event type or service needs its own topic.

For example:

```text
Order placed events ──► Topic 1
                   └──► Topic 2

User login events  ──► Topic 1
                   └──► Topic 3

```

Different subscribers can respond independently to the events they receive. Being a consumer does not mean processing every possible event; services subscribe to the event traffic relevant to them.

The YouTube analogy captures the separation: publishing a video creates something subscribers may learn about, but each subscriber decides whether to watch it immediately, save it, or ignore it.

Kafka, RabbitMQ, and other messaging systems may use different terminology, while many of the underlying messaging patterns overlap. Focus first on the pattern and the problem it solves; product-specific details come afterward.

**Key insight:** A topic describes how events are grouped or routed; it does not, by itself, define an event’s type.

**Key takeaway:** Producers publish events, subscribers handle the events they care about, and topics organize event streams without necessarily mapping one-to-one to event types.

## Event payloads and downstream data access

An event should contain enough information for its consumers, but that does not always mean copying the entire database record into the message.

### Put a reference in the event

An event might contain only an `order_id`. A subscriber fetches the full order details when it needs them.

- **Benefit:** The message stays small.
- **Cost:** Multiple consumers may make repeated reads against the order database, increasing its load.

### Include needed data in the event

The event may include a subset of the data required by its consumers, or—in some designs—the full order data.

- **Benefit:** Consumers may not need to query the order database again.
- **Cost:** The message is larger and carries more data.

If many consumers need to read order details, read replicas are another possible way to serve those reads without directing all of them to the primary database.

For asynchronous audit logging, for example, the application could save an order synchronously and then publish an event containing the audit information. If the event contains all required audit details, the audit consumer need not fetch the order again. If it contains only an order reference, the consumer must retrieve the data before logging it.

**Watch out:** Including more data can improve performance, but it may also expose sensitive information more widely. Consider performance, privacy, and security requirements together.

**Key takeaway:** Choose an event payload—reference, subset, or full data—based on what consumers need and the cost and risk of additional data access.

## Failures, retries, and queue-based examples

Subscribers may call external services while processing an event. If a call fails, the system needs a policy appropriate to the importance of that work:

- Wait for the result when the workflow requires confirmation.
- Retry failures that may be temporary.
- If retries are exhausted, arrange for critical work to be handled again—for example, through a retry mechanism associated with that service.

For example, if processing an `OrderPlaced` event succeeds for some tasks but a logistics-provider call fails, the logistics work can be retried separately. A service-specific retry queue is one possible design. Another is to create a new logistics-related event for the relevant subscriber.

Not every follow-up needs the same guarantees. A delayed or missed push notification may not block the main operation if the message is already stored. A critical warehouse task may need stronger handling so it is eventually processed.

SQS and SNS were discussed in an analytics use case where data had been written directly to a database and the team wanted to reduce performance pressure and process data for multiple products. Messaging services can decouple producers from downstream processors and buffer work. They do not make a system literally failure-proof; ordering and other guarantees depend on the chosen service and configuration.

**Key insight:** Classify deferred work by business impact, then choose retry and recovery behavior accordingly.

**Key takeaway:** A queue can decouple processing, but critical work still needs an explicit plan for failures, retries, and any required ordering.

## Quick reference

- **Timeout:** Means no acknowledgement arrived in time; it does not prove the server did not process the request.
- **Idempotency:** Reuse the same key for retries of one logical operation; use a new key for a new operation.
- **Sharding:** Choose keys around important access patterns; conversation ID favors message history, user ID favors user-centric lists.
- **WebSockets:** Use active persistent connections for direct server-to-client delivery when available.
- **Request path:** Complete must-have work before a successful response; defer work that can safely happen later.
- **Queue:** Decouples event production from processing; it does not eliminate the downstream work.
- **Pub/Sub:** Producers publish; interested subscribers handle events; topics organize streams but need not map one-to-one to event types.
- **Event payload:** A reference reduces message size but may require extra reads; included data can reduce reads but raises payload and privacy considerations.
- **Failure handling:** Decide which work must succeed and how critical deferred tasks are retried or recovered.