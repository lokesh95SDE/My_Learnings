# Database Normalization — Session Notes

> A revision session covering database fundamentals, normalization theory (1NF, 2NF),
> anomalies, and the practical trade-offs of applying it.

---

## 📌 Table of Contents

- [Database Basics Refresher](#-database-basics-refresher)
- [Why Normalization Exists](#-why-normalization-exists)
- [Redundancy, Consistency, and Why It Matters](#-redundancy-consistency-and-why-it-matters)
- [Dependency and the Student Enrollment Example](#-dependency-and-the-student-enrollment-example)
- [First Normal Form (1NF)](#-first-normal-form-1nf)
- [Why Blindly Applying 1NF Can Be a Bad Idea](#-why-blindly-applying-1nf-can-be-a-bad-idea)
- [Concurrency Problems with Aggregated Lists](#-concurrency-problems-with-aggregated-lists)
- [When Normalization Fits and When It Doesn't](#-when-normalization-fits-and-when-it-doesnt)
- [Anomalies: What Goes Wrong When Normalization Is Poor](#-anomalies-what-goes-wrong-when-normalization-is-poor)
- [Second Normal Form (2NF)](#-second-normal-form-2nf)
- [Normalized Table Design](#-normalized-table-design)
- [Cross-Database Consistency and Practical Constraints](#-cross-database-consistency-and-practical-constraints)
- [Quick Reference](#-quick-reference)

---

## 🗄️ Database Basics Refresher

Core relational concepts that underpin the normalization discussion.

### Attributes by Type

| Type | Description |
|------|-------------|
| Simple attribute | A single, indivisible value |
| Composite attribute | Composed of smaller parts (e.g., full name → first + last) |
| Single-valued attribute | Holds exactly one value |
| Multi-valued attribute | Can hold multiple values |
| Derived attribute | Computed from other attributes |

### Key Vocabulary

- **Key attribute** — uniquely identifies an entity
- **Candidate key** — any minimal set of attributes that can be a primary key
- **Primary key** — the chosen candidate key (ideally an integer in many designs)
- **Foreign key** — references the primary key of another table
- **Super key** — any set of attributes that uniquely identifies a row

### Other Recalled Topics

- **Soft delete vs hard delete** — especially important in privacy-sensitive systems (e.g., payment platforms)
- **Joins** — inner join and outer join

> **Key takeaway:** Tables, keys, and relationships must be understood clearly
> before you can reason about redundancy.

---

## 🎯 Why Normalization Exists

Normalization is a set of **guidelines** for structuring tables so redundancy is
reduced and data quality improves.

**Important correction:** Normalization is **not a hard rule**. SQL will not reject
an unnormalized table — the point is *design quality*, not validity. The framing is
similar to **SOLID principles** in software engineering:

> You can ignore it and still have working software, but the result is often harder
> to maintain and more error-prone.

Real database design is about **trade-offs**:

- Does the design reduce duplicate data?
- Does it make updates safer?
- Does it fit the real use case?
- What do you gain and lose by normalizing more?

⚠️ Don't treat normalization as something to apply mechanically just because the
textbook says so.

> **Key takeaway:** Normalization is mainly about improving schema quality by
> reducing redundancy and preventing inconsistency.

---

## 🔁 Redundancy, Consistency, and Why It Matters

As systems grow, the same information often ends up stored in multiple places.
That duplicate storage is **data redundancy**.

**Example (Airtribe-style):**

- A `users` table stores user ID, name, contact details
- A `mentor` table stores ratings, company, years of experience
- ❌ Poor design: copying `name` and `phone` into `mentor` too

**Why this is a problem:**

1. Uses more storage
2. Makes updates more expensive
3. **Most importantly** — creates inconsistency if one copy is updated and another isn't

This mirrors **DRY** in code: duplicating database facts makes consistency hard.

> **Key insight:** The biggest practical danger of redundancy is **not wasted
> space — it is conflicting data.**
>
> **Key takeaway:** Normalization keeps each fact in one appropriate place so
> updates stay reliable.

---

## 🔗 Dependency and the Student Enrollment Example

An attribute **determines** another if knowing the first lets you uniquely
identify the second:

```
StudentID → Name
```

- Left side determines right side
- Right side **depends on** the left side

**Running example — Student Enrollment table:**

| Student ID | Student Name | Course ID | Course Name | Instructor ID | Instructor Name | Instructor Office Hours |
|-----------|--------------|-----------|-------------|---------------|-----------------|--------------------------|

> **Key takeaway:** Dependency is about unique determination — it drives how you
> split data during normalization.

---

## 1️⃣ First Normal Form (1NF)

**Rule:** A table should not contain multi-valued data in a single column.
Each cell holds **one atomic value**.

**Violation:** Alice has two courses — course ID, course name, instructor ID,
instructor name, and office hours all stored as multiple values in one row.

**Fix:** Split repeated values into separate rows — one value per cell.

### Why 1NF Matters

- Filtering becomes easier
- Querying becomes cleaner
- Indexing works better
- Updates become less awkward

Comma-separated or list-like fields may look convenient, but they make querying
and filtering messy. Even if SQL can store structured values like JSON, the
database often has to fetch and deserialize the whole value — less efficient
than a clean relational design.

> **Key insight:** 1NF supports cleaner storage, easier querying, and better
> performance.
>
> ⚠️ The issue is not whether data is "structured" vaguely — it's whether each
> cell contains one indivisible value.
>
> **Key takeaway:** 1NF is about atomic values, not just "organized-looking" data.

---

## ⚠️ Why Blindly Applying 1NF Can Be a Bad Idea

Normalization is a guideline — don't force 1NF blindly without considering read
patterns and scale.

### Example 1: Instagram Followers

Follower lists range from a few names to **millions of IDs**. A single huge logical
row can span many **pages** (small storage units), causing:

- Storage inefficiency
- Traversal overhead across pages

> **Key insight:** A single huge multi-value field can become painfully expensive to read.

### Example 2: Amazon Addresses

A user's address list is typically small — maybe 2, 5, 10, or 30 addresses.
Normalizing is much more reasonable here: scale is small and manageable.

### The Real Question

Not *"normalize or not?"* but:

- How large is the repeated collection?
- How often does it change?
- What does the access pattern look like?

> **Key takeaway:** The right design depends on the size and behavior of the
> multi-value data.

---

## 🧵 Concurrency Problems with Aggregated Lists

A major reason not to keep large follower lists in a single field is **concurrency**.

```
followers_list = [A, B, C]

Thread 1 reads  [A, B, C]
Thread 2 reads  [A, B, C]
Thread 1 writes [A, B, C, D]
Thread 2 writes [A, B, C, E]   ← D is LOST
```

The last write erases the first — a **lost update**.

The instinctive fix is a **lock**, but that serializes operations: correct, yet
it destroys throughput at high-write scale (e.g., a viral social media account).

> **Key insight:** When multiple writers perform read-modify-write on the same
> aggregated value, the last write can erase earlier updates.
>
> ⚠️ Locking can protect correctness, but it may not scale.
>
> **Key takeaway:** For high-write data, storing each relationship separately is
> safer than repeatedly editing one shared blob.

---

## ⚖️ When Normalization Fits and When It Doesn't

| | Instagram-style (followers) | Amazon-style (addresses) |
|---|---|---|
| List size | Enormous | Small (2–30) |
| Concurrency | Real concern | Usually not serious |
| Storage volume | High | Low |
| Verdict | 1NF-style separation **essential** | Decomposition **not always necessary** |

> **Key insight:** Normalize where it solves a real problem; don't force it everywhere.
>
> **Key takeaway:** Normalization is a trade-off tool, not a universal commandment.
> Think logically about the use case, not just theoretically about the normal form.

---

## 🚨 Anomalies: What Goes Wrong When Normalization Is Poor

**Anomalies** are inconsistencies or errors caused by poor table design,
especially with redundancy.

> - **Redundancy** = the same fact is stored more than once
> - **Anomaly** = the problem that can result from that duplication

Three main types:

### Insert Anomaly

The schema forces awkward, incomplete, or misleading rows to represent a new fact.

**Example:** A new course `CS13 – Power BI` exists before any student enrolls.
An enrollment-table design forces rows with NULL student/instructor fields.

⚠️ The issue isn't NULL itself — it's **semantic**: the table claims to represent
enrollments but stores a course with no enrollment, so `COUNT(*)` can overstate
real enrollments.

> **Key takeaway:** Insert anomalies happen when the schema makes it hard to add
> a fact cleanly without awkward extra data.

### Update Anomaly

The same fact is repeated in multiple rows; every copy must be updated.

**Example:**

```
Employee 1 | Customer 1 | 60K
Employee 1 | Customer 2 | 60K
```

A salary change requires updating both rows; miss one and the same employee has
two different salaries. The problem is one logical fact duplicated in several
places — creating room for **partial updates**.

> **Key takeaway:** If changing one fact requires many row updates, the design is
> vulnerable to update anomalies.

### Delete Anomaly

Removing one row accidentally deletes other information that should have remained.

**Example:** `CS13` exists; Rahul is the only enrolled student. Deleting Rahul's
row deletes the course data too — the row was the only place it existed.

> **Key takeaway:** Good normalization protects facts from being accidentally lost
> when one related row is removed.

---

## 2️⃣ Second Normal Form (2NF)

**Rule:** Remove **partial dependency** — especially relevant when the primary
key is **composite**.

**Setup:**

- Table: student ID, student name, course ID, course name, instructor ID,
  instructor name, instructor office
- Composite primary key: `(student ID, course ID)`

### Partial Dependency

A non-key attribute depends on **only part** of the composite key:

```
CourseID → CourseName
```

Course name doesn't depend on student ID — yet the primary key is the
combination. That's partial dependency → **not in 2NF**.

The redundancy: if many students take `CS1`, then `Gen AI` repeats in many rows.
The repeated *student-course relationship* is fine; the repeated *course details*
are the problem.

### The Fix

Split the table:

- **Enrollment table** — stores the relationship (student ↔ course)
- **Course table** — stores course details, linked via foreign key

> **Key insight:** If a non-key attribute depends on only part of a composite key,
> move it into its own table.
>
> **Key takeaway:** 2NF removes attributes that depend on only part of a composite
> primary key.

---

## 🧩 Normalized Table Design

Separate the **"things"** (entities) from the **"relationships"** (links):

```
students            → student details
courses             → course details
instructors         → instructor details
student_course      → which student takes which course
course_instructor   → which instructor teaches which course
```

This captures many-to-many relationships properly instead of stuffing repeated
IDs into a single column.

> **Key insight:** Separate the entities from the links between them.

A looser design (comma-separated course IDs in the student row) can reduce row
duplication but breaks clean relational structure. It may be defensible only when
the list is small, changes rarely, storage isn't a concern, and concurrency is mild.

⚠️ Just because a denormalized design *can* work doesn't mean it's the default
good choice.

> **Key takeaway:** Use separate tables for entities and relationships unless
> real-world constraints justify a simpler compromise.

---

## 🌐 Cross-Database Consistency and Practical Constraints

Don't assume a simple cross-database transaction will solve every consistency
problem. In distributed setups, consistency may need to be handled at the
**application level**.

Database design is always tied to operational realities:

- Distribution
- Consistency
- Security / privacy constraints
- Application behavior

> **Key takeaway:** Good schema design balances normalization theory with practical
> constraints and expected access patterns. Normalization is a starting point for
> reasoning — not the entire answer.

---

## 📖 Quick Reference

### ER Basics
- **Entity** = real-world object
- **Attribute** = property of an entity
- **Key types:** candidate, primary, foreign, super

### Normalization
- A set of **guidelines**, not a hard rule
- Main goal: **reduce redundancy**
- Secondary goal: **prevent anomalies and inconsistency**

### 1NF
- No multi-valued columns; each cell atomic
- Avoid comma-separated lists / repeated values in one field

### When Not to Force 1NF Blindly
- Very large collections in one row → hurts storage, page traversal, concurrency
- Small collections → may be fine stored simply, depending on use case

### Anomalies
| Anomaly | What happens |
|---|---|
| **Insert** | Awkward or misleading insertion of a fact |
| **Update** | Same fact stored multiple times; partial update causes inconsistency |
| **Delete** | Deleting one row removes other needed information |

### 2NF
- Removes partial dependency
- Especially relevant with composite primary keys
- Non-key attribute depends on only part of the key → move it to another table

### Design Principle
> Separate the entities from the relationships. Use the simplest structure that
> fits the actual use case and scale.
