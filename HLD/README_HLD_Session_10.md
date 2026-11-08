# Session Overview

This guide covers messaging-system design: scale estimation, APIs, real-time delivery, retries and idempotency, and sharding trade-offs.\
It also includes practical job-search advice and guidance on preparing for senior system-design interviews.

## Messaging-system requirements, APIs, and scale

Start with the system’s main user actions, then use them to shape both the APIs and the data model.

### Functional requirements and APIs

A WhatsApp-style messaging system needs operations for:

- Getting a user’s recent conversations.
- Getting messages for a conversation, using a **conversation ID** and pagination parameters.
- Sending a message with a conversation ID, user ID, and message content.
- Creating a conversation.

**Pagination** breaks a large result set into manageable chunks. One familiar approach is SQL’s `LIMIT` and `OFFSET`; the important idea is to return only part of a potentially large result at a time.

### Scale estimation

In an interview, aim to reach a useful order-of-magnitude estimate in roughly **2–3 minutes**. Make defensible assumptions rather than spending too long trying to calculate exact figures.

A typical walkthrough starts with metrics such as **MAU** (monthly active users) and **DAU** (daily active users), then estimates messages per user per day. That estimate can inform:

- **Daily storage**: multiply message volume by message size, then convert to larger units such as terabytes or petabytes.
- **Sharding needs**: estimate how much data the system will need to distribute.
- **Read/write balance**: decide whether the workload is relatively read-heavy or write-heavy, and approximate the ratio.
- **Request rates**: estimate the volume of operations the system must serve.

> *The purpose of estimation is to make reasonable assumptions and reach a useful scale—not to claim precise capacity figures.*

**Key takeaway:** Define the important user actions first; estimate their scale with clear assumptions and focus on order of magnitude.

## Delivering messages to connected users

The system needs a way to deliver a new message to a user who is already connected. Three common approaches differ in how quickly they deliver updates and how much ongoing work they require.

- **Polling:** The client repeatedly asks the server whether new messages are available. This can waste resources when there is nothing new, and updates may be delayed until the next request.
- **Long polling:** The client makes a request that the server holds open until a message is available or the request times out. This can deliver updates sooner than ordinary polling, but many open requests can consume server resources, including memory.
- **WebSockets:** The client and server establish a persistent, bidirectional connection. The server can then send messages over that connection without waiting for the client to ask again.

For messaging, the server can maintain a mapping from a **user ID** to that user’s active WebSocket connection ID. A persistent connection uses server resources, and a disconnected client may need to reconnect when it comes back online.

> *Polling repeatedly checks for updates; long polling keeps a request open while waiting; WebSockets keep a bidirectional connection available for ongoing communication.*

**Key takeaway:** Use the delivery approach that fits the system’s latency and resource needs; WebSockets enable ongoing server-to-client delivery over an established connection.

## Reliable communication: acknowledgements, timeouts, and retries

A smooth user experience does not mean the underlying network is uninterrupted. Connections can fail, messages can be delayed, and servers can be unavailable. The same need for resilience applies to messaging, video calls, and financial operations: a seemingly simple action may depend on communication that is not perfectly reliable.

### Acknowledgement and response are different

In the simplified model used here, the server first sends an **acknowledgement** to confirm it received the request. It then processes the request and sends a **response** containing the result.

```text
Client                         Server
  |                               |
  | -------- request ----------> |
  | <----- acknowledgement ----- |
  |                               | process request
  | <--------- response -------- |

```

An acknowledgement is an early signal of receipt; it is not necessarily the final result. This is similar to receiving a receipt after making a deposit or enrolling in a policy: the receipt confirms the request was received, even if the outcome comes later.

### Timeouts and retries

A **timeout** is how long the client waits for an expected signal. If the client receives no acknowledgement before the timeout, it may **retry** by sending the request again.

But a timeout does **not** prove that the request was lost. It proves only that the client did not receive confirmation in time.

#### Case 1: The original request is lost

1. The client sends a request, but it never reaches the server.
2. No acknowledgement arrives, so the client waits until the timeout.
3. The client retries.
4. The retry reaches the server, which acknowledges and processes it.

In this case, the server receives only the retry.

#### Case 2: The acknowledgement is lost

1. The request reaches the server.
2. The server sends an acknowledgement, but it is lost.
3. The client receives no confirmation and retries after the timeout.
4. The retry may reach the server too, so the server may receive the same request more than once.

> *Retries help communication recover, but a lost acknowledgement can make the client retry a request that the server has already received.*

**Key takeaway:** A timeout tells the client that it did not get confirmation; it does not tell the client whether the server acted on the original request.

## Idempotency and duplicate-request handling

A retry can cause a request to arrive more than once. For example, a client sends “Hi,” the server receives it, but the acknowledgement is lost. The client retries, and the server may receive “Hi” again.

**Idempotency** means that repeating the same logical request does not repeat its effect. In practice, the server needs a way to recognize that a request is a retry and avoid applying its effect again.

### Use a request identifier, not message content

Identical content does not prove that two requests are duplicates. A person may intentionally send “Are you there?” twice, or send “Hi” from both a phone and a laptop.

The identifier should identify the **logical request**, not just its contents:

1. The client creates an identifier for the request.
2. The client sends it with the request.
3. If it retries, it sends the **same identifier** again.
4. The server uses the identifier to recognize a request it has already handled.

A server-generated database ID created only after the request arrives cannot identify a retry that happens before the server has processed it. A **client-generated UUID** can work as an idempotency key if it is unique for each logical request and reused across retries. Client-generated IDs are not inherently unreliable; the key is whether their uniqueness is strong enough for the system.

A timestamp/user/device combination was also considered as a possible key. Such a combination must be tested against collisions and the system’s clock assumptions. In particular, a retry must reuse the original key: generating a fresh timestamp for each network attempt could make a retry appear to be a new request.

### Why common attributes are not enough on their own

- **Message content:** different intentional messages can have identical text.
- **User ID:** does not distinguish two requests from the same user on different devices.
- **Conversation ID:** identifies a conversation, not one particular request.
- **Timestamp:** two distinct requests can share a timestamp, and client clocks can differ.
- **A hash:** produces the same output for the same input. It does not solve the identity problem if the chosen inputs fail to distinguish separate requests.

A deduplication design should be tested against cases such as different users sending the same text, the same user sending the same text in different conversations, and the same user sending from multiple devices. The design must distinguish separate intentional requests while keeping a retry’s key unchanged.

> *Idempotency prevents repeated effects; it does not guarantee that a message is physically delivered only once.*

**Key takeaway:** Generate one idempotency key per logical operation and reuse it on every retry; do not use message content alone to identify duplicates.

## Sharding by access pattern

A **sharding key** determines how records are distributed across shards. Choose it by examining the system’s APIs and asking which candidate key best supports the important access patterns.

### A practical selection framework

1. List the relevant APIs.
2. Identify which attributes each API uses to find its data.
3. Compare candidate keys by how many shards each API would need to access.
4. If traffic volumes are known, prioritize the APIs carrying the most load—not merely the number of APIs a key helps.
5. If traffic is unknown, the number of APIs optimized can serve as a rough guide.

A key that makes one operation efficient can make another expensive. For example, optimizing one API that handles 99% of traffic may matter more than optimizing several low-traffic APIs.

Not every field in a message record is a good sharding key. For the APIs discussed, **user ID** and **conversation ID** are plausible candidates; message ID, timestamp, and message content do not naturally group the data those operations need.

### Conversation-ID sharding

If messages are sharded by **conversation ID**, all messages in a conversation are stored together.

- **Send a message:** route to the conversation’s shard.
- **Get messages for a conversation:** read from that conversation’s shard.
- **Get a user’s recent conversations:** may need to search multiple shards, because the user’s conversations can be distributed across them.

“Get messages for a conversation” means fetching the full chat history for the conversation, including messages from all participants—not only messages sent by one particular user.

### User-ID sharding

If data is sharded by **user ID**, records associated with a user are routed according to that user’s key. This does not guarantee that a conversation between two users is stored together.

One proposed approach stores a message for both participants, so each participant’s shard contains the messages from their conversations. This makes the user’s own history more accessible, but it can mean writing the same message to multiple user shards. A group message may need to be available for every participant, making a send operation span multiple shards.

Another consequence is that loading a conversation can be difficult if its data is distributed across the participant shards. Fetching the same conversation from both participants’ shards is unnecessary if one already contains the complete history, but a design that distributes message data across users must still account for where all the messages live.

### One-on-one versus group chat

For one-on-one chat, user-ID sharding can be a reasonable choice when the goal is to keep a user’s conversations together. But it does not guarantee that the full conversation is on one shard.

Group chat makes the trade-off clearer:

| **Sharding key**    | **Send a message**                      | **Get messages for a conversation**   | **Get a user’s recent conversations** |
| :------------------ | :-------------------------------------- | :------------------------------------ | :------------------------------------ |
| **Conversation ID** | One shard                               | One shard                             | May require all shards                |
| **User ID**         | May require multiple participant shards | May require data from multiple shards | One user-oriented shard               |

Conversation-ID sharding keeps a group’s messages together, but a user’s different conversations may be spread across shards. User-ID sharding can keep a user’s conversation history together, but group sends may require updates across many participant shards, and a group conversation’s messages may be distributed.

**Key takeaway:** A good sharding key is not simply the one that fits the data model; it is the one that best serves the system’s important access patterns and traffic.

## Separate message data from recent-conversation data

Messages and recent-conversation lists serve different access patterns, so they can be stored as separate datasets with different sharding keys.

### Messages by conversation ID

Store message history by **conversation ID**. This keeps messages for a conversation together:

- **Get messages:** one-shard read.
- **Write a message:** write to the shard for that conversation.

### Recent conversations by user ID

Maintain a separate **Recent Conversations** dataset, sharded by **user ID**. For each user, store the conversations they participate in and the latest message in each. This gives the user’s recent-conversation view a user-oriented layout:

- **Get recent conversations:** read the user’s data from one shard.
- **Send a message:** update the message shard and update recent-conversation records for the participants. In a group, those user records may be spread across several shards.

The design intentionally maintains additional recent-message information so that it does not have to search the much larger message dataset to assemble a user’s recent-conversations list.

### Approximate storage comparison

The estimate assumes roughly:

- **100 conversations per user**
- **8 bytes** per conversation ID
- **50 bytes** for the latest message in each conversation

For one user:

```text
100 × (8 bytes + 50 bytes)
= 5,800 bytes
≈ 6 KB

```

For **1 billion users**, that is roughly **6 TB**, rounded up to about **10 TB**. If a shard holds around 1–2 TB, the recent-conversations dataset might fit in roughly **5–10 shards**.

By comparison, the message dataset was estimated at around **2 PB**, or roughly **1,000–2,000 shards** at 1–2 TB per shard.

> *“All shards” is not equally expensive for every dataset. Searching 5–10 shards is a much smaller fan-out than searching 1,000–2,000.*

This design accepts extra writes and some duplicated information to make the two main read paths efficient:

- **Get messages:** use the conversation-ID-sharded dataset.
- **Get recent conversations:** use the user-ID-sharded dataset.

Idempotency and storage duplication are separate concerns. Idempotency prevents a duplicate request from producing duplicate effects; sharding determines where intentional copies of data are stored.

**Key takeaway:** Store message history by conversation ID and maintain a separate user-ID-sharded recent-conversations view when both reads need to be efficient.

## Job search and senior interview preparation

### Keep applying while preparing

Rather than focusing only on one target company, continue applying to suitable roles and prepare as though an interview could come at any time. The aim is to be ready without needing a long preparation period after an interview opportunity appears.

Keep your **resume** clear and tailored to the roles you want. A review can help identify problems that might prevent it from getting through an initial screen. Treat **LinkedIn** as a digital resume and keep it current; consider using its job-search settings if they fit your situation.

### Use multiple channels

- Apply to relevant openings through **company career portals**.
- Ask for **referrals** through current and former colleagues, alumni, and relevant communities.
- Use **LinkedIn** to find recruiters or employees at companies of interest.
- Look for active **job platforms** in your market.

For LinkedIn outreach, focus on one company for a few days, find relevant contacts, and send a brief introduction—one or two lines—explaining your interest. Include a resume link and, if available, the job posting or ID; otherwise, ask whether there is a suitable opening. Recruiters and people earlier in their careers may be more likely to respond than very senior engineers, who often receive many requests and have limited time.

Many messages will go unanswered. Treat outreach as one channel among several and keep applying rather than treating silence as a verdict on your qualifications.

### Targeting senior roles

For someone with 12 years of experience, the suggested target was **SD3 or higher**, while recognizing that level names differ by company. In some organizations, this may correspond to principal-level roles; the mapping is not universal.

Senior system-design interviews may expect you to reason across multiple systems, not only describe the systems you have personally built. If your work experience has been narrow:

- Read about other systems and their architectural choices.
- Talk with colleagues or friends who work on different systems.
- Broaden your understanding of why systems are designed in particular ways.
- Explain your own experience clearly, distinguishing what you built firsthand from what you have studied or learned through discussion.

**Key takeaway:** Keep multiple job-search channels active, and for senior roles, prepare to demonstrate architectural reasoning beyond a single system.

## Quick reference

- **Estimate quickly:** Aim for a defensible order of magnitude in about 2–3 minutes.
- **Polling:** Repeated requests; can waste resources and delay updates.
- **Long polling:** Holds a request open; prompt, but many open requests consume resources.
- **WebSockets:** Persistent, bidirectional communication; the server can send updates over the established connection.
- **Timeout:** Means confirmation did not arrive in time—not that the server failed to act.
- **Retry:** Reuses the same **idempotency key** for the same logical operation.
- **Sharding:** Choose keys by API access patterns and, when known, traffic volume.
- **Conversation ID:** Keeps a conversation’s messages together.
- **User ID:** Groups user-oriented data, but does not automatically colocate a group conversation.
- **Recent-conversations design:** Messages by conversation ID; recent-conversation records by user ID.
- **Job search:** Keep applying through several channels while preparing for interviews.
