# High-Level Design (HLD) — Session Notes

> Study notes covering data modeling recap, distributed systems, networking fundamentals, DNS, and load balancers.

## Session Overview

This block moved from data modeling basics into the opening ideas of high-level design (HLD).
The big themes were: primary keys and cardinality recap, why HLD is being started earlier, what distributed systems are, and why a single server breaks at scale.
It also introduced the first networking foundations for HLD: IP addresses, IPv4 vs IPv6, NAT, DNS, domain registrars, public static IPs, and load balancers.

## Data Modeling Recap and Course Sequencing

Data modeling was revisited briefly to anchor the transition into systems design. The main reminders were about naming conventions, keys, relationships, and cardinality.

Tables are generally named in plural and use snake_case. Columns are generally singular. A primary key must be unique, not null, and small in size; when appropriate, a surrogate unique identifier is preferred over a meaningful natural value. Attributes store facts about an entity, while relationships show how entities reference each other.

Cardinality was reviewed through examples:

- one-to-one
- one-to-many
- many-to-one
- many-to-many
The key teaching point was that relationship direction changes the label. For example, a student → batch relationship is many-to-one, while batch → student is one-to-many. The same logic showed up in the ticket/seat example: one booking can contain many seats, but each seat belongs to one booking.

**Key insight:** The same pair of tables can be described from either side; relationship direction changes the cardinality label.

The remaining data modeling topic to be covered later is the internal working of SQL, especially because it helps with query optimization and day-to-day practical understanding.

**Key takeaway:** Data modeling fundamentals were reviewed to close the loop before moving into HLD, and SQL internals were deferred rather than dropped.

## Feedback, Pacing, and Course Plan

A major discussion was about feedback and class pacing. Feedback was framed as something useful in both positive and negative form; it is the main channel for communicating concerns about difficulty, pacing, or depth.

The instructor’s point was that different learners experience the same topic differently. One person may find it too easy, while another finds it appropriately challenging or useful. So the exact number of classes is not the main issue — the real goal is making sure the topics are covered properly. Data modeling has sometimes taken 8 classes, other times 14; the number itself is flexible.

**Updated sequence:**

- Today: begin high-level design
- Next class: revisit the deferred data modeling / SQL-internals topic
- After 1–3 HLD sessions: return to finish the remaining deferred content

**Key insight:** The course is changing sequence, not reducing depth.

> **Watch out:** A temporary schedule change does not mean important material has been removed.

**Key takeaway:** Feedback is the mechanism for pacing the course without sacrificing important content.

## High-Level Design: Why One Server Breaks

High-Level Design (HLD) was introduced through a simple startup scenario: imagine building a B2C product like Flipkart from day zero. At first, it may seem fine to run everything on one machine, but as users grow, the setup breaks down.

A server here just means a remote machine you access directly or indirectly. It can be an application server, database server, Kafka server, or any other machine running a service. In the simplest setup, one machine may do everything, but that does not scale well.

As load grows:

- more requests hit the system
- the server slows down
- failures and crashes become more likely
A core concept introduced here was the bottleneck: the narrow part of a system that limits overall flow. The analogies used were a water bottle neck and a highway narrowing into one lane. Even if most of the system can handle more traffic, one restricted point throttles everything.

**Key insight:** Scaling one part of the system does not help if another component remains constrained.

Three problems with a single-server setup were emphasized:

- it cannot handle increasing load indefinitely
- it becomes a bottleneck
- it creates a single point of failure
If the only server fails, the whole app goes down.

> **Watch out:** “It worked for a few users” does not mean it will survive growth.

**Key takeaway:** HLD starts with recognizing how a single machine becomes both a performance limit and a reliability risk.

## Distributed Systems and the Move to Multiple Servers

Once a single server becomes a bottleneck, the natural next step is to scale out by adding multiple servers. The example used was simple: if one machine can handle about 1 million requests and the system needs to handle 10 million, you add 10 application servers.

But adding machines only helps if traffic is distributed correctly. That is the role of a load balancer.

A load balancer spreads incoming requests across available servers so that the load is not concentrated on one machine. The class also previewed the broader infrastructure stack that often appears in large systems:

- multiple application servers
- multiple database replicas/servers
- cache
- messaging queues like Kafka or RabbitMQ
- CDNs

**Key insight:** Distributed systems are not just “more servers”; they are multiple layers working together.

The distinction between LLD and HLD was sharpened here:

LLD is about how code is written and modeled, including design patterns and principles
HLD is about how different infrastructure layers cooperate at scale
The same physical laptop can act like different “servers” because different software and configuration make it behave differently. For example, a database behaves like a database because of the engine underneath it; in SQL systems, the InnoDB engine was mentioned as an example.

**Key takeaway:** Distributed systems require orchestration across layers, not just more hardware.

## What HLD Is and What It Is Not

High-level design is about choosing infrastructure layers for a requirement and understanding the trade-offs. It is not about memorizing a fixed solution.

For example, if you add a cache, the reason should be tied to a requirement like:

- faster reads
- query optimization
- reduced load on the database

**Key insight:** Every infrastructure component should exist for a reason tied to a requirement.

HLD interviews are not mainly recall tests. They are about decision-making:

- clarify the requirements
- consider multiple options
- compare pros and cons
- justify the final choice
The Ola example captured this well. A weak answer would be to jump straight to “Ola uses HBase, so I’ll choose HBase.” A stronger answer considers SQL, Cassandra, and HBase, compares them, and then picks the best fit based on the stated needs.

To improve HLD skill, the recommendation was to study more case studies and learn how experienced designers reason. A book that was explicitly recommended is:

- **An Insider's Guide to System Design Interviews by Alex Xu**
- Part 1: must-read
- Part 2: recommended, though harder
An architect was described as someone with broader exposure and stronger practical judgment than a typical senior engineer.

> **Watch out:** HLD is not about implementing infra tools from scratch in an interview; it is about understanding where and why to use them.

**Key takeaway:** HLD tests your reasoning, trade-off analysis, and system-level judgment.

## Distributed Systems Motivation: The Delicious Example

A distributed-system case study was introduced through Delicious, a bookmarking service founded in 2003 and later sold around 2008. The reason it was useful as a teaching example is that it solved a very real pain point.

Before cloud-synced tools were common, bookmarks lived on a local machine. If you used internet cafés or switched computers, your saved links did not follow you. You had to copy URLs into a notepad or write them down manually. That meant the data was machine-specific rather than user-specific.

**Key insight:** When user data is stored only on a local machine, it is not portable across devices or sessions.

Delicious solved this by storing bookmarks centrally so they could be accessed from anywhere. The basic product was intentionally simple:

a login screen
- a bookmarks screen with a Create Bookmark action
- a list of Your Bookmarks, each with a name and URL
The system’s value came from turning machine-bound state into centrally stored user state.

**Key takeaway:** A simple feature can become powerful when it makes personal data portable across machines.

## Basic APIs for the Bookmark Service

From the Delicious example, the backend interface was reduced to two essential APIs:

Create bookmark
Get bookmarks for a user
A minimal create API would need:

- `userId`
- `url`
- `name`

Example:

```text
createBookmark(userId, url, name)
getBookmarks(userId)
```

The retrieval API would return all bookmarks for a user:

The scope was intentionally kept simple:

- one bookmark at a time
- no bulk creation
- no third-party API discussion
- login/session APIs were not expanded here

**Key insight:** Even a tiny API surface can support a valuable product if it solves a real user problem.

**Key takeaway:** The core bookmark service only needs create and retrieve operations to deliver the central value.

## IP Addresses, Internet Reachability, and Why a Laptop Alone Is Not Enough

The discussion then shifted into networking fundamentals. A remote user cannot directly access an app running on your laptop just because both devices are on the internet. Connectivity alone is not enough; the machine has to be reachable through a proper network address and exposure path.

An IP address was introduced as the machine’s internet location, similar to how latitude and longitude identify places on Earth. That is how a request for a site like google.com reaches the correct server rather than “broadcasting” to everyone.

The internet depends on unique addressing, not random probing of all machines.

**Key takeaway:** Reachability on the internet requires a uniquely addressable machine, not just an online device.

## IPv4 and IPv6

IPv4 was explained as a 32-bit addressing scheme written in the form A.B.C.D, where each part ranges from 0 to 255. Since each of the four numbers is 8 bits, IPv4 supports about 2^32 addresses — roughly 4 billion.

That turned out to be too small for the modern internet, since there are billions of people and many internet-connected devices per person. That is why IPv6 exists.

- **IPv4:** 32 bits
- **IPv6:** 128 bits
The move to 128 bits creates an astronomically larger address space, enough for huge numbers of devices.

**Key insight:** IPv6 exists because IPv4 address space was not enough.

IPv4 still remains widely used because many older systems still depend on it.

**Key takeaway:** IPv4 ran out of room; IPv6 massively expands the number of available addresses.

## NAT, Public vs Private IPs, and Dynamic Allocation

NAT (Network Address Translation) was introduced to explain how many users can share fewer public IP addresses.

The motivation is cost and scarcity:

public IPs are limited
not every device needs a unique public IP all the time
an ISP can conserve addresses by sharing them across many users
The Airtel example captured this: if there are 100 customers but only 4 active at a time, the ISP may buy only 4 public IP addresses and use NAT to serve many customers through them.

The important distinction is:

public IP: visible on the internet
private IP: used inside the local/internal network
NAT creates an internal network where many devices can reuse private addresses, while the NAT device itself faces the public internet.

IP addresses are managed through allocation systems such as ICANN and then distributed through ISPs. End users do not directly “claim” public IPs for their laptops. The IP you use may also be dynamic: you may disconnect and reconnect and receive a different one later.

**Key insight:** IP addresses are often assigned dynamically, not permanently owned by the device.

A user asked whether a laptop gets the same IP every time. The answer was no: if the laptop disconnects and reconnects, it may receive a different address.

> **Watch out:** Do not treat an IP address as a permanent device identity.

**Key takeaway:** NAT lets many devices share limited public IPs, and both public and private IPs may change over time.

## Client-Server Architecture, Geolocation, and Static IPs

Because IP addresses are often dynamic, the class connected this to client-server architecture. In a standard client-server model:

- the client initiates the request
- the server responds
- the server does not casually start a conversation with the client first
This matters because if a client’s address changes frequently, a server cannot reliably “reach back” to it later without an ongoing connection mechanism. That is part of why tools like WebSockets matter.

The session also noted that IP-based geolocation is usually approximate, not exact. Because IP ranges are often allocated regionally by ISPs, an IP may map to a nearby area rather than a precise location.

For machines that must remain publicly reachable, the solution discussed was a public static IP address. This is useful for production servers or any service that needs a stable endpoint. Such IPs can be obtained through an ISP or via an allocation path tied to IP management. They can be expensive; the rough price estimate mentioned was around $4,000/month historically.

**Key insight:** A stable public endpoint is essential for reliable hosting, but static IPs can be costly.

**Key takeaway:** Dynamic IPs complicate client reachability, while static public IPs provide stable access for public services.

## DNS, Domain Registrars, and Making a Website Reachable

Once a stable IP exists, DNS (Domain Name System) connects a human-friendly name to that IP. DNS translates a domain name like www.google.com into the machine’s IP address.

Humans are poor at remembering numbers, so we use names. DNS makes web access friendly and usable.

Domain names are managed through registrars such as:

- GoDaddy
- Namecheap
For a public app like Delicious, the basic setup was:

- buy a public static IP address
- buy a domain name
- register the IP with the domain via a domain registrar
- configure DNS
- users can access the app through the URL

**Key insight:** A public website needs a stable IP, a registered domain, and DNS pointing the two together.

**Key takeaway:** DNS is the name-to-IP bridge that makes human-friendly web access possible.

## Why a Publicly Reachable App Can Still Go Down

Even after a website is publicly accessible, it can still fail. The session identified several failure modes:

- hardware failure
- too many requests causing overload
- performance issues such as memory leaks or other resource problems
Some of these are unexpected, like machine failure. Others are developer-induced, like a leak that degrades the server over time.

**Key insight:** Being reachable is not the same as being reliable.

**Key takeaway:** Deployment and availability are different problems; a public endpoint can still crash under load or hardware failure.

## Load Balancer: Why It Exists and How It Fits with DNS

The final major topic was the load balancer.

The example began with a single application server that has to be restarted for deployment. During deploy, the app stops briefly, which creates downtime and a single point of failure. To avoid that, multiple application servers are used.

Now the new question is: if the app is behind multiple servers, how does traffic reach the right one?

DNS helps get the user to the service entry point, but DNS alone does not decide which backend server handles the request. That is the job of the load balancer.

**Request flow:**

- user enters the domain name
- DNS resolves it to an IP
- that IP is actually the load balancer’s IP
- the load balancer receives the request
- it selects a backend server
- the chosen server processes the request
- the response returns to the user

**Key insight:** The load balancer is the traffic director; users do not talk directly to a specific backend server.

The next things to understand about load balancers were explicitly identified as:

how the load balancer knows about application servers
how it knows a server is unavailable
how it routes requests when all servers are healthy

**Key takeaway:** DNS gets you to the service, and the load balancer chooses the backend server that actually serves the request.

## Quick Reference

### Data modeling basics

Tables: plural, snake_case
Columns: singular
Primary key: unique, not null, small, preferably surrogate when appropriate
Cardinality: one-to-one, one-to-many, many-to-one, many-to-many
Relationship direction matters
### HLD vs LLD

LLD: internal code structure, classes, patterns
HLD: how system layers work together at scale
### HLD mindset

Start from requirements
Compare alternatives
State trade-offs
Don’t memorize company stacks; reason through them
### Distributed systems

Work is spread across multiple machines
Add servers only helps if traffic is properly distributed
### Load balancer

Routes requests to one of many backend servers
Front door may be the load balancer’s IP, not an app server IP
### Networking basics

- IPv4 = 32-bit, about 2^32 addresses
- IPv6 = 128-bit, about 2^128 addresses
- NAT lets many devices share fewer public IPs
- Public IP = internet-facing
- Private IP = internal/local
- IPs can be dynamic
### DNS and domains

- DNS maps domain names to IPs
- Domain registrars: GoDaddy, Namecheap
- Public app setup: static IP + domain + DNS
### Reliability

- Single server = bottleneck + single point of failure
Publicly reachable does not mean reliable
- Hardware failure, overload, and memory leaks can still bring systems down
