# Database Normalization, ACID, Transactions, WAL, and Recovery

A practical revision guide covering:

-   Database normalization
-   Insert, update, and delete anomalies
-   First, Second, and Third Normal Form
-   Functional dependencies
-   ACID properties
-   SQL transactions
-   Write-Ahead Logging
-   Checkpoints and crash recovery
-   Commit and rollback
-   Interview questions and answers

------------------------------------------------------------------------

## Table of Contents

1.  [Database Normalization](#database-normalization)
2.  [Data Anomalies](#data-anomalies)
3.  [First Normal Form](#first-normal-form-1nf)
4.  [Second Normal Form](#second-normal-form-2nf)
5.  [Third Normal Form](#third-normal-form-3nf)
6.  [Complete Normalization Example](#complete-normalization-example)
7.  [Normalization vs Performance](#normalization-vs-performance)
8.  [ACID Properties](#acid-properties)
    -   [Isolation Levels and Concurrency](#isolation-levels-and-concurrency)
    -   [Concurrency Phenomena](#concurrency-phenomena)
    -   [Choosing an Isolation Level](#choosing-an-isolation-level)
9.  [Transactions](#transactions)
10. [Transaction Example](#transaction-example)
11. [Write-Ahead Logging](#write-ahead-logging-wal)
12. [Checkpoints and Recovery](#checkpoints-and-recovery)
13. [Rollback](#rollback)
14. [Quick Reference](#quick-reference)
15. [Interview Questions](#interview-questions)

------------------------------------------------------------------------

# Database Normalization

**Normalization** is the process of organizing relational data to reduce
unnecessary duplication and prevent data modification anomalies.

The main goals are:

-   Store each fact in an appropriate place
-   Reduce repeated data
-   Improve data consistency
-   Prevent insert, update, and delete anomalies
-   Make relationships between entities clearer

> Normalize by default, but do not normalize blindly. The correct design
> depends on consistency requirements, access patterns, performance, and
> scale.

Normalization is normally discussed through a series of **normal
forms**, including:

-   First Normal Form --- 1NF
-   Second Normal Form --- 2NF
-   Third Normal Form --- 3NF
-   Boyce-Codd Normal Form --- BCNF
-   Fourth Normal Form --- 4NF
-   Fifth Normal Form --- 5NF

For many application databases, understanding and applying **3NF**
addresses the most common modeling problems.

------------------------------------------------------------------------

# Data Anomalies

Consider the following unnormalized or poorly designed table:

  --------------------------------------------------------------------------------
        student_id student_name          course_id course_name   instructor_name
  ---------------- -------------- ---------------- ------------- -----------------
                 1 Alice                       101 Databases     Dr. Smith

                 2 Bob                         101 Databases     Dr. Smith

                 1 Alice                       102 Networking    Dr. Khan
  --------------------------------------------------------------------------------

This design repeats student, course, and instructor information.

## Insert anomaly

Suppose the university creates a new course but no student has enrolled
in it.

If course information can only be inserted as part of an enrollment row,
the course cannot be stored without inventing student data or using
unnecessary `NULL` values.

## Update anomaly

If Dr. Smith changes their name, every enrollment row containing that
instructor must be updated.

If one row is missed, the database contains conflicting information.

## Delete anomaly

If Bob is the last student enrolled in a course and his enrollment row
is deleted, the database could accidentally lose the only stored
information about that course.

------------------------------------------------------------------------

# First Normal Form --- 1NF

A table is in **First Normal Form** when:

-   Each column contains atomic values
-   Each cell contains one value rather than a list
-   Rows can be uniquely identified
-   Values in a column represent the same kind of attribute

## 1NF violation

``` text
students
+------------+--------------+-------------------------+
| student_id | student_name | courses                 |
+------------+--------------+-------------------------+
| 1          | Alice        | Databases, Networking   |
+------------+--------------+-------------------------+
```

The `courses` column contains multiple values.

Querying, validating, updating, and indexing individual courses becomes
difficult.

## Converting to 1NF

One possible 1NF representation is:

``` text
student_courses
+------------+--------------+------------+
| student_id | student_name | course     |
+------------+--------------+------------+
| 1          | Alice        | Databases  |
| 1          | Alice        | Networking |
+------------+--------------+------------+
```

Each cell now contains one value.

However, this design still repeats `student_name`. Reaching 1NF does not
automatically mean the schema is in 2NF or 3NF.

------------------------------------------------------------------------

# Second Normal Form --- 2NF

A table is in **Second Normal Form** when:

1.  It is already in 1NF.
2.  Every non-key attribute depends on the **entire candidate key**, not
    only part of a composite key.

A **partial dependency** occurs when a non-key attribute depends on only
one part of a composite key.

> A 2NF problem generally matters when a candidate key contains multiple
> columns.

## Example of a 2NF violation

Consider:

``` text
enrollments
+------------+-----------+--------------+-------------+-------+
| student_id | course_id | student_name | course_name | grade |
+------------+-----------+--------------+-------------+-------+
| 1          | 101       | Alice        | Databases   | A     |
| 1          | 102       | Alice        | Networking  | B     |
| 2          | 101       | Bob          | Databases   | A     |
+------------+-----------+--------------+-------------+-------+
```

Assume the primary key is:

``` text
(student_id, course_id)
```

The functional dependencies include:

``` text
student_id -> student_name
course_id  -> course_name
(student_id, course_id) -> grade
```

The problems are:

-   `student_name` depends only on `student_id`
-   `course_name` depends only on `course_id`
-   Only `grade` depends on the complete composite key

Therefore, the table violates 2NF.

## Converting to 2NF

Separate the different entities:

``` sql
CREATE TABLE students (
    student_id   INT PRIMARY KEY,
    student_name VARCHAR(100) NOT NULL
);

CREATE TABLE courses (
    course_id   INT PRIMARY KEY,
    course_name VARCHAR(100) NOT NULL
);

CREATE TABLE enrollments (
    student_id INT NOT NULL,
    course_id  INT NOT NULL,
    grade      VARCHAR(2),

    PRIMARY KEY (student_id, course_id),

    FOREIGN KEY (student_id)
        REFERENCES students(student_id),

    FOREIGN KEY (course_id)
        REFERENCES courses(course_id)
);
```

Now:

-   Student information is stored once
-   Course information is stored once
-   Enrollment contains facts about the student-course relationship

------------------------------------------------------------------------

# Third Normal Form --- 3NF

A table is in **Third Normal Form** when:

1.  It is already in 2NF.
2.  Its non-key attributes do not depend transitively on a candidate key
    through another non-key attribute.

A simplified interview explanation is:

> Non-key attributes should depend on the key, the whole key, and
> nothing but the key.

## Transitive dependency

A transitive dependency can be represented as:

``` text
A -> B
B -> C
Therefore, A -> C indirectly
```

If `A` is a key and both `B` and `C` are non-key attributes, this can
indicate a 3NF violation.

## Example of a 3NF violation

``` text
courses
+-----------+-------------+---------------+-----------------+
| course_id | course_name | instructor_id | instructor_name |
+-----------+-------------+---------------+-----------------+
| 101       | Databases   | 10            | Dr. Smith       |
| 102       | Networking  | 20            | Dr. Khan        |
+-----------+-------------+---------------+-----------------+
```

The dependencies are:

``` text
course_id     -> course_name
course_id     -> instructor_id
instructor_id -> instructor_name
```

Therefore:

``` text
course_id -> instructor_id -> instructor_name
```

`instructor_name` depends on the key indirectly through `instructor_id`.

## Converting to 3NF

Create a separate instructor table:

``` sql
CREATE TABLE instructors (
    instructor_id   INT PRIMARY KEY,
    instructor_name VARCHAR(100) NOT NULL
);

CREATE TABLE courses (
    course_id     INT PRIMARY KEY,
    course_name   VARCHAR(100) NOT NULL,
    instructor_id INT,

    FOREIGN KEY (instructor_id)
        REFERENCES instructors(instructor_id)
);
```

Now instructor information is stored in one place.

> This example assumes one instructor is assigned to each course. If a
> course can have multiple instructors, introduce a junction table such
> as `course_instructors`.

------------------------------------------------------------------------

# Complete Normalization Example

## Poor initial design

``` sql
CREATE TABLE student_course_details (
    student_id       INT,
    student_name     VARCHAR(100),
    student_email    VARCHAR(255),
    course_id        INT,
    course_name      VARCHAR(100),
    instructor_id    INT,
    instructor_name  VARCHAR(100),
    grade            VARCHAR(2),

    PRIMARY KEY (student_id, course_id)
);
```

This table contains several entities:

-   Student
-   Course
-   Instructor
-   Enrollment

It has partial and transitive dependencies.

## Functional dependencies

``` text
student_id -> student_name, student_email

course_id -> course_name, instructor_id

instructor_id -> instructor_name

(student_id, course_id) -> grade
```

## Normalized 3NF design

``` sql
CREATE TABLE students (
    student_id    INT PRIMARY KEY,
    student_name  VARCHAR(100) NOT NULL,
    student_email VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE instructors (
    instructor_id   INT PRIMARY KEY,
    instructor_name VARCHAR(100) NOT NULL
);

CREATE TABLE courses (
    course_id     INT PRIMARY KEY,
    course_name   VARCHAR(100) NOT NULL,
    instructor_id INT,

    FOREIGN KEY (instructor_id)
        REFERENCES instructors(instructor_id)
);

CREATE TABLE enrollments (
    student_id INT NOT NULL,
    course_id  INT NOT NULL,
    grade      VARCHAR(2),

    PRIMARY KEY (student_id, course_id),

    FOREIGN KEY (student_id)
        REFERENCES students(student_id),

    FOREIGN KEY (course_id)
        REFERENCES courses(course_id)
);
```

## Adding example data

``` sql
INSERT INTO students (
    student_id,
    student_name,
    student_email
)
VALUES
    (1, 'Alice', 'alice@example.com'),
    (2, 'Bob', 'bob@example.com');

INSERT INTO instructors (
    instructor_id,
    instructor_name
)
VALUES
    (10, 'Dr. Smith'),
    (20, 'Dr. Khan');

INSERT INTO courses (
    course_id,
    course_name,
    instructor_id
)
VALUES
    (101, 'Databases', 10),
    (102, 'Networking', 20);

INSERT INTO enrollments (
    student_id,
    course_id,
    grade
)
VALUES
    (1, 101, 'A'),
    (1, 102, 'B'),
    (2, 101, 'A');
```

## Querying the normalized schema

Normalization separates data, so joins are used to reconstruct related
information:

``` sql
SELECT
    s.student_id,
    s.student_name,
    c.course_id,
    c.course_name,
    i.instructor_name,
    e.grade
FROM enrollments AS e
JOIN students AS s
    ON s.student_id = e.student_id
JOIN courses AS c
    ON c.course_id = e.course_id
LEFT JOIN instructors AS i
    ON i.instructor_id = c.instructor_id
ORDER BY s.student_id, c.course_id;
```

Possible result:

``` text
+------------+--------------+-----------+-------------+-----------------+-------+
| student_id | student_name | course_id | course_name | instructor_name | grade |
+------------+--------------+-----------+-------------+-----------------+-------+
| 1          | Alice        | 101       | Databases   | Dr. Smith       | A     |
| 1          | Alice        | 102       | Networking  | Dr. Khan        | B     |
| 2          | Bob          | 101       | Databases   | Dr. Smith       | A     |
+------------+--------------+-----------+-------------+-----------------+-------+
```

------------------------------------------------------------------------

# 2NF vs 3NF

  -----------------------------------------------------------------------
  Normal form             Main issue              Diagnostic question
  ----------------------- ----------------------- -----------------------
  2NF                     Partial dependency on   Does this attribute
                          part of a composite     depend on the entire
                          candidate key           key?

  3NF                     Transitive dependency   Does one non-key
                          through a non-key       attribute determine
                          attribute               another non-key
                                                  attribute?
  -----------------------------------------------------------------------

## Memory aid

``` text
2NF: part of the key determines a field.

3NF: a non-key field determines another field.
```

------------------------------------------------------------------------

# Normalization vs Performance

Normalization improves:

-   Consistency
-   Data integrity
-   Maintainability
-   Storage efficiency
-   Update safety

However, highly normalized schemas can require more joins.

In distributed systems, related data may also be located on different
servers or shards. Retrieving it can require network communication,
which is usually more expensive than a local join.

## Denormalization

**Denormalization** deliberately duplicates or reshapes data to improve
read performance or simplify a particular access pattern.

Examples include:

-   Storing a calculated total
-   Keeping a reporting table
-   Creating a materialized view
-   Duplicating selected data in a read model
-   Storing precomputed aggregates

Denormalization introduces risks:

-   Duplicate data can become inconsistent
-   Updates become more complex
-   Additional synchronization logic may be necessary
-   Storage requirements increase

> Denormalization should be based on measured performance requirements,
> not assumptions.

Before denormalizing, consider:

-   Appropriate indexes
-   Query optimization
-   Caching
-   Read replicas
-   Materialized views
-   Table partitioning
-   Better shard-key selection

------------------------------------------------------------------------

# ACID Properties

ACID describes important transaction properties provided by relational
database systems.

  -----------------------------------------------------------------------
  Property                            Meaning
  ----------------------------------- -----------------------------------
  Atomicity                           All operations succeed as one unit,
                                      or none take effect

  Consistency                         A transaction moves the database
                                      from one valid state to another

  Isolation                           Concurrent transactions are
                                      controlled so they do not interfere
                                      incorrectly

  Durability                          Once committed, changes survive
                                      failures covered by the database's
                                      guarantees
  -----------------------------------------------------------------------

## Atomicity

Atomicity means **all or nothing**.

For example, a bank transfer normally involves:

1.  Subtracting money from Account A
2.  Adding money to Account B

Both operations must succeed together. If the second operation fails,
the first must not remain permanently applied.

## Consistency

Consistency means a successful transaction preserves database rules and
invariants.

Examples include:

-   Primary-key uniqueness
-   Foreign-key validity
-   Check constraints
-   Application-level rules
-   Valid account balance rules

Consistency does not mean that every transaction automatically contains
correct business logic. The schema, application, and transaction must
define and enforce the relevant rules.

# Isolation
Isolation controls how concurrent transactions observe and affect one
another.
## Isolation Levels and Concurrency

Isolation controls what one transaction can observe while other
transactions are running. The goal is to prevent incorrect results
caused by concurrency, while avoiding unnecessary blocking and
performance costs.

**Beginner mental model:** Imagine two users updating the same shopping
order at the same time. Isolation determines what each user can see and
whether both users' decisions can safely be committed.

### First, understand the four concurrency bugs

#### 1. Dirty read

Transaction B reads a value written by Transaction A before A commits.
If A later rolls back, B has read data that never became committed
truth.

**Timeline Execution Matrix --- product price**

Initial committed price: ₹100.

| Time | Transaction A | Transaction B | Database State / Snapshot View |
| :--- | :--- | :--- | :--- |
| **T1** | `BEGIN;` | *Idle* | Committed price is ₹100. |
| **T2** | `UPDATE products SET price = 200 WHERE id = 1;` | *Idle* | Transaction A changes price to ₹200 (Uncommitted). |
| **T3** | *Processing application logic...* | `SELECT price FROM products WHERE id = 1;`<br>📊 **Result: ₹200** | **Dirty Read Anomaly.** Transaction B reads the uncommitted value written by Transaction A. |
| **T4** | `ROLLBACK;` | *Processing application logic...* | Transaction A aborts. Database rolls price back to ₹100. |
| **T5** | *Finished* | Uses ₹200 value for checkout or shipping calculation. | **System Failure.** Transaction B operates on a dirty state that never officially existed. |

**Expected safe behavior:** B should not read A's uncommitted value.

**When it matters:** Prices, balances, inventory, order status, and any
decision that must be based on committed data.

#### 2. Non-repeatable read (also called fuzzy read)

Transaction A reads one row. Transaction B changes or deletes that row
and commits. When A reads the same row again, the value is different or
the row is gone.

**Timeline Execution Matrix --- invoice generation**

Initial committed product price: ₹100.

| Time | Transaction A (Invoice Generation) | Transaction B (Price Update) | Database State / Snapshot View |
| :--- | :--- | :--- | :--- |
| **T1** | `SELECT price FROM products WHERE id = 5;`<br>📊 **Result: ₹100** | *Idle* | Transaction A reads initial price and caches it for application validation steps. |
| **T2** | *Processing checkout steps...* | `UPDATE products SET price = 200 WHERE id = 5;` | Transaction B changes the underlying price row to ₹200. |
| **T3** | *Processing checkout steps...* | `COMMIT;` | Transaction B commits its data. The database price is officially finalized at ₹200. |
| **T4** | `SELECT price FROM products WHERE id = 5;`<br>👻 **Result: ₹200** | *Finished* | **Non-Repeatable Read.** Transaction A re-reads the same row and gets a different value within the same execution scope. |

A single invoice calculation could use ₹100 in one step and ₹200 in
another if it rereads the row under an isolation level that permits
this.

**Expected behavior depends on the business rule:** If one transaction
needs a stable view of a row for the entire operation, use an isolation
level or query design that provides that guarantee.

#### 3. Phantom read

Transaction A queries a set of rows matching a condition. Transaction B
inserts or changes a row so that it matches the condition and commits.
When A runs the same range query again, an additional matching row
appears.

**Timeline Execution Matrix --- booking capacity**

Assume a room can have at most 10 active bookings, and the current count
is 9.

| Time | Transaction A (User 1) | Transaction B (User 2) | Database State / Snapshot View |
| :--- | :--- | :--- | :--- |
| **T1** | `SELECT COUNT(*) FROM bookings WHERE room_id = 5;`<br>📊 **Result: 9** | *Idle* | 9 rows exist. Transaction A sees 9, concludes 1 slot is left, and starts booking. |
| **T2** | *Processing application logic...* | `INSERT INTO bookings (room_id, status) VALUES (5, 'active');` | A 10th row is inserted by Transaction B, but it remains uncommitted. |
| **T3** | *Processing application logic...* | `COMMIT;` | Transaction B finalizes its row. True count is now 10. |
| **T4** | `SELECT COUNT(*) FROM bookings WHERE room_id = 5;`<br>👻 **Result: 10** | *Finished* | **Phantom Read.** A completely new record materializes inside Transaction A's range query scope out of nowhere. |

A phantom is about a **set/range of rows**, not merely a changed value
in one already-read row.
>**Important:** Preventing a phantom read does not automatically make
every multi-row business rule safe. Write skew can still occur under
snapshot-based isolation.

#### 4. Write skew

Two transactions read overlapping data, make decisions that are
individually reasonable, and update different rows. Because they write
different rows, neither necessarily overwrites the other's change. But
the combined result violates a business rule.

**Timeline Execution Matrix --- on-call staffing**

Rule: At least one doctor must remain on call. Two doctors, Alice and
Bob, are both on call.

| Time | Transaction A (Dr. Alice) | Transaction B (Dr. Bob) | Database State & Snapshot View |
| :--- | :--- | :--- | :--- |
| **T1** | `SELECT COUNT(*) FROM doctors WHERE status = 'on_call';`<br>📊 **Result: 2** | *Idle* | Transaction A opens a snapshot. Sees 2 doctors. Thinks: *"Safe for me to go off-call."* |
| **T2** | *Processing...* | `SELECT COUNT(*) FROM doctors WHERE status = 'on_call';`<br>📊 **Result: 2** | Transaction B opens an independent snapshot. Also sees 2 doctors and thinks the exact same thing. |
| **T3** | `UPDATE doctors SET status = 'off_call' WHERE name = 'Alice';` | *Processing...* | Transaction A updates Alice's row. Allowed since no row lock conflicts on Alice's row. |
| **T4** | *Processing...* | `UPDATE doctors SET status = 'off_call' WHERE name = 'Bob';` | Transaction B updates Bob's row. Allowed since no row lock conflicts on Bob's row. |
| **T5** | `COMMIT;` | *Processing...* | Transaction A successfully commits. Alice is now `off_call`. |
| **T6** | *Finished* | `COMMIT;` | Transaction B successfully commits. Bob is now `off_call`. |
| **🚨 Result** | **Alice = off_call** | **Bob = off_call** | **Invariant Broken.** The total count of on-call doctors is now **0**. |

This can happen under snapshot isolation / some implementations of
Repeatable Read because each transaction changes a different row.
Serializable isolation is designed to prevent outcomes that cannot be
explained by a serial execution, though the application must still
define the invariant correctly.

**Common fixes:** Serializable transactions with retry handling,
explicit locking of a shared guard row, or a schema/constraint design
that directly enforces the rule.

# SQL Transaction Isolation Levels — Step-by-Step Dry Runs

## 1. Read Uncommitted (Exposing Dirty Reads)

This example demonstrates why **Read Uncommitted** provides the weakest isolation. Transaction B can read uncommitted changes made by Transaction A, potentially causing incorrect business decisions.

- **Initial State:** Product price is ₹100.
- **Scenario:** An admin updates the price to ₹200 but later rolls back the transaction.

| Time | Transaction A (Admin Portal) | Transaction B (Checkout Service) | Database State & Visibility |
|---|---|---|---|
| T1 | `BEGIN;`<br>`UPDATE products SET price = 200 WHERE id = 1;` | Idle | Transaction A updates the price to ₹200 but does not commit. |
| T2 | Processing application logic... | `BEGIN;`<br>`SELECT price FROM products WHERE id = 1;`<br>**Result: ₹200** | 🚨 **Dirty Read:** Transaction B reads Transaction A's uncommitted value. |
| T3 | `ROLLBACK;` | Processing payment... | Transaction A aborts. The official price returns to ₹100. |
| T4 | Finished | `COMMIT;` | Transaction B completes the sale using ₹200, even though that price was never committed. |

### Key Takeaway

- **Problem:** A transaction can read data that another transaction later rolls back.
- **Business Impact:** Incorrect invoices, payments, or checkout decisions.
- **Important:** Read Uncommitted permits dirty reads under the SQL standard, but actual behavior depends on the database engine. For example, PostgreSQL treats Read Uncommitted as Read Committed.

---

## 2. Read Committed (Overcoming Dirty Reads)

This example demonstrates how **Read Committed** prevents dirty reads while allowing non-repeatable reads.

- **Initial State:** Product price is ₹100.
- **Scenario:** Transaction A reads the price, Transaction B updates and commits it, and Transaction A reads it again.

| Time | Transaction A (Invoice Engine) | Transaction B (Price Updater) | Database State & Visibility |
|---|---|---|---|
| T1 | `BEGIN;`<br>`SELECT price FROM products WHERE id = 1;`<br>**Result: ₹100** | Idle | Transaction A reads the initial committed price. |
| T2 | Processing line items... | `BEGIN;`<br>`UPDATE products SET price = 200 WHERE id = 1;` | Transaction B updates the row but has not committed. |
| T3 | `SELECT price FROM products WHERE id = 1;`<br>**Result: ₹100** | Processing... | 🛡️ **Dirty Read Prevented:** Transaction A cannot see Transaction B's uncommitted update. |
| T4 | Processing line items... | `COMMIT;` | Transaction B commits. The official price becomes ₹200. |
| T5 | `SELECT price FROM products WHERE id = 1;`<br>**Result: ₹200** | Finished | 👻 **Non-Repeatable Read:** Transaction A sees a different value for the same row within the same transaction. |

### Key Takeaway

- **Solved:** Dirty reads.
- **Remaining Problem:** Non-repeatable reads can occur because each statement may see a newer committed version.
- **Business Impact:** An invoice calculation may use different prices for the same product at different points in the same transaction.
- **Typical Use Case:** Applications that need committed data but do not require a stable view across multiple statements.

---

## 3. Repeatable Read (Overcoming Non-Repeatable Reads)

This example demonstrates how **Repeatable Read** prevents a transaction from observing a different version of an existing row when it reads that row repeatedly.

- **Initial State:** Product price is ₹100.
- **Scenario:** Transaction A reads the price, Transaction B changes and commits the price, and Transaction A reads it again.
- **Implementation Note:** This example assumes snapshot-based Repeatable Read, such as PostgreSQL's implementation using MVCC.

| Time | Transaction A (Reporting Worker) | Transaction B (Price Updater) | Database State & Visibility |
|---|---|---|---|
| T1 | `BEGIN;`<br>`SELECT price FROM products WHERE id = 1;`<br>**Result: ₹100** | Idle | Transaction A establishes its transaction snapshot. |
| T2 | Generating chart data... | `BEGIN;`<br>`UPDATE products SET price = 200 WHERE id = 1;`<br>`COMMIT;` | Transaction B commits the new price of ₹200. |
| T3 | `SELECT price FROM products WHERE id = 1;`<br>**Result: ₹100** | Finished | 🛡️ **Non-Repeatable Read Prevented:** Transaction A continues to see the original version of the row. |
| T4 | `COMMIT;` | Idle | Transaction A ends. A new transaction can see the committed price of ₹200. |

### Key Takeaway

- **Solved:** Non-repeatable reads for the scenario shown.
- **Mechanism:** MVCC and a consistent transaction snapshot in snapshot-based implementations.
- **Important Limitation:** Repeatable Read does not have identical behavior in every database. Some implementations can still permit phantom reads or serialization anomalies.
- **Typical Use Case:** Consistent reports, analytics, and multi-query operations that need a stable view of existing data.

---

## 4. Serializable (Preventing Serialization Anomalies)

This example demonstrates how **Serializable** isolation protects a business rule involving multiple rows.

- **Business Rule:** A maximum of 10 active bookings is allowed for a room.
- **Initial State:** There are 9 active bookings for room ID 5.
- **Scenario:** Two users attempt to create the 10th and 11th bookings concurrently.

| Time | Transaction A (User 1 Checkout) | Transaction B (User 2 Checkout) | Database Engine Enforcement |
|---|---|---|---|
| T1 | `BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE;` | `BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE;` | Both transactions begin under Serializable isolation. Exact syntax varies by database. |
| T2 | `SELECT COUNT(*) FROM bookings WHERE room_id = 5;`<br>**Result: 9** | `SELECT COUNT(*) FROM bookings WHERE room_id = 5;`<br>**Result: 9** | Both transactions observe 9 bookings. |
| T3 | `INSERT INTO bookings (room_id) VALUES (5);` | Processing application logic... | Transaction A provisionally inserts the 10th booking. |
| T4 | `COMMIT;` | `INSERT INTO bookings (room_id) VALUES (5);` | Transaction A commits. The booking count becomes 10. Transaction B's conflicting read/write dependencies may require it to abort. |
| T5 | Finished | `COMMIT;`<br>**Possible outcome: Serialization Failure** | 🛡️ **Invariant Protected:** If the database detects a serialization anomaly, Transaction B is aborted and must be retried. |

Under Serializable, the database must prevent both transactions from
committing in a way that violates the serializable outcome. It may block
one transaction or abort one with a serialization error. The application
must be ready to retry a transaction that is aborted.

**Use for:** High-integrity decisions involving multiple rows or ranges,
such as capacity limits, allocation rules, and invariants that are
difficult to enforce using a single constraint or atomic update.

**Avoid using blindly for:** Every read in a high-throughput application
without measuring contention. Long-running transactions and hot data can
increase waits, aborts, and retries.

**Important:** Serializable does not mean "nothing ever fails."
Applications still need correct constraints, transaction boundaries,
error handling, and retry logic.

### Key Takeaway

- **Solved:** Serialization anomalies that would violate the intended serial execution of transactions.
- **Mechanism:** Depending on the database, Serializable isolation can use predicate or range locking, dependency tracking, conflict detection, or transaction aborts.
- **Business Impact:** Helps protect booking limits, inventory rules, account balances, and other multi-row business invariants.
- **Important:** Serializable isolation alone does not enforce every business rule automatically. The application must implement the rule correctly, and database constraints should be used where appropriate.

---

## 5. Isolation Levels — Quick Comparison

The SQL standard names four levels, but database engines do not all
implement them with identical mechanisms or guarantees. This table is a
conceptual guide; consult the target engine's documentation before
relying on a specific behavior.

| Isolation Level | Dirty Reads | Non-Repeatable Reads | Phantom Reads | Write Skew / Serialization Anomalies | Relative Cost |
|---|---|---|---|---|---|
| **Read Uncommitted** | Permitted by the standard | Permitted | Permitted | Possible | Usually lowest restrictions |
| **Read Committed** | Prevented | Possible | Possible | Possible | Low |
| **Repeatable Read** | Prevented | Prevented for rows already read | Engine-dependent; may be prevented by snapshot behavior or allowed by locking implementations | Possible in snapshot-isolation implementations | Medium |
| **Serializable** | Prevented | Prevented | Prevented as a serialization anomaly | Prevented for transactions that successfully commit under serializable guarantees | Usually highest contention/retry cost |

> "Relative cost" is not a universal speed ranking. A higher isolation
level can reduce anomalies but may increase lock waits, aborts, retries,
or deadlocks. Actual performance depends on workload, indexes,
transaction duration, and database implementation.

> **Remember:** The SQL standard defines isolation guarantees, but database engines implement them differently. Always verify the behavior of your specific database, particularly for MVCC, locking, phantom reads, and write skew.

## 6. Practical Selection Guide

| Use Case | Suggested Isolation Level | Reason |
|---|---|---|
| Simple queries that require committed data | Read Committed | Prevents dirty reads with relatively low contention. |
| Reports requiring a stable snapshot | Repeatable Read | Keeps repeated reads consistent in snapshot-based implementations. |
| Booking limits and inventory invariants | Serializable or suitable locking and constraints | Protects against conflicting concurrent transactions. |
| Financial operations requiring strong consistency | Depends on the invariant; often Serializable or explicit locking | Prevents incorrect outcomes when combined with appropriate constraints and transaction design. |

**Senior Engineer's Rule:** Choose the weakest isolation level that safely preserves your business invariants. Stronger isolation can reduce concurrency or increase transaction retries, so validate correctness and performance under realistic concurrent workloads.


### Choosing an isolation level

  ------------------------------------------------------------------------------------------
  Use case                Starting point                 Why / what to verify
  ----------------------- ------------------------------ -----------------------------------
  Read-only dashboard or  Read Committed                 Usually avoids dirty reads with
  ordinary CRUD endpoint                                 modest contention; decide whether
                                                         different statements may see
                                                         different committed versions

  Invoice or report       Repeatable Read or a           Ensure all reads use the intended
  requiring a stable      database-specific snapshot     consistent view; capture
  multi-query view        transaction                    price/version rules explicitly when
                                                         business semantics require it

  Inventory decrement     Atomic conditional `UPDATE`    Example: update only where
                          plus constraints; often Read   `quantity >= requested_quantity`;
                          Committed is sufficient        verify affected row count

  Booking/capacity limit  Serializable, or explicit      Prevent two transactions from both
  across multiple rows    locking/guard-row/constraint   observing available capacity and
                          design                         overselling it

  Money transfer between  Explicit transaction plus      Isolation alone does not replace
  two accounts            appropriate row                checking balances, affected-row
                          locking/isolation and          counts, and transaction success
                          constraints                    

  Approximate analytics   Read Committed or a            Prefer a deliberate
  where occasional        database-specific              approximate/read-only design rather
  inconsistency is        snapshot/read-only strategy    than relying on dirty reads
  acceptable                                             

  Cross-row invariant     Serializable or a shared guard Repeatable Read may permit write
  such as "at least one   row/constraint strategy        skew in snapshot-based
  doctor stays on call"                                  implementations
  ------------------------------------------------------------------------------------------

### Short decision process for a real system

1.  **State the invariant.** Example: "Inventory must never become
    negative."
2.  **Identify the read/write set.** Which rows or ranges are read, and
    which rows are changed?
3.  **Describe the bad interleaving.** What can two transactions do at
    the same time that breaks the rule?
4.  **Choose the smallest reliable protection.** A constraint or atomic
    conditional update may be simpler than raising the isolation level
    for everything.
5.  **Check engine-specific behavior.** Isolation level names alone are
    not enough.
6.  **Handle retries and deadlocks.** Serializable transactions can
    abort; locking transactions can deadlock.
7.  **Test with concurrent sessions.** A single-threaded unit test will
    not reliably expose concurrency bugs.

### SQL examples: make the business rule explicit

**Atomic inventory decrement**

``` sql
-- Illustrative SQL; adapt syntax and transaction handling to your engine.
UPDATE inventory
SET quantity = quantity - 1
WHERE product_id = 42
  AND quantity >= 1;

-- Application must check affected row count:
-- 1 row = reservation succeeded; 0 rows = unavailable or invalid product.
```

This avoids the unsafe pattern of reading a quantity in one statement
and later updating it without checking the current value.

**Explicit isolation level (syntax varies by engine)**

``` sql
-- Example syntax supported by several database engines, but not universal:
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
BEGIN;

-- Read data and perform the related writes here.

COMMIT;
```

Set the isolation level using the syntax and ordering required by the
database and driver you actually use.

### Important interview catches

-   **Dirty read is not the same as non-repeatable read.** Dirty read
    involves uncommitted data; non-repeatable read involves a changed
    committed row.
-   **Phantom read is about a changed result set.** A new or newly
    qualifying row appears in a repeated range query.
-   **Repeatable Read is not identical across vendors.** Always name the
    database engine when describing its guarantees.
-   **PostgreSQL's Repeatable Read prevents phantoms but can still
    permit write skew.** Do not equate "no phantom reads" with "fully
    serializable."
-   **SQL Server's locking Repeatable Read can permit phantoms.**
    Serializable adds key-range protection where applicable.
-   **Snapshot isolation and Serializable are not synonyms.** Snapshot
    isolation gives a consistent snapshot but may allow write skew;
    Serializable also prevents non-serializable outcomes.
-   **Isolation is not a substitute for constraints.** Use unique
    constraints, check constraints, foreign keys, and atomic conditional
    updates where they express the rule directly.
-   **Higher isolation can increase retries, waits, and deadlocks.** It
    is a correctness/performance trade-off, not a simple "higher is
    always better" choice.

### Practice exercises

For each case, identify the anomaly, predict the outcome under each
isolation level, and explain a safe design.

1.  A transaction reads a product price twice while another transaction
    updates it.
2.  Two shoppers both see one ticket remaining and attempt to buy it.
3.  Two doctors each decide to go off call because the other doctor
    appears to be on call.
4.  A report counts active users twice while another transaction inserts
    a new active user.
5.  A service reads stock quantity, waits for 200 ms, then subtracts one
    without a conditional update.

For every answer, distinguish **the isolation guarantee**, **the
database-engine implementation**, and **the business invariant**.

## Durability

Durability means that after a successful commit, the database should
preserve the committed changes across supported failures such as a
process crash or restart.

Databases commonly use mechanisms such as:

-   Durable transaction logs
-   Write-ahead logging
-   Checksums
-   Replication
-   Backups
-   Recovery procedures

Durability is not a promise that data can survive every possible
disaster. Storage destruction, corruption, operator error, or loss of
all replicas may still result in data loss.

------------------------------------------------------------------------

# Transactions

A **transaction** is one or more database operations treated as a single
logical unit of work.

The common transaction lifecycle is:

``` text
BEGIN
  |
  +-- Statement 1
  |
  +-- Statement 2
  |
  +-- Statement 3
  |
COMMIT or ROLLBACK
```

## Explicit transaction

``` sql
BEGIN;

UPDATE accounts
SET balance = balance - 100
WHERE account_id = 1;

UPDATE accounts
SET balance = balance + 100
WHERE account_id = 2;

COMMIT;
```

> Transaction syntax differs slightly between database engines. For
> example, some systems use `START TRANSACTION`.

## Rollback example

``` sql
BEGIN;

UPDATE accounts
SET balance = balance - 100
WHERE account_id = 1;

UPDATE accounts
SET balance = balance + 100
WHERE account_id = 2;

ROLLBACK;
```

After `ROLLBACK`, neither update should remain as a committed change.

## Implicit and autocommit transactions

Many database clients enable **autocommit** by default.

In autocommit mode, each individual statement is normally treated as its
own transaction unless an explicit transaction has been started.

``` sql
UPDATE students
SET student_name = 'Alice Johnson'
WHERE student_id = 1;
```

This single statement may be committed automatically, depending on the
database and client configuration.

------------------------------------------------------------------------

# Transaction Example

## Bank account table

``` sql
CREATE TABLE accounts (
    account_id INT PRIMARY KEY,
    owner_name VARCHAR(100) NOT NULL,
    balance    DECIMAL(12, 2) NOT NULL,
    CHECK (balance >= 0)
);
```

## Safe transfer

``` sql
BEGIN;

UPDATE accounts
SET balance = balance - 100.00
WHERE account_id = 1
  AND balance >= 100.00;

-- The application should verify that exactly one row was updated.

UPDATE accounts
SET balance = balance + 100.00
WHERE account_id = 2;

COMMIT;
```

If an error occurs before `COMMIT`, the application should issue:

``` sql
ROLLBACK;
```

## Application-level pseudocode

``` text
begin transaction

try:
    debit source account

    if source account was not updated:
        raise "Insufficient balance or invalid account"

    credit destination account

    commit transaction
catch error:
    rollback transaction
    report failure
```

A production implementation must also handle:

-   Missing accounts
-   Insufficient funds
-   Concurrent updates
-   Deadlocks
-   Retries
-   Idempotency
-   Correct isolation levels

------------------------------------------------------------------------

# Write-Ahead Logging --- WAL

A **Write-Ahead Log** is an internal database log used for recovery.

The central rule is:

> Relevant log records must be made durable before the corresponding
> modified data pages are considered safely written to their final
> data-file locations.

The log is commonly sequential and append-oriented, making it more
efficient to write than immediately updating many scattered data pages.

## Simplified write sequence

``` text
1. Begin transaction
2. Change a row in memory
3. Generate the corresponding WAL/log record
4. Flush the required log records
5. Commit the transaction
6. Write modified data pages later
```

The precise sequence and guarantees differ between database engines.

## Why WAL is useful

WAL helps support:

-   Crash recovery
-   Redoing changes when necessary
-   Preserving committed work
-   Efficient data-page writes
-   Replication in some database systems
-   Point-in-time recovery when combined with backups and archived logs

## Main data files vs WAL

``` text
Application
    |
    v
Database transaction
    |
    +----> WAL / transaction log
    |
    +----> Buffer cache / memory
                  |
                  v
             Data files
```

The WAL and data files serve different purposes:

  -----------------------------------------------------------------------
  Data files                          WAL
  ----------------------------------- -----------------------------------
  Store database pages and current    Stores recovery-related change
  data structures                     records

  Updated in place at the page level  Usually append-oriented

  Used for normal data access         Primarily used internally for
                                      recovery and related features
  -----------------------------------------------------------------------

## What WAL is not

WAL is not:

-   A normal application table
-   A replacement for audit logging
-   A permanent business-event archive
-   A table developers normally create themselves
-   Intended for ordinary business queries

Some database systems provide administrative functions or tools to
inspect logs, but applications should not treat WAL as a normal
queryable data model.

## WAL and auditing are different

  -----------------------------------------------------------------------
  WAL                                 Audit log
  ----------------------------------- -----------------------------------
  Designed mainly for database        Designed to record user or business
  recovery                            activity

  Internal database format            Human-readable or
                                      application-defined format

  May be recycled or removed          Retained according to audit
                                      requirements

  Engine-specific                     Application or organization
                                      specific
  -----------------------------------------------------------------------

If the application must answer, "Who changed this value and why?",
create an audit mechanism rather than depending on WAL.

------------------------------------------------------------------------

# Checkpoints and Recovery

A **checkpoint** is a database recovery coordination point.

It helps limit how much log history the database must examine or replay
during recovery.

## Simplified timeline

``` text
WAL records:  L1 ---- L2 ---- L3 ---- L4 ---- L5
                            ^
                        checkpoint
```

After a crash, the database uses its recovery metadata, WAL, and
checkpoint information to determine which operations require recovery
processing.

## Important clarification

A checkpoint does not always mean:

> Everything before this exact position can be ignored or deleted
> immediately.

The precise meaning depends on:

-   The database engine
-   Active transactions
-   Dirty data pages
-   Replication requirements
-   Backup and recovery configuration
-   Log archiving and retention policies

## Simplified crash-recovery example

Assume:

1.  A transaction updates a student record.
2.  The required WAL records become durable.
3.  The transaction commits.
4.  The database crashes before the modified data page reaches its final
    data file.

During restart, the database can use the log to redo the committed
modification.

``` text
Before crash:
WAL:       update student cohort from 40 to 70
Data page: may still contain cohort 40

After recovery:
Data page: cohort 70
```

This illustrates how WAL contributes to durability.

------------------------------------------------------------------------

# Rollback

A **rollback** cancels an uncommitted transaction and restores the
database's logical state as though that transaction had not successfully
completed.

## Example

``` sql
BEGIN;

INSERT INTO enrollments (
    student_id,
    course_id,
    grade
)
VALUES (
    1,
    101,
    'A'
);

-- A later operation fails.

ROLLBACK;
```

The inserted enrollment does not become a committed row.

## Rollback with multiple statements

Suppose a transaction contains five operations:

``` text
Statement 1: succeeds
Statement 2: succeeds
Statement 3: succeeds
Statement 4: fails
Statement 5: not executed
```

The application or database can roll back the transaction so that
statements 1--3 do not remain as committed partial work.

## Rollback vs crash recovery

These concepts are related but not identical:

-   **Rollback** removes the effects of an incomplete or cancelled
    transaction.
-   **Crash recovery** restores the database to a consistent state after
    a crash.
-   **Redo** may reapply committed work that was logged but not fully
    reflected in data files.
-   **Undo** may remove effects associated with transactions that did
    not commit.

The exact mechanisms differ between PostgreSQL, MySQL/InnoDB, SQL
Server, Oracle, and other systems.

It is therefore safer to describe WAL, checkpoints, undo, redo, and
rollback conceptually rather than assuming every database uses the same
internal algorithm.

------------------------------------------------------------------------

# Practical Example: Transaction with Savepoint

A savepoint allows part of a transaction to be rolled back without
cancelling all previous work.

``` sql
BEGIN;

UPDATE students
SET student_name = 'Alice Johnson'
WHERE student_id = 1;

SAVEPOINT student_updated;

INSERT INTO enrollments (
    student_id,
    course_id,
    grade
)
VALUES (
    1,
    999,
    'A'
);

-- Suppose course 999 is invalid.
ROLLBACK TO SAVEPOINT student_updated;

COMMIT;
```

After the commit:

-   The student-name update remains
-   The invalid enrollment insert is cancelled

Savepoint support and syntax may differ by database.

------------------------------------------------------------------------

# Common Mistakes

## Mistake 1: Treating normalization as "remove every duplicate"

Repeated values do not always prove a normalization violation.

Normalization is based primarily on:

-   Candidate keys
-   Functional dependencies
-   Entity relationships

Duplication is often a symptom, not the complete definition.

## Mistake 2: Saying every table with a single-column key is automatically in 3NF

A table with a single-column key cannot have a partial dependency on
that key, but it can still have a transitive dependency.

Example:

``` text
employee_id -> department_id
department_id -> department_name
```

This may violate 3NF even though the primary key has only one column.

## Mistake 3: Describing WAL as an audit table

WAL is mainly a recovery mechanism. An application audit log has a
different purpose.

## Mistake 4: Saying commit means all data pages are immediately written

Depending on the engine, commit may require the relevant log records to
be durable without requiring every changed data page to be written
immediately.

## Mistake 5: Assuming rollback deletes WAL history

Rollback restores the database's logical state. The engine may preserve
log records needed for recovery and internal processing.

## Mistake 6: Assuming checkpoints work identically in all databases

Checkpoint and recovery algorithms are database-engine specific.

------------------------------------------------------------------------

# Quick Reference

  -----------------------------------------------------------------------
  Concept                             Reminder
  ----------------------------------- -----------------------------------
  Normalization                       Reduces redundancy and modification
                                      anomalies

  1NF                                 Each cell contains one atomic value

  2NF                                 No non-key attribute depends on
                                      only part of a composite candidate
                                      key

  3NF                                 Avoid transitive dependencies
                                      through non-key attributes

  Functional dependency               One attribute or attribute set
                                      determines another

  Composite key                       A key containing more than one
                                      column

  Denormalization                     Intentional duplication or
                                      reshaping for a justified access
                                      pattern

  ACID                                Atomicity, Consistency, Isolation,
                                      Durability

  Isolation levels                    Trade off concurrency anomalies
                                      against waits, aborts, and retries

  Dirty read                          Read another transaction's
                                      uncommitted value

  Non-repeatable read                 Read the same row twice and get
                                      different committed values

  Phantom read                        Repeat a predicate/range query and
                                      get a different set of rows

  Write skew                          Concurrent transactions update
                                      different rows and jointly break an
                                      invariant

  Transaction                         Operations treated as one logical
                                      unit

  Commit                              Successfully makes a transaction
                                      permanent

  Rollback                            Cancels an uncommitted transaction

  Savepoint                           Creates a point for partial
                                      rollback

  WAL                                 Internal append-oriented log used
                                      for recovery

  Checkpoint                          Recovery coordination or progress
                                      point

  Redo                                Reapply changes that should be
                                      present

  Undo                                Remove effects that should not
                                      remain
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# Interview Questions

<details>
<summary>
<strong>1. What is database normalization?</strong>
</summary>
Normalization is the process of organizing relational data to reduce
unnecessary duplication and prevent insert, update, and delete
anomalies.

It usually involves identifying entities, candidate keys, functional
dependencies, and relationships, then separating different facts into
appropriate tables.

</details>
<details>
<summary>
<strong>2. What are insert, update, and delete anomalies?</strong>
</summary>
-   **Insert anomaly:** A fact cannot be inserted without adding
    unrelated information.
-   **Update anomaly:** The same fact appears in several rows and must
    be updated in multiple places.
-   **Delete anomaly:** Deleting one fact accidentally removes another
    useful fact.

These problems commonly occur when several entities are mixed into one
table.

</details>
<details>
<summary>
<strong>3. What is First Normal Form?</strong>
</summary>
A table is in 1NF when each cell contains a single atomic value and the
table does not store repeating groups or lists in one column.

For example, storing `"Databases, Networking"` in one `courses` cell
violates 1NF.

</details>
<details>
<summary>
<strong>4. What are Second Normal Form?</strong>
</summary>
A table is in 2NF when it is in 1NF and every non-key attribute depends
on the entire candidate key.

A 2NF violation occurs when a non-key field depends on only part of a
composite candidate key.

For example:

``` text
(student_id, course_id) -> grade
student_id -> student_name
course_id -> course_name
```

`student_name` and `course_name` are partially dependent and should be
moved to separate tables.

</details>
<details>
<summary>
<strong>5. Can a table with a single-column primary key violate 2NF?</strong>
</summary>
A partial dependency requires a composite candidate key. Therefore, a
non-key attribute cannot depend on only part of a single-column key.

However, candidate keys---not only the selected primary key---must be
considered in a formal normalization analysis.

A table with a single-column primary key can still violate 3NF.

</details>
<details>
<summary>
<strong>6. What is Third Normal Form?</strong>
</summary>
A table is in 3NF when it is in 2NF and non-key attributes do not depend
transitively on a candidate key through other non-key attributes.

Example:

``` text
course_id -> instructor_id
instructor_id -> instructor_name
```

`instructor_name` depends indirectly on `course_id`, so instructor
details should normally be separated.

</details>
<details>
<summary>
<strong>7. What is the difference between 2NF and 3NF?</strong>
</summary>
-   **2NF** removes partial dependencies on part of a composite
    candidate key.
-   **3NF** removes transitive dependencies through non-key attributes.

A useful diagnostic is:

``` text
2NF: Does this field depend on the whole key?

3NF: Does a non-key field determine another non-key field?
```

</details>
<details>
<summary>
<strong>8. What is a functional dependency?</strong>
</summary>
A functional dependency exists when one attribute or group of attributes
uniquely determines another attribute.

It is written as:

``` text
A -> B
```

This means that for each value of `A`, there is only one corresponding
value of `B`.

For example:

``` text
student_id -> student_name
```

</details>
<details>
<summary>
<strong>9. Why do companies sometimes denormalize databases?</strong>
</summary>
Companies may denormalize to:

-   Reduce expensive joins
-   Improve read performance
-   Precompute reporting values
-   Reduce cross-server or cross-shard requests
-   Support a specific high-volume access pattern

The tradeoff is additional duplication, synchronization complexity, and
a greater risk of inconsistent data.

</details>
<details>
<summary>
<strong>10. What does ACID stand for?</strong>
</summary>
ACID stands for:

-   **Atomicity:** All transaction operations succeed or none take
    effect.
-   **Consistency:** Transactions preserve defined database rules.
-   **Isolation:** Concurrent transactions are prevented from
    interfering incorrectly.
-   **Durability:** Committed changes survive failures covered by the
    database's guarantees.

</details>
<details>
<summary>
<strong>11. What is a transaction?</strong>
</summary>
A transaction is one or more database operations treated as a single
logical unit.

The transaction normally ends with:

-   `COMMIT` when all work succeeds
-   `ROLLBACK` when the work must be cancelled

Transactions prevent related operations from leaving the database in a
partially completed state.

</details>
<details>
<summary>
<strong>12. What is the difference between COMMIT and ROLLBACK?</strong>
</summary>
`COMMIT` successfully completes the transaction and makes its changes
durable according to the database's guarantees.

`ROLLBACK` cancels the uncommitted transaction and restores its logical
changes to the earlier state.

</details>
<details>
<summary>
<strong>13. What is autocommit?</strong>
</summary>
Autocommit is a mode in which each SQL statement is automatically
committed as its own transaction unless an explicit transaction has been
started.

Its default behavior depends on the database, driver, and client
configuration.

</details>
<details>
<summary>
<strong>14. What is a Write-Ahead Log?</strong>
</summary>
A Write-Ahead Log is an internal, append-oriented database log used for
recovery.

The database makes the required log information durable before the
related changed data pages are considered safely stored in their final
locations.

This allows the database to recover committed changes after certain
failures.

</details>
<details>
<summary>
<strong>15. Why can WAL improve database performance?</strong>
</summary>
Writing sequential log records is generally more efficient than
immediately writing many modified data pages to scattered disk
locations.

The database can first make the required log records durable, then flush
modified pages later in a more efficient way.

</details>
<details>
<summary>
<strong>16. Is WAL the same as an audit log?</strong>
</summary>
No.

WAL is mainly an internal recovery mechanism and may use an
engine-specific binary format.

An audit log is designed to answer business or security questions such
as:

-   Who changed the data?
-   What was changed?
-   When was it changed?
-   Why was it changed?

Applications should not rely on WAL as a replacement for proper
auditing.

</details>
<details>
<summary>
<strong>17. What is a checkpoint?</strong>
</summary>
A checkpoint is a recovery coordination point that helps the database
limit the amount of log processing required after a restart.

Its exact meaning and implementation depend on the database engine.

It should not be described universally as simply "everything before this
point can be deleted."

</details>
<details>
<summary>
<strong>18. How does a database recover after a crash?</strong>
</summary>
In a simplified explanation, the database:

1.  Locates relevant checkpoint and recovery information.
2.  Reads the required transaction log records.
3.  Redoes committed changes that are not fully represented in the data
    files.
4.  Ensures incomplete transactions do not remain logically applied.
5.  Restores the database to a consistent state.

The actual algorithm differs by database engine.

</details>
<details>
<summary>
<strong>19. What is the difference between rollback and crash recovery?</strong>
</summary>
Rollback cancels a transaction that has not successfully committed.

Crash recovery runs after a database failure and may involve:

-   Redoing committed work
-   Removing or ignoring incomplete work
-   Restoring a consistent database state

They are related concepts, but they are not identical operations.

</details>
<details>
<summary>
<strong>20. Does durability guarantee that data can never be lost?</strong>
</summary>
No.

Durability means committed changes survive the failures covered by the
database's guarantees.

Data can still be lost through:

-   Destruction of all storage and replicas
-   Corruption
-   Misconfiguration
-   Operator error
-   Missing backups
-   Software defects
-   Disasters beyond the recovery design

Durability should be supported by backups, replication, monitoring, and
tested recovery procedures.

</details>
<details>
<summary>
<strong>21. Does COMMIT mean every modified data page has already been written?</strong>
</summary>
Not necessarily.

In a WAL-based database, the commit may require the relevant log records
to be made durable. Modified data pages can be flushed to their final
data-file locations later.

The precise behavior depends on the database engine and durability
configuration.

</details>
<details>
<summary>
<strong>22. What is a savepoint?</strong>
</summary>
A savepoint creates a named point inside a transaction.

It allows the transaction to roll back part of its work without
necessarily cancelling everything performed since the transaction began.

Example:

``` sql
SAVEPOINT before_enrollment;
ROLLBACK TO SAVEPOINT before_enrollment;
```

</details>
<details>
<summary>
<strong>23. What is a composite key?</strong>
</summary>
A composite key is a key made from two or more columns.

For example, an enrollment may be identified by:

``` text
(student_id, course_id)
```

Neither column identifies an enrollment by itself, but their combination
does.

</details>
<details>
<summary>
<strong>24. Why are foreign keys important in a normalized schema?</strong>
</summary>
Foreign keys preserve referential integrity between related tables.

For example, an enrollment should not reference a student or course that
does not exist.

They also make entity relationships explicit in the database schema.

</details>
<details>
<summary>
<strong>25. When would you stop normalizing?</strong>
</summary>
A practical answer is:

1.  Normalize enough to create a correct and maintainable model.
2.  Measure the application's real performance.
3.  Identify specific bottlenecks.
4.  Denormalize only when the expected benefit justifies the consistency
    and maintenance cost.

Many ordinary application schemas aim for approximately 3NF, but the
right stopping point depends on the system.

</details>

------------------------------------------------------------------------

# Final Summary

``` text
Normalization
├── 1NF: Atomic values
├── 2NF: No partial dependencies
└── 3NF: No transitive dependencies

ACID
├── Atomicity: All or nothing
├── Consistency: Preserve rules
├── Isolation: Control concurrency
└── Durability: Preserve committed work

Recovery
├── WAL: Record recovery information first
├── Checkpoint: Coordinate recovery progress
├── Redo: Reapply work that should exist
├── Undo: Remove work that should not exist
└── Rollback: Cancel an uncommitted transaction
```

The central design principle is:

> Start with a correct normalized model, use transactions to protect
> related operations, and optimize only after measuring real
> performance.
