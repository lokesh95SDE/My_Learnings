This guide covers a structured high-level design (HLD) interview process, then applies it to a WhatsApp-style messaging system.\
It walks through requirements, scale and storage estimates, APIs and data modeling, and message delivery using polling, long polling, and WebSockets.

## 1. A structured HLD interview process

A useful HLD discussion moves from understanding the problem to exploring one part of the design in depth:

1. **Understand the problem.** If the prompt is unclear, ask for clarification. Otherwise, restate your understanding and confirm it.
2. **Define requirements.**
   - **Functional requirements** describe what the system must do. Focus on the core features and define a minimal viable product (MVP).
   - **Non-functional requirements** describe qualities such as consistency, availability, latency, and reliability. Decide which matter most for this particular system.
3. **Estimate scale** with explicit, back-of-the-envelope assumptions.
4. **Identify the major APIs** implied by the requirements.
5. **Draw the high-level architecture**, explaining how it supports the requirements.
6. **Deep-dive into a component** and discuss its design in more detail.

> *Build the design step by step from the requirements instead of presenting a memorized design all at once.*

**Key takeaway:** Align on the problem and requirements before estimating scale, listing APIs, or drawing architecture.

## 2. Messaging requirements and scope

The messaging MVP discussed supports **one-to-one text chats**, with message order and timestamps preserved. For this design, **consistency** means that messages should reach the recipient and retain their order and timestamps.

Consistency needs to be defined in context: its meaning can differ across systems. Clarify what it requires before weighing it against availability or latency. Reliability may also matter, depending on the requirements.

Keep later design decisions tied to the agreed scope. Editing messages and group messaging were not established as MVP requirements, so APIs and design work for those features should not be added unless the requirements change. Group conversations appear in a later data-model example as a way to generalize participant representation; they are not part of the one-to-one MVP.

**Key insight:** “Consistency” is not a complete requirement by itself. State what users must observe—in this case, delivery, order, and timestamps.

**Key takeaway:** Lock the MVP and define what important non-functional requirements mean before designing the system.

## 3. Back-of-the-envelope scale estimation

Scale estimates are assumptions, not facts you are expected to know exactly. Start from the user base, then estimate how often users create or use the system’s main entity. That gives your traffic estimate a clear basis.

- Messaging system: messages per active user per day
- Booking system: bookings per user per day
- Ticketing service: tickets per user per day

The main entity matters because it drives estimates of storage, read/write workload, and traffic.

> *Start from the user base and the system’s main entity; don’t invent a large traffic number without explaining where it comes from.*

### Worked example: messages per day

Assume:

- **1 billion MAU** — monthly active users
- **50% of MAU are DAU** — daily active users
- **20 messages per DAU per day**

Then:

```text
1 billion MAU × 50% = 500 million DAU

500 million DAU × 20 messages/user/day
= 10 billion messages/day

```

These are illustrative assumptions, not fixed facts. You could choose a different plausible number of messages per user per day, provided you explain the assumption and use it consistently. Keep user counts within realistic bounds; for example, a global user estimate cannot exceed the world’s population.

### Average and peak throughput

Convert daily traffic into average throughput by dividing by the number of seconds in a day:

```text
10 billion messages/day ÷ 86,400 seconds/day
≈ 115,700 messages/second
≈ 100,000 messages/second (10^5)

```

Round to an order of magnitude rather than spending time on false precision. Then estimate peak load separately. Using a working peak multiplier of **5–10× average**:

```text
100,000 × 5 = 500,000 messages/second
100,000 × 10 = 1,000,000 messages/second

```

**Key insight:** State average and peak separately. Peak traffic helps you reason about the capacity the system may need at its busiest.

### Keeping estimation useful

Estimation should support the rest of the design, not take it over. Keep it to roughly **2–3 minutes**:

- State assumptions clearly and keep them plausible.
- Round calculations rather than seeking exactness.
- Explain how your estimates follow from user behavior.
- Adjust if the interviewer offers a hint or a different assumption.

**Key takeaway:** Choose defensible assumptions, calculate an order of magnitude, and move on to the design.

## 4. Message storage and workload estimates

### Storage per message

First define what a stored message contains. A rough record might include:

- Message ID
- Timestamp
- Conversation ID
- Sender user ID
- Receiver user ID
- Message content

For a simple estimate, assume the fixed-size fields and content total about **100 bytes per message**. One way to reach that estimate is to use roughly 8 bytes for IDs and timestamps and about 50 bytes for the average message content. A 16-byte UUID still leaves the total close enough to round to 100 bytes.

The content-length assumption is a judgment call. An average of 50 characters was chosen as a reasonable rough estimate for this exercise; another value can work if justified.

### Daily and five-year storage

Using 10 billion messages per day and 100 bytes per message:

```text
10^10 messages/day × 10^2 bytes/message
= 10^12 bytes/day
≈ 1 TB/day

```

This is a raw message-data estimate; it does **not** include indexes or replicas.

At that rate, five years of retention is approximately:

```text
365 days/year × 1 TB/day = 365 TB/year
≈ 400 TB/year

5 years × 400 TB/year = 2,000 TB
≈ 2 PB

```

A volume around 2 PB cannot reasonably fit on one database disk, so the data must be distributed across multiple storage units. That leads to the need for **sharding**.

### Decimal and binary units

For quick estimates, decimal units use powers of 10:

- 1 KB = 10³ bytes
- 1 MB = 10³ KB
- 1 GB = 10³ MB
- 1 TB = 10³ GB
- 1 PB = 10³ TB

Binary units use powers of 2: for example, **1 KiB = 1,024 bytes** and **1 TiB = 2⁴⁰ bytes**, or about 1.10 TB. Precise binary names include KiB, MiB, GiB, and TiB.

**Watch out:** A decimal TB is not exactly a TiB. State which convention you are using and keep the precision realistic.

### Read-heavy or write-heavy?

Do not classify a messaging system as write-heavy just because users send messages. Each message is written so someone can read it, and users may read a message once, several times, or not at all.

A rough starting assumption is that each message is read about once on average. Under that assumption, reads and writes are **roughly balanced**. The real ratio depends on user behavior and the product. Caching recent messages can affect where reads are served, but it does not by itself determine the overall read-to-write ratio.

**Key takeaway:** Estimate storage from the message record and volume; estimate read/write balance from user behavior rather than from writes alone.

## 5. APIs and conversation data

Derive the major APIs from the agreed requirements; this is not the point to specify every parameter or produce a complete REST design.

The core messaging operations discussed are:

- **Get recent conversations** for the logged-in user. This powers the initial conversation list, which can show each other person’s profile picture, name, and latest chat message.
- **Get messages** for a selected conversation.
- **Send a message.**
- **Create a conversation.**

Login, registration, and logout APIs may also exist, but they are separate from the core messaging operations and can often be treated as standard functionality.

### Paginate message history

A conversation may contain a large number of messages, so return history in chunks rather than in a single response. The get-messages API should identify the conversation and support pagination using a **limit** and an **offset** (or page number).

For example, with a limit of 100 and an offset of 1,200, a SQL-style query returns the next 100 records:

```sql
LIMIT 100 OFFSET 1200

```

Assuming records are numbered from 1, that corresponds to records 1,201–1,300.

A send-message request needs, at minimum, the conversation ID, sender user ID, and message content. A conversation must be created before messages can refer to its ID.

### Representing participants

A conversation-participant relationship can associate multiple users with a conversation ID:

| **conversation_id** | **user_id** |
| :------------------ | :---------- |
| 1                   | 101         |
| 1                   | 108         |
| 1                   | 110         |
| 1                   | 120         |

This representation can support multiple participants without changing the basic relationship. In the case study, group chats were not part of the MVP; the example simply illustrates how participants can be represented.

**Watch out:** Don’t expand the API list with editing or group-chat features unless the requirements explicitly add them.

**Key takeaway:** Requirements determine the APIs; use conversation IDs and pagination to retrieve message history in manageable chunks.

## 6. Message delivery: polling, long polling, and WebSockets

In a basic client–server design, the sender sends a message to the server, the server stores it, and the message is then delivered to the recipient. Persisting before treating a message as delivered helps avoid telling the sender the message was accepted before it has been safely stored.

Ordinary HTTP request–response communication is initiated by the client: the client requests something, and the server responds. For a messaging system, that means the server needs a way to reach a recipient who has not just asked for a message.

### Short polling

With **short polling**, the recipient’s client repeatedly asks the server whether a message is available. If there is none, the server replies that there is nothing to deliver; the client waits briefly and asks again.

This can waste resources on empty requests, and delivery may be delayed until the next poll.

### Long polling

With **long polling**, the client sends a request and the server keeps it open while waiting for a message. When a message arrives—or the request times out—the server responds, and the client immediately sends another long-poll request.

Long polling can reduce repeated empty responses and improve responsiveness compared with short polling. But requests are still renewed repeatedly, and many may remain open while clients wait.

### WebSockets

A **WebSocket** provides a persistent, bidirectional channel between a client and server. The connection is typically initiated through an HTTP(S) request that negotiates an upgrade to the WebSocket protocol. Once the channel is established, either side can send messages over it.

For messaging, the recipient’s client opens a WebSocket connection when the user comes online. The server maintains a mapping from the user ID to the active connection:

```text
User ID -> WebSocket connection

```

A simplified flow is:

```text
Sender
  -> Server receives message
  -> Message is written to the database cluster
  -> Server looks up the recipient's connection
  -> Server sends the message over that WebSocket

```

The server can send to the recipient because it has an established connection to that client. Unlike polling, it does not have to wait for the client to ask again.

WebSockets avoid repeated requests for each message, but the server must maintain many concurrent connections, which can require substantial server-side memory. Connections can also fail; health checks or heartbeats help detect a lost connection. When the client reconnects, the server updates the user-to-connection mapping.

> *Long polling renews requests as it waits; WebSockets keep a bidirectional channel open for ongoing communication.*

**Key insight:** There is no perfect delivery mechanism. Polling, long polling, and WebSockets make different trade-offs in responsiveness, request overhead, and server resources.

**Key takeaway:** Use a persistent connection for timely server-to-client delivery, and account for the cost of maintaining many active connections.

## 7. Offline recipients and reliability

If the recipient is offline, there is no active WebSocket for immediate delivery. The system needs to retain pending messages so they can be delivered when the recipient returns. A **30-day retention policy** was discussed as an example.

When the recipient comes online, the client opens a new connection and asks whether there are pending messages. The server sends them over the WebSocket; new messages can then be delivered through the same connection.

For an end-to-end encrypted design, stored message payloads remain encrypted. Encryption protects message privacy, but the system still needs a way to retain and deliver pending messages.

**Key takeaway:** Real-time delivery handles connected recipients; retained pending messages cover recipients who are offline.

## Quick reference

- **HLD sequence:** Understand the problem → define requirements → estimate scale → identify APIs → draw architecture → deep-dive.
- **Estimate traffic:** Users × core entity actions per user → daily volume → divide by 86,400 for average per second → apply a peak multiplier.
- **Example scale:** 1B MAU × 50% DAU × 20 messages/day = 10B messages/day ≈ 100K messages/second average; a 5× peak assumption gives 500K/second.
- **Example storage:** 100 bytes/message × 10B messages/day ≈ 1 TB/day; five years at roughly 400 TB/year ≈ 2 PB.
- **Core messaging APIs:** Get recent conversations, get messages, send message, create conversation.
- **History retrieval:** Identify the conversation and paginate with a limit and offset.
- **Delivery choices:** Short polling repeatedly checks; long polling holds a request open; WebSockets maintain a bidirectional channel.
- **Offline delivery:** Retain pending messages and deliver them when the recipient reconnects.