# Database Transactions & Concurrency — 20-Year Developer Mentor Notes

> **Goal:** Learn transactions the way an experienced production developer thinks about them—not by memorizing definitions, but by predicting what two concurrent transactions can see, what they can change, what can go wrong, and how to design, test, and fix it.

This guide is tailored for a developer moving from **automation testing toward development**. It starts in simple English and gradually moves toward senior-level production and interview thinking.

---

## 0. The Golden Rule: Draw the Timeline

Whenever you see a transaction/concurrency problem, do not immediately memorize an isolation-level rule.

Draw:

```text
Transaction A                 Transaction B

BEGIN
READ
                              BEGIN
                              UPDATE
                              COMMIT
READ AGAIN
COMMIT
```

Then ask:

1. What did A read?
2. What did B read?
3. Was B committed when A read?
4. Did A read the same row again?
5. Did the set of matching rows change?
6. Did both transactions make decisions using the same old state?
7. Did they update the same row or different rows?
8. What is the final database state?
9. Is the final state valid according to the business rule?
10. Is the behavior expected or a bug?
11. What isolation, locking, data-model, or application technique is appropriate?

This thought process is more valuable than memorizing a table.

---

# 1. Transaction — Foundation

A **transaction** is a logical unit of database work.

Example: transfer ₹1,000 from Account A to Account B.

```sql
BEGIN;

UPDATE accounts
SET balance = balance - 1000
WHERE id = 'A';

UPDATE accounts
SET balance = balance + 1000
WHERE id = 'B';

COMMIT;
```

We want:

```text
Debit A
+
Credit B
```

to behave as one logical operation.

If crediting B fails, we do not want the debit from A to remain committed.

```text
BEGIN
  ↓
Debit A
  ↓
Credit B
  ↓
COMMIT
```

If something fails:

```text
ROLLBACK
```

---

# 2. ACID — What a Developer Actually Needs to Know

## Atomicity

> **All or nothing.**

For a money transfer, either both sides of the operation succeed or the transaction is rolled back.

## Consistency

> **The database moves from one valid state to another valid state according to database constraints and business rules.**

Example:

```text
Before:
A = ₹10,000
B = ₹5,000
Total = ₹15,000

Transfer ₹1,000

After:
A = ₹9,000
B = ₹6,000
Total = ₹15,000
```

### Atomicity vs Consistency

Do not mix them up.

**Atomicity:**
> Did the transaction happen completely or not?

**Consistency:**
> Is the resulting state valid?

Atomicity helps preserve consistency, but consistency also depends on constraints, validation, and business logic.

## Isolation

> **How much should one transaction be protected from concurrent transactions, and what should it be allowed to see?**

Simple mental model:

> **Isolation level = visibility/concurrency rule.**

## Durability

> Once a transaction commits successfully, its committed result should survive failures according to the database's durability guarantees.

---

# 3. What Is an Isolation Level?

This was one of the biggest points of confusion, so remember:

> **An isolation level is not a different type of transaction. It is a rule that controls visibility and concurrency behavior for a transaction.**

The same query can run under different isolation levels.

```sql
SELECT balance
FROM accounts
WHERE id = 42;
```

The SQL is the same.

The visibility behavior can differ.

Think:

```text
Same query
+
Different isolation rule
=
Different concurrency behavior
```

---

# 4. Four Common Isolation Levels

```text
1. Read Uncommitted
2. Read Committed
3. Repeatable Read
4. Serializable
```

Conceptual ladder:

```text
Read Uncommitted
       ↓
Read Committed
       ↓
Repeatable Read
       ↓
Serializable
```

Generally, stronger isolation gives stronger consistency guarantees but may increase waiting, conflicts, or retries.

---

# 5. Read Uncommitted

## Simple meaning

> A transaction may be allowed to see another transaction's uncommitted changes.

Example:

Initial:

```text
Balance = ₹1,000
```

Transaction A:

```text
UPDATE balance → ₹500

-- A has NOT committed
```

Transaction B using Read Uncommitted reads:

```text
₹500
```

Then A does:

```text
ROLLBACK
```

Final committed database value:

```text
₹1,000
```

B saw ₹500 even though it never became the committed final value.

That is:

## Dirty Read

Memory:

> **Dirty Read = I read somebody else's unfinished/uncommitted change.**

### Is Read Uncommitted used in production?

It can be used for approximate/non-critical information, but it is generally a poor choice for:

- payments
- bank balances
- inventory reservation
- seat booking
- financial settlement
- critical order transitions

Important database-specific warning: database engines can implement or map Read Uncommitted differently. Do not assume every database literally exposes dirty reads.

---

# 6. Read Committed

## Simple meaning

> **A transaction does not read another transaction's uncommitted changes.**

Initial:

```text
Balance = ₹1,000
```

A:

```text
UPDATE → ₹500
-- not committed
```

B using Read Committed:

```text
SELECT balance
```

B sees:

```text
₹1,000
```

not ₹500.

Therefore:

```text
Dirty Read → Prevented
```

---

# 7. Read Committed + Non-Repeatable Read

Read Committed does **not** mean that repeated reads must return the same value.

Example:

```text
A: READ → ₹1,000

B: UPDATE → ₹800
B: COMMIT

A: READ AGAIN → ₹800
```

A read the same row twice:

```text
First  → ₹1,000
Second → ₹800
```

That is:

## Non-Repeatable Read

Memory:

> **Same row + different committed value = Non-Repeatable Read.**

---

# 8. What Does "Fuzzy Read" Mean?

"Fuzzy read" is commonly used for a non-repeatable read.

Example:

```text
First look:
Status = OPEN

Someone changes it and commits.

Second look:
Status = RESOLVED
```

You looked at the same row twice, but it changed between the reads.

---

# 9. Expected Behavior vs Bug

A concurrency phenomenon is **not automatically a functional defect**.

Example:

```text
Complaint #101
Status = OPEN
```

Another user changes it:

```text
OPEN → RESOLVED
COMMIT
```

The first user later sees RESOLVED.

That may be perfectly expected.

The senior developer asks:

> **Does the business operation require a consistent historical view?**

### Shopping example

A product price can legitimately change:

```text
₹999 → ₹1,049
```

Seeing the new price may be expected.

### Invoice example

If an invoice must use one agreed price, repeatedly reading the current product price could be a design problem.

Potential better data model:

```text
orders
----------------
order_id
product_id
agreed_price
quantity
```

The invoice uses `agreed_price`, not a mutable current `product.price`.

##Preventing Inconsistency Caused by Non-Repeatable Reads

1. Data Immutability (Schema Redesign)
Instead of pointing directly to dynamic, mutable tables for transactional records, copy critical values into the transaction table at the moment of creation.

Bad Design (Mutable Reference)
```sql
-- The order points directly to the product's dynamic price
CREATE TABLE order_items (
    order_id INT,
    product_id INT REFERENCES products(id), -- If product price changes, old order totals break!
    quantity INT
);
```
Good Design (Immutable Snapshot)
```sql
-- Capture the agreed price permanently on creation
CREATE TABLE order_items (
    order_id INT,
    product_id INT REFERENCES products(id),
    agreed_unit_price DECIMAL(10, 2) NOT NULL, -- Frozen snapshot of product.price at purchase time
    quantity INT
);
```
2. Row Locking (SELECT ... FOR UPDATE)
Use explicit row locking when a multi-step operation requires reading a value, making a business decision, and writing back, ensuring no concurrent transaction modifies the row in between.
```sql
BEGIN;

-- Lock the specific row so other concurrent transactions must wait
SELECT balance FROM accounts WHERE account_id = 101 FOR UPDATE;

-- Application checks if balance >= 500, then executes:
UPDATE accounts SET balance = balance - 500 WHERE account_id = 101;

COMMIT; -- Releases the lock
```
3. Snapshot Isolation / Isolation Levels
Raise the transaction isolation level when running operations (such as end-of-day financial audits or reports) that require a consistent point-in-time view across multiple tables without blocking concurrent writers.
```
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ;

-- First query reads data snapshot at transaction start
SELECT SUM(balance) FROM accounts;

-- Even if another transaction updates and commits a balance here, 
-- this second query still sees the original snapshot:
SELECT balance FROM accounts WHERE account_id = 101;

COMMIT;
```
Senior lesson:

> **Do not use an isolation level to compensate for a bad domain/data model.**

---

# 10. Repeatable Read

## Simple meaning

> **Once a transaction establishes its view of data, repeated reads remain consistent according to that database's Repeatable Read semantics.**

Production example:

Initial:

```text
Employee bonus = ₹2,000
```

Transaction A starts under Repeatable Read:

```text
A reads → ₹2,000
```

Transaction B:

```text
UPDATE bonus → ₹3,000
COMMIT
```

A reads again:

```text
A reads → ₹2,000
```

A continues seeing its transaction-consistent view.

A new transaction started later can see:

```text
₹3,000
```

---

# 11. Why Repeatable Read Prevents Non-Repeatable Reads

## Read Committed

Think:

> "Give me committed data when I read."

```text
A first read → ₹2,000
B commits → ₹3,000
A second read → ₹3,000
```

Non-repeatable read is possible.

## Repeatable Read

Think:

> "Keep my transaction view consistent."

```text
A first read → ₹2,000
B commits → ₹3,000
A second read → ₹2,000
```

Therefore:

```text
Repeatable Read
      ↓
Non-repeatable read prevented
```

### Critical clarification

Repeatable Read does not necessarily mean B cannot update.

The important distinction is:

```text
Current committed database state → ₹3,000

A's transaction view             → ₹2,000
```

Both can be true at the same time in snapshot/MVCC systems.

---

# 12. Phantom Read

A phantom read is different from a non-repeatable read.

## Non-Repeatable Read

Same row changes:

```text
Row #101
First → OPEN
Second → RESOLVED
```

## Phantom Read

The **set of rows matching a condition changes**.

Example:

Transaction A:

```sql
SELECT COUNT(*)
FROM complaints
WHERE status = 'OPEN';
```

Result:

```text
10
```

Transaction B:

```sql
INSERT INTO complaints(status)
VALUES ('OPEN');

COMMIT;
```

A runs the same query again and sees:

```text
11
```

A new matching row appeared.

That is:

## Phantom Read

Memory:

> **Non-Repeatable = same row, different value.**
>
> **Phantom = same query/range, different matching row set.**

---

# 13. Production Phantom Example

Banking application:

```text
A:
Count loans > ₹10 lakh
→ 20
```

B creates a new ₹15 lakh loan:

```text
INSERT
COMMIT
```

A runs the same query again:

```text
→ 21
```

The newly matching loan is the phantom.

---

# 14. Repeatable Read vs Phantom Reads — Database-Specific Warning

Do not blindly memorize:

> "Repeatable Read always prevents phantom reads."

Isolation-level names do not have identical implementation behavior across all database engines.

For example, PostgreSQL's Repeatable Read uses a transaction snapshot and prevents the usual phantom-read behavior within that transaction.

Other databases can have different implementation details.

Therefore:

> **Learn the actual behavior of the database you use, not only the ANSI terminology.**

---

# 15. Write Skew

## Simple definition

> **Two concurrent transactions read a shared condition, each decides its own change is safe, but their combined changes violate a business rule.**

Classic example:

```text
Doctor A = ON
Doctor B = ON

Business rule:
At least one doctor must remain ON.
```

Transaction A:

```text
Reads B = ON

"I can safely turn A OFF."
```

Transaction B:

```text
Reads A = ON

"I can safely turn B OFF."
```

Writes:

```text
A → OFF
B → OFF
```

Both commit.

Final:

```text
A = OFF
B = OFF
```

Business invariant:

```text
At least one doctor ON
```

is broken.

That is:

## Write Skew

---

# 16. Why Is Write Skew Different from Lost Update?

Write skew commonly looks like:

```text
Shared condition
      ↓
A updates row A
B updates row B
      ↓
Combined business rule breaks
```

Lost update commonly looks like:

```text
A reads old value
B reads old value

A writes
B writes

One intended update is overwritten/lost
```

Memory:

> **Different rows + shared decision + broken business invariant = Write Skew**
>
> **One concurrent change gets overwritten/lost = Lost Update**

Do not classify a concurrency issue only from "same row/different row." Look at the actual SQL, locks, and business rule.

---

# 17. Write Skew Requires Concurrency

Classic write skew requires overlapping transactions.

Sequential:

```text
A completes
   ↓
B starts
```

B can see A's committed result.

Concurrent:

```text
A reads old state
B reads old state

A writes
B writes
```

Both make decisions using the same earlier state.

Therefore:

> **Classic write skew requires overlapping/concurrent execution.**

---

# 18. Delivery-Order Write Skew Example

Suppose an order must always have at least one eligible driver assigned.

Initial:

```text
Driver A → assigned
Driver B → assigned
```

A checks:

```text
B is assigned
→ A removes himself
```

At almost the same time B checks:

```text
A is assigned
→ B removes himself
```

Both commit:

```text
A → unassigned
B → unassigned
```

No driver remains.

The business invariant is broken.

That is write skew.

---

# 19. Serializable

## Simple meaning

> **The result of concurrent transactions should be equivalent to some serial execution of those transactions.**

Serial means:

```text
A
then
B
```

or:

```text
B
then
A
```

It does not necessarily mean the database physically runs every transaction one at a time.

Think:

> **"Make the result behave as though the transactions were safely ordered."**

---

# 20. Serializable + Write Skew

Return to:

```text
A = ON
B = ON

Rule:
At least one must remain ON
```

A wants:

```text
A → OFF
```

B wants:

```text
B → OFF
```

Under Serializable semantics, the database should not silently accept an execution that produces a result inconsistent with every valid serial ordering.

Depending on the database, one transaction may:

- wait
- fail with a serialization error
- be aborted
- need to retry

The exact mechanism is database-specific.

Important production lesson:

> **Serializable can turn a silent data-integrity problem into an explicit transaction failure that the application can retry safely.**

---

# 21. Serializable Does Not Mean "No Errors"

A common beginner assumption:

> "Serializable is strongest, so every transaction automatically succeeds."

Wrong.

Serializable can produce:

```text
Serialization failure
```

Application code may need:

```text
BEGIN
  business logic
COMMIT
     ↓
serialization failure
     ↓
retry transaction
```

Retries must be designed carefully, especially when the transaction has side effects outside the database.

---

# 22. Isolation-Level Learning Table

For conceptual learning:

| Isolation Level | Dirty Read | Non-Repeatable Read | Phantom Read | Write Skew |
|---|---|---|---|---|
| Read Uncommitted | Possible | Possible | Possible | Possible |
| Read Committed | Prevented | Possible | Possible | Possible |
| Repeatable Read | Prevented | Prevented | Database-dependent | Can be possible |
| Serializable | Prevented | Prevented | Prevented by serializable semantics | Prevented by serializable semantics |

**Warning:** This is a learning model. Exact behavior depends on the database engine and implementation.

---

# 23. The Five Concurrency Problems to Recognize

## Dirty Read

```text
A writes
A doesn't commit
B reads A's value
A rolls back
```

> **Uncommitted data was read.**

## Non-Repeatable Read

```text
A reads row → OPEN
B updates row → RESOLVED + COMMIT
A reads same row → RESOLVED
```

> **Same row, different value.**

## Phantom Read

```text
A queries OPEN rows → 10
B inserts another OPEN row + COMMIT
A runs same query → 11
```

> **Same query/range, different matching rows.**

## Write Skew

```text
A reads shared condition
B reads shared condition

A updates row A
B updates row B

Business invariant breaks
```

> **Different writes, shared decision, broken rule.**

## Lost Update

```text
A reads old value
B reads old value

A writes
B writes

One intended update gets lost
```

> **One concurrent change is overwritten/lost.**

---

# 24. Production Invoice Scenario — Your Handwritten Diagram

This is a very useful real-world example.

Initial:

```text
Product Price = ₹100
```

Transaction 1 is generating an invoice.

```text
T1:
READ Product Price
→ ₹100
```

While T1 is still running:

```text
T2:
UPDATE Product Price
→ ₹200

COMMIT
```

T1 reads again.

## Under Read Committed

```text
T1 first read  → ₹100
T2 commits     → ₹200
T1 second read → ₹200
```

This is a non-repeatable read.

## Under PostgreSQL Repeatable Read

Conceptually:

```text
T1 first read  → ₹100
T2 commits     → ₹200
T1 second read → ₹100
```

The current committed database value can be ₹200 while T1 continues seeing its transaction-consistent snapshot.

---

# 25. Is the Price Change a Bug?

Not automatically.

The senior question is:

> **What does the business require?**

### Requirement A — Price can change freely

Then:

```text
₹100 → ₹200
```

may be expected.

### Requirement B — Order price is locked

Then the order should preserve the agreed price:

```text
orders
----------------
order_id
product_id
agreed_price
quantity
```

The invoice reads `agreed_price`.

This is data modeling, not merely isolation.

Senior lesson:

> **Do not try to solve every business-consistency problem with isolation levels.**

---

# 26. Explicit Transactions

An explicit transaction means the application controls the transaction boundary.

```sql
BEGIN;

UPDATE table_a ...;
UPDATE table_b ...;
INSERT INTO audit_log ...;

COMMIT;
```

If something fails:

```sql
ROLLBACK;
```

The statements are intended to form one transaction.

---

# 27. Autocommit / Implicit Transaction Behavior

With common autocommit behavior:

```text
Statement 1
   ↓
commit

Statement 2
   ↓
commit

Statement 3
   ↓
commit
```

So three statements can become three separate transaction units.

If statement 2 fails, statement 1 may already be committed.

If you need:

```text
A + B + C
```

to succeed or fail together, use an explicit transaction.

### Terminology warning

"Implicit transaction" can mean different things in different databases, drivers, and frameworks.

Do not rely only on the word.

Determine:

1. Is autocommit enabled?
2. When does a transaction begin?
3. When does it commit?
4. What causes rollback?
5. Does the framework automatically manage transactions?

The actual transaction boundary matters more than terminology.

---

# 28. Why Money Transfers Need Explicit Transactions

Suppose:

```text
A = ₹10,000
B = ₹5,000
```

Transfer ₹1,000.

Desired:

```text
A = ₹9,000
B = ₹6,000
```

Bad independent flow:

```text
Debit A
→ COMMIT

Credit B
→ ERROR
```

Possible result:

```text
A = ₹9,000
B = ₹5,000
```

The logical operation is incomplete.

Explicit transaction:

```text
BEGIN
   ↓
Debit A
   ↓
Credit B
   ↓
COMMIT
```

If credit fails:

```text
ROLLBACK
```

Main ACID property:

> **Atomicity — all or nothing.**

---

# 29. Locks — Next Layer

Once isolation phenomena are clear, learn locking.

Example:

```sql
SELECT *
FROM accounts
WHERE id = 42
FOR UPDATE;
```

Conceptually:

> "I need to work with this row; protect it from conflicting concurrent work until my transaction completes."

But do not assume `FOR UPDATE` solves every concurrency problem.

A row lock is not automatically the same as locking every possible future row matching a predicate.

This matters for:

- range queries
- phantom prevention
- write skew
- MVCC
- Serializable isolation

---

# 30. Pessimistic vs Optimistic Concurrency

## Pessimistic Concurrency

Assume conflict is likely.

Lock the data.

```sql
SELECT balance
FROM accounts
WHERE id = 42
FOR UPDATE;
```

Useful when:

- contention is high
- critical section is short
- conflicting updates are expensive
- coordinated access is important

## Optimistic Concurrency

Assume conflicts are relatively rare.

Use a version column.

Initial:

```text
balance = 100
version = 5
```

Update:

```sql
UPDATE accounts
SET balance = 150,
    version = version + 1
WHERE id = 42
  AND version = 5;
```

If another process already changed it:

```text
version = 6
```

The update affects:

```text
0 rows
```

The application detects the conflict and can reload/retry or report a conflict.

---

# 31. Deadlocks

Deadlock occurs when transactions wait for each other in a cycle.

Example:

```text
Transaction A:
locks Account 1
waits for Account 2

Transaction B:
locks Account 2
waits for Account 1
```

Diagram:

```text
A holds 1 → wants 2
B holds 2 → wants 1
```

Neither can continue.

The database must detect/break the deadlock, commonly by aborting one transaction.

---

# 32. Senior Deadlock Rule

> **Acquire multiple locks in a consistent order.**

For example, if updating two accounts:

```text
sort IDs
lowest → highest
```

Then both transactions use:

```text
Account 1
then
Account 2
```

instead of:

```text
A: 1 → 2
B: 2 → 1
```

This reduces circular waiting.

---

# 33. Keep Transactions Short

Avoid:

```text
BEGIN
  DB query
  HTTP API call
  Wait 3 seconds
  CPU-heavy calculation
  Another DB query
COMMIT
```

A transaction can hold:

- database locks
- a connection-pool slot
- snapshots/MVCC resources
- other database resources

while doing unrelated work.

Often prefer:

```text
Do external work
       ↓
Begin transaction
       ↓
Short DB operation
       ↓
Commit
```

The exact design depends on the business operation.

---

# 34. External APIs and Transactions

Avoid assuming a local database transaction can safely include an external service.

Example:

```text
BEGIN

UPDATE order

CALL payment API

COMMIT
```

Problems:

- API is slow
- API times out
- DB connection remains occupied
- locks may remain longer
- external service is not automatically part of the local DB transaction

For distributed workflows, learn:

- Saga
- Outbox Pattern
- Idempotency
- Retry
- Eventual Consistency
- 2PC trade-offs

---

# 35. Senior Code-Review Checklist

When reviewing database-heavy code, ask:

### Transaction boundary

- Where does the transaction start?
- Where does it end?
- Is it unnecessarily long?

### Concurrency

- Can two users execute this code at the same time?
- What happens if they do?

### Reads

- What does each transaction see?
- Can a value change between reads?

### Writes

- Are the same logical rows being updated?
- Can an update be lost?

### Business invariant

- Is there a rule involving multiple rows?
- Could two individually valid decisions break it together?

### Isolation

- What isolation level is active?
- What does this database actually do at that level?

### Locks

- Are locks needed?
- Are they acquired consistently?
- Could they deadlock?

### Retry

- What happens after serialization failure?
- What happens after deadlock?
- Is retry safe/idempotent?

### External calls

- Is an HTTP/API call inside the transaction?

### Batch processing

- Is a huge update happening in one transaction?
- Should the work be chunked?

---

# 36. Scenario-Solving Framework

When someone gives you a production concurrency problem:

## Step 1 — Initial state

```text
A = ON
B = ON
```

## Step 2 — Transaction A reads

```text
A sees B = ON
```

## Step 3 — Transaction B reads

```text
B sees A = ON
```

## Step 4 — Writes

```text
A updates A
B updates B
```

## Step 5 — Did they overlap?

```text
YES
```

## Step 6 — Same row or different rows?

Same logical row:

```text
Investigate write-write conflicts/lost update.
```

Different rows:

```text
Investigate shared business invariant/write skew.
```

## Step 7 — Final state

```text
A = OFF
B = OFF
```

## Step 8 — Business rule

```text
At least one must be ON
```

Broken.

## Step 9 — Possible solution

Depending on the actual requirement:

- stronger isolation
- explicit locking
- optimistic concurrency
- atomic SQL operation
- schema/data-model redesign
- application retry

---

# 37. Interview Scenario 1 — Dirty Read

### Interviewer

Transaction A changes an account:

```text
₹1,000 → ₹500
```

but does not commit.

Transaction B reads:

```text
₹500
```

A then rolls back.

### Expected answer

> "This is a dirty read. B read a value written by A before A committed. A rolled back, so ₹500 never became the committed final value."

---

# 38. Interview Scenario 2 — Read Committed

A reads:

```text
₹1,000
```

B changes:

```text
₹1,000 → ₹800
COMMIT
```

A reads again under Read Committed.

### Answer

```text
₹800
```

The same row returned a different committed value.

Phenomenon:

> **Non-Repeatable Read**

---

# 39. Interview Scenario 3 — Repeatable Read

A reads:

```text
₹1,000
```

B changes:

```text
₹1,000 → ₹800
COMMIT
```

A reads again under PostgreSQL Repeatable Read.

### Answer

```text
₹1,000
```

A continues seeing its transaction-consistent snapshot.

---

# 40. Interview Scenario 4 — Phantom Read

A:

```sql
SELECT COUNT(*)
FROM orders
WHERE status = 'PENDING';
```

Result:

```text
10
```

B inserts another pending order and commits.

A runs the same query and gets:

```text
11
```

### Answer

> **Phantom Read**

Because the set of matching rows changed.

---

# 41. Interview Scenario 5 — Write Skew

Two doctors:

```text
A = ON
B = ON
```

Rule:

```text
At least one must remain ON.
```

A sees B ON and turns A OFF.

B sees A ON and turns B OFF.

Both commit.

### Expected answer

```text
A = OFF
B = OFF
```

The business invariant is broken.

Phenomenon:

> **Write Skew**

Reason:

> Both transactions made decisions from shared information but updated different rows.

---

# 42. Interview Scenario 6 — Lost Update

Initial:

```text
Quantity = 5
```

A reads 5.

B reads 5.

A writes 6.

B writes 7.

### Expected answer

> "This can be a lost-update scenario because both operations worked from the same old value and one intended change was overwritten."

Possible protections:

- pessimistic locking
- optimistic version checking
- atomic SQL update
- appropriate concurrency control

---

# 43. Interview Scenario 7 — Expected or Bug?

A user sees:

```text
Product price = ₹999
```

Another process changes it:

```text
₹999 → ₹1,049
COMMIT
```

A later sees:

```text
₹1,049
```

### Expected answer

> "Not automatically a bug. It depends on the business requirement. If prices can change, this may be expected. If the price was promised/locked after checkout, the application needs to preserve and enforce that agreed price."

This demonstrates developer thinking.

---

# 44. Interview Scenario 8 — Serializable

Two transactions execute the doctor write-skew scenario under Serializable.

### Expected answer

> "Serializable semantics should prevent the database from silently accepting an execution that cannot be equivalent to a valid serial order. One transaction may be rejected with a serialization failure or otherwise prevented from producing the invalid result. The application should handle retryable serialization failures where appropriate."

---

# 45. Questions to Ask During a Production Incident

When someone says:

> "Sometimes two users get inconsistent results."

Ask:

```text
1. Are there concurrent transactions?
2. What is the exact initial state?
3. What does Transaction A read?
4. What does Transaction B read?
5. Which transaction commits first?
6. Was any uncommitted data read?
7. Is the same row read twice?
8. Is a range/set queried twice?
9. Are different rows updated?
10. Is there a business invariant?
11. Can an update be lost?
12. What isolation level is active?
13. Which database engine is used?
14. What locks are acquired?
15. Could there be a deadlock?
16. Could there be a serialization failure?
17. Is retry implemented?
18. Is the operation idempotent?
19. Does the data model preserve the business fact?
20. Is the observed behavior actually expected?
```

---

# 46. How Your Automation-Testing Background Helps

Your existing testing mindset is an advantage.

You already think:

```text
Given
When
Then
```

Apply the same model to concurrency.

Example:

```text
GIVEN:
Doctor A and B are ON

WHEN:
A and B execute concurrently

THEN:
A sees B ON
B sees A ON

AND:
A turns OFF
B turns OFF

EXPECTED:
At least one remains ON

ACTUAL:
Both are OFF
```

That is developer-level concurrency reasoning.

---

# 47. One-Line Memory Sheet

```text
DIRTY READ
= Read uncommitted data

NON-REPEATABLE READ
= Same row, different value

PHANTOM READ
= Same query/range, different matching rows

WRITE SKEW
= Shared condition + different writes + broken invariant

LOST UPDATE
= One concurrent change gets overwritten/lost

READ UNCOMMITTED
= Weakest conceptual isolation; dirty reads may be possible

READ COMMITTED
= Do not read uncommitted changes; repeated reads may change

REPEATABLE READ
= Repeated reads remain consistent according to DB semantics

SERIALIZABLE
= Result behaves as if transactions were executed serially
```

---

# 48. The Next Learning Sequence

Do not jump straight into microservices.

Recommended order:

```text
1. Transactions
      ↓
2. ACID
      ↓
3. Isolation levels
      ↓
4. Dirty Read
      ↓
5. Non-Repeatable Read
      ↓
6. Phantom Read
      ↓
7. Write Skew
      ↓
8. Lost Update
      ↓
9. MVCC
      ↓
10. Locks
      ↓
11. SELECT FOR UPDATE
      ↓
12. Deadlocks
      ↓
13. Optimistic Concurrency
      ↓
14. Serializable + Retry
      ↓
15. Transaction boundaries
      ↓
16. Batch transactions
      ↓
17. Outbox Pattern
      ↓
18. Saga
      ↓
19. Idempotency
      ↓
20. Distributed consistency
```

### Why MVCC is next

A key question from our learning was:

> "How can Transaction A still see ₹2,000 when Transaction B has already committed ₹3,000?"

MVCC/snapshots explain this behavior.

Once MVCC is clear, Read Committed, Repeatable Read, snapshots, visibility, and many real PostgreSQL behaviors become much easier to understand.

---

# 49. Mentor Rule

Whenever you face a transaction question:

**Do not answer from the isolation-level name alone.**

Draw:

```text
             TIME ↓

Transaction A          Transaction B

BEGIN
READ
                       BEGIN
                       UPDATE
                       COMMIT
READ AGAIN
COMMIT
```

Then reason:

> **What did A see at each point?**

That one habit is the foundation for production-level transaction debugging and senior developer interview reasoning.
