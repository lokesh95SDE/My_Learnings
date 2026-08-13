<div align="center">

# ☕ Spring Boot — Industry-Level Learning Material

### From Student Notes to Senior Engineer & SDET Interview Mastery

[![Java](https://img.shields.io/badge/Java-17%2B-ED8B00?style=for-the-badge&logo=openjdk&logoColor=white)](https://openjdk.org/)
[![Spring Boot](https://img.shields.io/badge/Spring_Boot-3.x-6DB33F?style=for-the-badge&logo=springboot&logoColor=white)](https://spring.io/projects/spring-boot)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen?style=for-the-badge)](CONTRIBUTING.md)

> **Audience:** Senior Java Backend Engineers · Senior SDETs · Spring Boot Architects  
> **Goal:** Deep, interview-ready mastery — not just syntax, but *internals*, *production thinking*, and *design decisions*

</div>

---

## 📚 Table of Contents

| # | Topic | Key Concepts |
|---|-------|-------------|
| 1 | [Spring Boot & Auto-Configuration](#1-spring-boot--auto-configuration) | `@SpringBootApplication` · `@ConditionalOn*` · `spring.factories` |
| 2 | [Beans, Dependency Injection & IoC](#2-beans-dependency-injection--ioc) | `@Component` · `@Autowired` · `@Qualifier` · Bean Lifecycle |
| 3 | [Spring Web MVC & REST API Design](#3-spring-web-mvc--rest-api-design) | `DispatcherServlet` · HTTP Methods · Stateless vs Stateful |
| 4 | [Spring Data JPA, Hibernate & ORM](#4-spring-data-jpa-hibernate--orm) | `@Entity` · Fetch Types · N+1 Problem · Cascading · `@Lock` · Pessimistic Locking |
| 5 | [DTOs, Specification API & Pagination](#5-dtos-specification-api--pagination) | DTO Pattern · Criteria API · `Pageable` · Sorting |
| 6 | [Exception Handling & Validation](#6-exception-handling--validation) | `@RestControllerAdvice` · `@Valid` · Bean Validation |
| 7 | [Spring Security — Authentication & Authorization](#7-spring-security--authentication--authorization) | BCrypt · JWT · `SecurityFilterChain` · `@PreAuthorize` |
| 8 | [Caching Strategies](#8-caching-strategies) | `@Cacheable` · Redis · LRU · TTL · Cache Patterns |
| 9 | [Reactive Programming, WebClient & WebFlux](#9-reactive-programming-webclient--webflux) | `Mono` · `Flux` · Event Loop · Parallel Calls |
| 10 | [Multithreading, Concurrency & CompletableFuture](#10-multithreading-concurrency--completablefuture) | Race Conditions · `AtomicInteger` · `CompletableFuture` |
| 11 | [JVM Internals, Memory & Garbage Collection](#11-jvm-internals-memory--garbage-collection) | Heap Regions · GC Algorithms · Heap Sizing |
| 12 | [Spring Actuator & Production Monitoring](#12-spring-actuator--production-monitoring) | Health · Metrics · Prometheus · Grafana |
| 13 | [Testing in Spring Boot](#13-testing-in-spring-boot) | `@WebMvcTest` · `@DataJpaTest` · `@SpringBootTest` |
| 14 | [Master Cheat Sheet](#14-master-cheat-sheet--interview-quick-reference) | All Annotations · HTTP Codes · Top 20 Interview Topics |
| 15 | [Practice Exercises](#15-practice-exercises) | Beginner → Advanced → Production Scenarios |

---

## 1. Spring Boot & Auto-Configuration

### What Is It?
Spring Boot is an opinionated framework that eliminates manual setup by **automatically configuring components** based on what's present in your classpath. The three pillars are:

```
Embedded Server  +  Auto-Configuration  +  Production-ready Defaults
```

### How Auto-Configuration Works Internally

```
@SpringBootApplication
        │
        ├── @Configuration          → Marks class as bean factory
        ├── @ComponentScan          → Scans for @Component, @Service, @Repository
        └── @EnableAutoConfiguration
                    │
                    └── SpringFactoriesLoader reads:
                        META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
                                    │
                                    ├── DataSourceAutoConfiguration
                                    │       └── @ConditionalOnClass(DataSource.class)
                                    ├── DispatcherServletAutoConfiguration
                                    │       └── @ConditionalOnWebApplication
                                    └── JpaRepositoriesAutoConfiguration
                                                └── @ConditionalOnMissingBean(JpaRepository.class)
```
#### Complete Mental Model
```
Start Application
        │
        ▼
Read @SpringBootApplication
        │
        ▼
Component Scan
        │
        ▼
Register Controller
Register Service
Register Repository
        │
        ▼
Look at classpath
        │
        ├── Is Spring MVC present?
        │        └── Configure DispatcherServlet
        │
        ├── Is JPA present?
        │        └── Configure EntityManager & DataSource
        │
        ├── Is Redis present?
        │        └── Configure RedisTemplate
        │
        ├── Is Kafka present?
        │        └── Configure KafkaTemplate
        │
        ▼
Before creating each bean:
"Did the user already define one?"
        │
        ├── Yes → Use the user's bean
        └── No  → Create the default bean
        │
        ▼
Embedded Tomcat starts
        │
        ▼
Application Ready
```

```java
// Minimal Spring Boot application
@SpringBootApplication
public class LmsApplication {
    public static void main(String[] args) {
        SpringApplication.run(LmsApplication.class, args);
    }
}
```

### Key @Conditional Annotations

| Annotation | Activates Bean When... |
|---|---|
| `@ConditionalOnClass(X.class)` | Class X is on the classpath |
| `@ConditionalOnMissingBean` | No bean of that type is already defined |
| `@ConditionalOnProperty("key")` | Property exists/has specific value in config |
| `@ConditionalOnWebApplication` | App is a web (servlet) application |

### Best Practices
- ✅ Use `--debug` flag to see the **Conditions Report** and know exactly which auto-configs activated
- ✅ Exclude unwanted configs: `@SpringBootApplication(exclude = {DataSourceAutoConfiguration.class})`
- ✅ Use `spring-boot-starter-*` parents — they manage compatible dependency versions for you
- ✅ Externalize all config to `application.properties` / `application.yml`

### 💡 Memory Trick
> **"Boot = Build Fast, Start Fast"**  
> `@SpringBootApplication` = **C**onfigure + **E**nable + **S**can → **"CES"**  
> *"Spring reads your classpath like an ingredient list and auto-cooks what it can."*

### 🎯 Interview Questions
<details>
<summary>Click to expand</summary>

**Basic**
- What is the difference between Spring and Spring Boot?
- What does `@SpringBootApplication` do internally?

**Intermediate**
- How does `@ConditionalOnClass` work? Give a real example.
- How do you disable a specific auto-configuration?

**Advanced**
- Your app starts and an unwanted `DataSource` bean is created. How do you diagnose and fix it?
- Explain the order of bean creation when auto-config competes with user-defined beans.
          <details>
          <summary>Click for Answer</summary>
              
            🟢 [1] DatabaseConnectionPool created — no dependencies
            🟢 [2] CourseService created — depends on DatabaseConnectionPool
            🟢 [3] EnrollmentController created — depends on CourseService
              
            EnrollmentController (User Bean A)
            ↓ depends on
            CourseService (Auto-config Bean B)
            ↓ depends on
            DatabaseConnectionPool (User Bean C)
          
            Registration (scanning) order:    A  →  C  →  B
            ↓     ↓     ↓
            Creation (instantiation) order:   3rd   1st   2nd
            ↑     ↑     ↑
            needs B  root  needs C
          </details>
- How does Spring Boot 3.x change auto-configuration vs 2.x?

</details>

---

## 2. Beans, Dependency Injection & IoC

### What Is a Spring Bean?
A **Bean** is any Java object whose **full lifecycle** — creation, dependency wiring, initialization, and destruction — is managed by the Spring IoC container instead of the developer using `new`.

### Dependency Injection Types

| Type | Mechanism | Recommended? | Why |
|---|---|---|---|
| **Constructor** | `@Autowired` on constructor (implicit in Spring 4.3+) | ✅ **Always preferred** | Immutable, testable, explicit |
| **Setter** | `@Autowired` on setter | ⚠️ Optional dependencies only | Allows partial initialization |
| **Field** | `@Autowired` on field | ❌ Avoid in production | Hides deps, breaks unit tests |

```java
// ❌ Tight Coupling — Traditional Java
public class Car {
    private Engine engine = new DieselEngine(); // hardcoded
}

// ✅ Loose Coupling — Spring DI with Constructor Injection
@Component
public class Car {
    private final Engine engine;

    @Autowired // Spring injects the correct Engine implementation
    public Car(@Qualifier("dieselEngine") Engine engine) {
        this.engine = engine;
    }
}
```

### Key Bean Annotations

| Annotation | Layer | One-Line Purpose |
|---|---|---|
| `@Component` | Any | Generic Spring-managed bean — *"Spring owns it"* |
| `@Service` | Service | Business logic — *"Business Brain"* |
| `@Repository` | Data | DB access + exception translation — *"DB Gatekeeper"* |
| `@RestController` | Web | `@Controller` + `@ResponseBody` — *"API Mouth"* |
| `@Configuration` | Config | Java-based bean factory — *"Factory Blueprint"* |
| `@Qualifier("name")` | Any | Select specific bean when multiple exist |
| `@Primary` | Any | Default bean when multiple exist |
| `@Scope("prototype")` | Any | New instance per injection point |
| `@Profile("prod")` | Any | Activate bean for specific environment |

### Bean Lifecycle

```
1. @Component scanned → BeanDefinition created
2. Constructor called → Bean instantiated
3. @Autowired resolved → Dependencies injected
4. @PostConstruct → Custom init logic runs
5. ✅ Bean ready for use
6. @PreDestroy → Cleanup logic runs on shutdown
7. GC → Bean collected
```

```java
@Service
public class LearnerService {
    private final LearnerRepository repo;

    public LearnerService(LearnerRepository repo) { // Constructor injection
        this.repo = repo;
    }

    @PostConstruct
    public void init() { log.info("LearnerService initialized"); }

    @PreDestroy
    public void cleanup() { log.info("LearnerService shutting down"); }
}
```



### ⚠️ `@Value` Injection Timing — Common Interview Trap

One of the most common Spring mistakes is assuming that `@Value` is available everywhere. Spring injects `@Value` **after** the bean is constructed.

#### ❌ Mistake 1: Using `@Value` in a Static Context

```java
@Component
public class PaymentConfig {

    @Value("${payment.api.key}")
    private static String apiKey;

    public static String getApiKey() {
        return apiKey;   // null
    }
}
```

**Why?**
- Static fields belong to the class, not a Spring bean instance.
- Spring cannot inject static fields.

#### ❌ Mistake 2: Using `@Value` Inside the Constructor

```java
@Component
public class NotificationService {

    @Value("${notification.url}")
    private String url;

    public NotificationService() {
        System.out.println(url);   // null
    }
}
```

**Why does this happen?**

- Constructor executes first.
- Then Spring injects `@Value` and `@Autowired`.
- Finally `@PostConstruct` runs.

```
Constructor
    ↓
Object Created
    ↓
@Value / @Autowired Injection
    ↓
@PostConstruct
    ↓
Bean Ready
```

### ✅ Better Approach 1 — `@PostConstruct`

```java
@PostConstruct
public void init() {
    System.out.println(url);
}
```

### ✅ Better Approach 2 — Constructor Injection (Recommended)

```java
@Component
public class PaymentConfig {

    private final String apiKey;

    public PaymentConfig(@Value("${payment.api.key}") String apiKey) {
        this.apiKey = apiKey;
    }
}
```

> **Memory Trick:** Constructor → Injection → `@PostConstruct` → Ready.

### Common Mistake ❌
```
WARNING: expected single matching bean but found 2: dieselEngine, petrolEngine
```
> Caused by injecting `Engine` (parent type) when two child beans exist.  
> Fix: Add `@Qualifier("dieselEngine")` at the injection point — you do **not** have to put it on both implementing classes.

### ⚠️ Production Warning
> **Singleton beans are shared across all threads.**  
> NEVER store mutable per-request state in singleton fields — this causes race conditions in production.  
> Field injection (`@Autowired` on field) breaks unit testing without a Spring context — always use constructor injection.

### 💡 Memory Tricks
> - `"DI = Don't Instantiate Inside — let Spring deliver the object."`
> - `"IoC = I Own Control — Spring says that, not your code."`
> - **Singleton** = *"One ring to rule them all."* | **Prototype** = *"Fresh copy every time."*

### 🎯 Interview Questions
<details>
<summary>Click to expand</summary>

**Basic**
- What is the difference between `@Component`, `@Service`, and `@Repository`?
- What is the default bean scope in Spring?

**Intermediate**
- What happens when two beans of the same type exist without `@Primary` or `@Qualifier`?
- How does Spring handle circular dependencies?

**Advanced**
- A `@Singleton` bean holds a counter variable. 100 threads hit it simultaneously. What happens?
- What is `BeanPostProcessor` and how is it used internally?

</details>

---

## 3. Spring Web MVC & REST API Design

### Complete Request Lifecycle

```
Client (Browser / Mobile / API Consumer)
    │  HTTP Request: GET /learners/1
    ▼
Embedded Tomcat (port 8080)
    ▼
DispatcherServlet  ──── Front Controller, single entry point
    │  Delegates to HandlerMapping
    ▼
HandlerMapping  ──── Finds matching @GetMapping("/learners/{id}")
    ▼
HandlerAdapter  ──── Invokes Controller method
    │  JSON Deserialization via Jackson (Unmarshalling)
    ▼
@RestController method
    ▼
@Service  ──── Business logic
    ▼
@Repository  ──── Spring Data JPA
    ▼
Database  ──── SQL via Hibernate
    │  Entity returned
    ▼
Service maps Entity → DTO
    │  JSON Serialization via Jackson (Marshalling)
    ▼
HTTP Response 200 OK  {JSON body}
```

### HTTP Methods Quick Reference

| Annotation | Method | Idempotent? | Use Case |
|---|---|---|---|
| `@GetMapping` | GET | ✅ Yes | Fetch — **must NOT alter state** |
| `@PostMapping` | POST | ❌ No | Create — return the created resource |
| `@PutMapping` | PUT | ✅ Yes | Full update |
| `@PatchMapping` | PATCH | ✅ Yes | Partial update |
| `@DeleteMapping` | DELETE | ✅ Yes | Remove resource |

### Stateless vs Stateful

| Property | Stateless | Stateful |
|---|---|---|
| Server memory | None — every request is independent | Server remembers session |
| Load balancing | Any server handles any request | Sticky Load Balancer required |
| Scalability | Horizontally scales easily | Complex — needs session replication |
| Spring impl | Spring Security + JWT | `HttpSession` + `JSESSIONID` cookie |
| Example | REST APIs with JWT | Banking portals |

### REST API Best Practices ✅
- Resources are **nouns**, not verbs: `/learners` ✅ vs `/getLearners` ❌
- `GET` must always be **idempotent** — never alters DB state
- `POST` must be **reflective** — return the newly created resource
- Use correct HTTP status codes: `201 Created`, `400 Bad Request`, `404 Not Found`
- Always use **DTOs** in responses — never expose raw JPA entities
- **Version your API**: `/api/v1/learners`

### 🎯 Interview Questions
<details>
<summary>Click to expand</summary>

- What is the role of `DispatcherServlet`?
- What is the difference between `@Controller` and `@RestController`?
- What is marshalling and unmarshalling in Spring MVC?
- How does Spring handle content negotiation (JSON vs XML)?
- What is the difference between `@RequestParam`, `@PathVariable`, and `@RequestBody`?

</details>

### 🎯 Interview Answers
<details>
<summary>Click to expand</summary>

- `DispatcherServlet` is the traffic cop of Spring MVC — it receives every request, figures out where it needs to go, executes the handler and orchestrates the response, all while keeping controllers focused purely on business logic.
- `@Controller` → Returns a view (HTML/JSP/Thymeleaf) for rendering web pages.
  `@RestController` → Returns data (typically JSON/XML) directly in the HTTP response body for REST APIs.
- Spring uses `ContentNegotiationManager` to determine the desired response format by checking the Accept header (e.g., application/json vs application/xml), a format query parameter, or a path extension. It then selects the appropriate HttpMessageConverter (like MappingJackson2HttpMessageConverter for JSON or Jaxb2RootElementHttpMessageConverter for XML) to serialize the @ResponseBody return value before writing it to the HTTP response.


</details>
---

## 4. Spring Data JPA, Hibernate & ORM

### The Layer Stack

```
Spring Data JPA  ──── Top abstraction layer (generates queries from method names)
        │
        JPA (Jakarta Persistence API)  ──── Specification / interface
        │
        Hibernate  ──── ORM Implementation
        │
        JDBC  ──── Raw Java-to-database wire protocol
        │
        Database
```

> 💡 *"JPA = spec, Hibernate = impl, Spring Data JPA = top layer that generates the impl for you."*

### Fetch Types — Critical for Production

| Association | Default | Loaded When | Risk |
|---|---|---|---|
| `@OneToMany` | **LAZY** | Only when accessed | `LazyInitializationException` outside transaction |
| `@ManyToMany` | **LAZY** | Only when accessed | Same risk |
| `@ManyToOne` | **EAGER** | Always with parent | N+1 query problem in collections |
| `@OneToOne` | **EAGER** | Always with parent | Unexpected JOINs in every query |

### Relationship Rules (Refined from Class Notes)

```java
// @ManyToOne / @OneToMany — Course → Cohort
@Entity
public class Course {
    @OneToMany(mappedBy = "course", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<Cohort> cohorts = new ArrayList<>();
}

@Entity
public class Cohort {
    @ManyToOne(fetch = FetchType.LAZY)  // Many-side ALWAYS owns the FK column
    @JoinColumn(name = "course_id")
    private Course course;
}

// @ManyToMany — Cohort owns the join table
@Entity
public class Cohort {
    @ManyToMany
    @JoinTable(
        name = "cohort_learners",
        joinColumns = @JoinColumn(name = "cohort_id"),
        inverseJoinColumns = @JoinColumn(name = "learner_id")
    )
    private List<Learner> learners = new ArrayList<>();
}

@Entity
public class Learner {
    @ManyToMany(mappedBy = "learners")
    @JsonIgnore  // Prevent circular JSON serialization
    private List<Cohort> cohorts = new ArrayList<>();
}
```

### JPA Relationship Rules Summary
1. In `@ManyToOne` / `@OneToMany` — the **Many-side (Cohort)** always owns the FK column in DB
2. `@OneToMany` on the Course side is always a **back-reference** using `mappedBy`
3. For `@ManyToMany` — pick one owner, use `@JoinTable` there; the other uses `mappedBy`
4. **Law of Demeter**: Don't shortcut `Course → Learner`; traverse `Course → Cohort → Learner`

### Circular Reference Fix (from Class Notes)

| Annotation | Effect |
|---|---|
| `@JsonIgnore` | Completely omits the field from JSON |
| `@JsonManagedReference` / `@JsonBackReference` | Handles parent/child direction automatically |
| `@JsonIdentityInfo` | Serializes as ID on second occurrence — preserves full graph |

### Pessimistic Locking — `@Lock` & `@QueryHints`

When multiple transactions compete for the same database row simultaneously (e.g., two users booking the last available parking spot), optimistic locking may not be enough. **Pessimistic locking** acquires an exclusive database lock at the moment of the `SELECT`, so no other transaction can touch that row until the first one commits or rolls back.

#### `@Lock(LockModeType.PESSIMISTIC_WRITE)`

```java
public interface ParkingSlotRepository
    extends JpaRepository<ParkingSlot, Long>, JpaSpecificationExecutor<ParkingSlot> {

    // Lock the selected row immediately — no other transaction can acquire a write lock
    // until this transaction completes. Generates: SELECT ... FOR UPDATE
    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @QueryHints(@QueryHint(
        name  = "jakarta.persistence.lock.timeout",
        value = "3000"  // Wait up to 3 seconds for the lock; fail-fast beyond that
    ))
    @Query("SELECT s FROM ParkingSlot s WHERE s.status = 'AVAILABLE' ORDER BY s.id ASC")
    List<ParkingSlot> findAvailableSlotWithLock(Pageable pageable);
}
```

```java
// Caller — request only 1 row instead of loading the full list
@Transactional
public ParkingSlot reserveSlot() {
    // PageRequest.of(0, 1) = "give me exactly 1 row" — DB-level LIMIT 1
    List<ParkingSlot> slots = repository.findAvailableSlotWithLock(PageRequest.of(0, 1));
    if (slots.isEmpty()) throw new NoSlotAvailableException();

    ParkingSlot slot = slots.get(0);
    slot.setStatus("RESERVED");
    return repository.save(slot); // Lock released on transaction commit
}
```

#### What Each Part Does

| Component | What It Does | Why It Matters |
|---|---|---|
| `@Lock(PESSIMISTIC_WRITE)` | Acquires a DB write lock on every selected row | Prevents two transactions from grabbing the same row simultaneously — generates `SELECT ... FOR UPDATE` |
| `@QueryHints(lock.timeout = 3000)` | Tells the DB to wait up to 3 seconds for the lock | Avoids indefinite blocking; blocked requests fail fast with a `LockTimeoutException` instead of hanging |
| `Pageable pageable` with `PageRequest.of(0, 1)` | Adds `LIMIT 1` to the SQL query | Fetches only the **one** row you actually need — no memory waste loading a full list when you use only the first result |

#### Optimistic vs Pessimistic Locking

| | Optimistic (`@Version`) | Pessimistic (`@Lock`) |
|---|---|---|
| **How** | Version column checked on UPDATE | DB-level row lock on SELECT |
| **Blocks other readers?** | No | Yes (PESSIMISTIC_WRITE) |
| **Failure mode** | `OptimisticLockException` on commit collision | `LockTimeoutException` if lock wait exceeded |
| **Best for** | Low-contention data, read-heavy systems | High-contention critical sections (seat booking, parking, inventory) |
| **Performance** | Higher throughput — no blocking | Lower throughput under heavy contention |

#### ⚠️ Production Nuances

> - `lock.timeout` support **varies by database**. It is reliable on PostgreSQL and Oracle, but behaves differently on MySQL (may be ignored in some modes) and H2 (in-memory). Always test locking behaviour against your **actual production database**, not only H2.
> - `@Lock` requires an active `@Transactional` context — the lock is held until the transaction commits or rolls back. Calling a `@Lock` repository method outside a transaction will throw an exception.
> - Keep locked transactions **as short as possible** — long-running transactions holding `FOR UPDATE` locks are a top cause of production deadlocks and connection pool exhaustion.
> - Combine with a **connection pool timeout** (`spring.datasource.hikari.connection-timeout`) so the entire request fails fast rather than exhausting the pool waiting for a lock.

#### 💡 Memory Trick
> **"Pessimistic = Assume the worst — grab the lock before you even look at the data."**  
> **"Optimistic = Assume the best — read freely, but verify no one changed it before you save."**  
> **"`@Lock` = Bouncer at the door. `@Version` = Bouncer who checks your ticket at checkout."**

### ⚠️ Production Warnings
> **`LazyInitializationException`** — Occurs when a LAZY association is accessed after the JPA session (transaction) closes.  
> Fix: Use `@Transactional`, or `JOIN FETCH` in JPQL, or DTO projections.
>
> **N+1 Problem** — Loading 100 orders then accessing `order.getCustomer()` generates 101 queries.  
> Fix: `@EntityGraph` or `JOIN FETCH`.
>
> **`CascadeType.REMOVE` on `@ManyToMany`** — Can accidentally delete shared entities (a Learner in multiple Cohorts).

### 💡 Memory Tricks
> - `"@ManyToOne owns the FK — the many-side always holds the key in the real table."`
> - `"LAZY = I'll get it when you ask. EAGER = I bring it every time, wanted or not."`
> - `"Cascade = parenting — what happens to parent happens to child."`

### 🎯 Interview Questions
<details>
<summary>Click to expand</summary>

**Basic**
- What is the difference between JPA and Hibernate?
- Explain the difference between LAZY and EAGER loading.

**Intermediate**
- What is the N+1 problem and how do you solve it?
- Explain `LazyInitializationException` and how to prevent it.

**Advanced**
- How does Hibernate's first-level cache differ from the second-level cache?
- How does Spring Data JPA generate query implementations at startup?
- What is the difference between `PESSIMISTIC_WRITE` and `PESSIMISTIC_READ` lock modes?
- Why should you use `PageRequest.of(0, 1)` instead of fetching a full list when you only need one row?
- A `@Lock` query works fine on H2 in tests but behaves unexpectedly in production PostgreSQL. What is the likely cause?

</details>


### 🎯 Interview Answers
<details>
<summary>Click to expand</summary>

Here are concise answers to all your JPA/Hibernate questions, organized by level:

---

## **Intermediate**

### 1. JPA vs Hibernate

| JPA | Hibernate |
|-----|-----------|
| **Specification** (Java Persistence API) — defines interfaces and rules | **Implementation** of JPA — the actual engine |
| `javax.persistence.*` or `jakarta.persistence.*` packages | `org.hibernate.*` packages |
| `EntityManager`, `Query`, `TypedQuery` | `Session`, `SessionFactory`, `CriteriaBuilder` |
| Portable across providers (EclipseLink, OpenJPA, etc.) | Hibernate-specific features (HQL, `@Formula`, `@Filter`, `Session`) |

> **Analogy:** JPA is the **electrical outlet standard**; Hibernate is **one brand of socket** that follows it (with extra features).

```java
// JPA (portable)
@PersistenceContext
private EntityManager em;

// Hibernate-specific (non-portable)
Session session = em.unwrap(Session.class);
session.enableFilter("activeOnly");
```

---

### 2. LAZY vs EAGER Loading

| LAZY | EAGER |
|------|-------|
| Data loaded **on demand** when accessed | Data loaded **immediately** with parent |
| `FetchType.LAZY` (default for `@OneToMany`, `@ManyToMany`) | `FetchType.EAGER` (default for `@OneToOne`, `@ManyToOne`) |
| Better performance — loads only what's needed | Risk of loading massive object graphs unintentionally |

```java
@Entity
public class Department {
    @OneToMany(mappedBy = "department", fetch = FetchType.LAZY)
    private List<Employee> employees;  // Loaded only when getEmployees() called
}

@Entity
public class Employee {
    @ManyToOne(fetch = FetchType.EAGER)  // Department loaded WITH employee
    private Department department;
}
```

> **Rule of thumb:** Prefer LAZY. EAGER is the root cause of most performance issues.

---

## **Advanced**

### 3. N+1 Problem & Solutions

**Problem:** 1 query fetches N parents, then N additional queries fetch children.

```java
// ❌ N+1: 1 query for departments + N queries for employees
List<Department> depts = deptRepo.findAll();  // Query 1
for (Department d : depts) {
    d.getEmployees().size();  // Query 2, 3, 4... N+1
}
```

**Solutions:**

| Solution | How | When |
|----------|-----|------|
| `JOIN FETCH` | `SELECT d FROM Department d JOIN FETCH d.employees` | When you ALWAYS need children |
| `@EntityGraph` | `@EntityGraph(attributePaths = "employees")` | Reusable, flexible |
| `BatchSize` | `@BatchSize(size = 50)` | When you need children for SOME parents |

```java
// ✅ JOIN FETCH — single query
@Query("SELECT d FROM Department d JOIN FETCH d.employees")
List<Department> findAllWithEmployees();

// ✅ EntityGraph
@EntityGraph(attributePaths = {"employees", "employees.manager"})
List<Department> findAll();
```

---

### 4. LazyInitializationException & Prevention

**Cause:** Accessing a LAZY association **outside a transaction/session**.

```java
// ❌ Session closed — proxy can't load data
@Transactional
public List<Employee> getEmployees() {
    Department dept = deptRepo.findById(1L);  // dept attached to session
    return dept.getEmployees();  // OK — still in transaction
}

// Later, in controller:
dept.getEmployees().get(0).getName();  // 💥 LazyInitializationException!
```

**Prevention:**

| Approach | Code |
|----------|------|
| **Open Session in View** | `spring.jpa.open-in-view=true` (anti-pattern, avoid in production) |
| **Fetch within transaction** | Use `JOIN FETCH` or `@EntityGraph` in service layer |
| **DTO projection** | `SELECT new EmployeeDto(e.id, e.name) FROM Employee e` |
| **Map to DTO inside tx** | Convert to DTO before returning from `@Transactional` method |

```java
// ✅ Best practice: fetch everything needed inside transaction
@Transactional(readOnly = true)
public DepartmentDto getDepartmentWithEmployees(Long id) {
    Department dept = deptRepo.findByIdWithEmployees(id);  // JOIN FETCH
    return new DepartmentDto(dept);  // DTO has all data, no proxies
}
```

---

### 5. First-Level vs Second-Level Cache

| First-Level Cache | Second-Level Cache |
|-------------------|-------------------|
| **Session/EntityManager** scope | **SessionFactory/JPA** scope — shared across sessions |
| Enabled **by default** | Must enable explicitly (`@EnableCaching`, `hibernate.cache.use_second_level_cache=true`) |
| Tracks entities within ONE transaction | Survives transaction boundaries |
| Cleared when session closes | Requires cache provider (Ehcache, Caffeine, Redis) |

```java
// First-level: automatic
EntityManager em = emf.createEntityManager();
Employee e1 = em.find(Employee.class, 1L);  // DB hit
Employee e2 = em.find(Employee.class, 1L);  // Cache hit — no DB query!

// Second-level: needs config + @Cacheable
@Entity
@Cacheable
@org.hibernate.annotations.Cache(usage = CacheConcurrencyStrategy.READ_WRITE)
public class Employee { }
```

---

### 6. How Spring Data JPA Generates Query Implementations

At startup, Spring creates **proxy implementations** dynamically:

```
1. Scans interfaces extending JpaRepository
2. Parses method names (Query Derivation)
   findByLastNameAndActiveTrue → WHERE lastName = ? AND active = true
3. Or uses @Query annotation directly
4. Generates JDK Dynamic Proxy or CGLIB subclass at runtime
5. Injects EntityManager into proxy
```

```java
public interface UserRepository extends JpaRepository<User, Long> {
    // Spring parses method name and generates:
    // SELECT u FROM User u WHERE u.lastName = ?1 AND u.active = true
    List<User> findByLastNameAndActiveTrue(String lastName);
    
    // Or uses explicit query
    @Query("SELECT u FROM User u WHERE u.email = :email")
    Optional<User> findByEmail(@Param("email") String email);
}
```

> The actual implementation class is generated at runtime — you never write it.

---

### 7. PESSIMISTIC_WRITE vs PESSIMISTIC_READ

| Mode | Lock Type | Use Case |
|------|-----------|----------|
| `PESSIMISTIC_READ` | Shared lock (others can read, not write) | Prevent dirty reads, allow concurrent reads |
| `PESSIMISTIC_WRITE` | Exclusive lock (no one else can read or write) | Critical updates — inventory, balance deduction |

```java
@Lock(LockModeType.PESSIMISTIC_WRITE)
@Query("SELECT a FROM Account a WHERE a.id = :id")
Optional<Account> findByIdForUpdate(@Param("id") Long id);

// Usage:
@Transactional
public void transfer(Long fromId, Long toId, BigDecimal amount) {
    Account from = accountRepo.findByIdForUpdate(fromId).orElseThrow();  // Locked!
    Account to = accountRepo.findByIdForUpdate(toId).orElseThrow();      // Locked!
    from.debit(amount);
    to.credit(amount);
}  // Locks released on commit/rollback
```

> `PESSIMISTIC_WRITE` is what you use for **"SELECT FOR UPDATE"** in SQL.

---

### 8. `PageRequest.of(0, 1)` vs Full List

```java
// ❌ Loads ALL rows into memory just to get one
User user = userRepo.findAll().get(0);  // SELECT * FROM users

// ✅ Database returns only 1 row
User user = userRepo.findAll(PageRequest.of(0, 1)).getContent().get(0);
// SELECT * FROM users LIMIT 1
```

| `PageRequest.of(0, 1)` | Full List |
|------------------------|-----------|
| `LIMIT 1` in SQL | `SELECT *` — all rows |
| O(1) memory | O(n) memory |
| Network transfers 1 row | Network transfers all rows |
| Index-friendly | Table scan |

> Even better: `findFirstByOrderByCreatedAtDesc()` — Spring generates `LIMIT 1` automatically.

---

### 9. `@Lock` Works on H2 but Not PostgreSQL

**Likely cause: H2 doesn't support or defaults to different locking behavior.**

| Issue | Explanation |
|-------|-------------|
| **H2 lacks `SELECT FOR UPDATE` support** in some modes | H2's MVCC mode may silently ignore pessimistic locks |
| **No `@Transactional`** | Lock requires active transaction — H2 might auto-commit, PostgreSQL won't |
| **Wrong isolation level** | PostgreSQL defaults to `READ COMMITTED`; lock behavior varies |
| **Lock timeout** | PostgreSQL waits indefinitely by default; H2 may return immediately |

**Fix:**

```java
@Transactional  // ← REQUIRED for locks!
@Lock(LockModeType.PESSIMISTIC_WRITE)
@QueryHints({
    @QueryHint(name = "javax.persistence.lock.timeout", value = "5000")  // 5s timeout
})
@Query("SELECT a FROM Account a WHERE a.id = :id")
Optional<Account> findByIdWithLock(@Param("id") Long id);
```

**Also verify:**
- PostgreSQL connection isn't in `autocommit` mode
- Use `SERIALIZABLE` or `READ COMMITTED` as appropriate
- Check `pg_locks` view to confirm locks are acquired

---

## Quick Reference Card

| Concept | Key Takeaway |
|---------|-------------|
| JPA vs Hibernate | Interface vs Implementation |
| LAZY vs EAGER | Prefer LAZY; EAGER causes performance issues |
| N+1 | Use `JOIN FETCH` or `@EntityGraph` |
| LazyInitializationException | Fetch within transaction or use DTOs |
| 1st vs 2nd level cache | Session vs SessionFactory scope |
| Spring Data query generation | Method name parsing + runtime proxies |
| PESSIMISTIC_WRITE | `SELECT FOR UPDATE` — exclusive lock |
| PageRequest.of(0,1) | Always use pagination for single-row needs |
| Lock on H2 vs PostgreSQL | H2 may silently ignore; always test on real DB |

</details>
---

---
## 5. DTOs, Specification API & Pagination

### DTO — The Warehouse Analogy (from Class Notes)

```
Entity  =  Physical product on the warehouse shelf
           (has internal barcodes, warehouse metadata — DO NOT ship raw)

DTO     =  The clean shipping box sent to the customer
           (only contains what the customer is allowed to see)

Specification  =  The Search Warrant
                  (instructions to Hibernate: which products to find on the shelf)
```

### Why Always Use DTOs?

| Problem Without DTO | Solution With DTO |
|---|---|
| Sensitive fields (`password`, `role`) exposed in API | DTO only includes allowed fields |
| `LazyInitializationException` during JSON serialization | DTO uses only already-loaded values |
| API contract breaks when entity changes | DTO version maintained separately |
| Can't add `@Email`, `@NotBlank` to entity | DTO has its own validation annotations |
| Client sets fields they shouldn't (`id`, `createdAt`) | DTO omits non-settable fields |

```java
// Request DTO — what client sends
public class LearnerRequestDTO {
    @NotBlank @Size(min = 2, max = 50)
    private String name;

    @NotBlank @Email
    private String email;
}

// Response DTO — what client receives (NO passwordHash, NO internalRole)
public class LearnerResponseDTO {
    private Long id;
    private String name;
    private String email;
}
```

### Specification API — Dynamic Query Building

```java
// Repository must extend JpaSpecificationExecutor
public interface LearnerRepository
    extends JpaRepository<Learner, Long>, JpaSpecificationExecutor<Learner> {}

// Composable specifications
public class LearnerSpecifications {

    public static Specification<Learner> hasCity(String city) {
        return (root, query, cb) -> {
            if (city == null) return cb.conjunction(); // 1=1 → no filter applied
            return cb.equal(root.get("city"), city);
        };
    }

    public static Specification<Learner> enrolledAfter(LocalDate date) {
        return (root, query, cb) -> {
            if (date == null) return cb.conjunction();
            return cb.greaterThanOrEqualTo(root.get("enrolledAt"), date);
        };
    }
}

// Combine and execute
Specification<Learner> spec = Specification
    .where(LearnerSpecifications.hasCity("Chennai"))
    .and(LearnerSpecifications.enrolledAfter(LocalDate.of(2024, 1, 1)));

List<Learner> results = learnerRepository.findAll(spec);
```

**Criteria API — Three Core Components**
- `CriteriaBuilder` — creates conditions (`equal`, `greaterThan`, `like`)
- `CriteriaQuery` — structures the query (`SELECT`, `WHERE`, `ORDER BY`)
- `Root` — defines the `FROM` clause and accesses entity attributes via `root.get("city")`

### Pagination

```java
@GetMapping("/learners")
public Page<LearnerResponseDTO> getLearners(
    @RequestParam(defaultValue = "0") int page,
    @RequestParam(defaultValue = "10") int size,
    @RequestParam(defaultValue = "name") String sortBy,
    @RequestParam(defaultValue = "ASC") String sortDir) {

    Sort sort = sortDir.equalsIgnoreCase("ASC")
        ? Sort.by(sortBy).ascending()
        : Sort.by(sortBy).descending();

    Pageable pageable = PageRequest.of(page, size, sort);
    // SQL: SELECT * FROM learner ORDER BY name ASC LIMIT 10 OFFSET 0

    return learnerRepository.findAll(pageable).map(this::toDTO);
}
// Page<T> response includes: totalElements, totalPages, number, size, first, last, hasNext
```

### `Pageable` as a Query Optimizer — Fetch Only What You Need

`Pageable` is not just for user-facing pagination. It is also a **precision fetching tool** — you can use it in any repository method to enforce a DB-level `LIMIT`, even when the caller only ever needs a single result.

```java
// Without Pageable — loads ALL available slots into memory, then uses only index [0]
List<ParkingSlot> all = repository.findByStatus("AVAILABLE"); // SELECT * → could be thousands
ParkingSlot slot = all.get(0); // wasteful

// With Pageable — DB does the work; only 1 row crosses the wire
List<ParkingSlot> one = repository.findAvailableSlot(PageRequest.of(0, 1));
// SQL: SELECT * FROM parking_slot WHERE status = 'AVAILABLE' LIMIT 1
```

This pattern is especially powerful **combined with `@Lock`**, where you want to lock and fetch exactly one row atomically:

```java
@Lock(LockModeType.PESSIMISTIC_WRITE)
@Query("SELECT s FROM ParkingSlot s WHERE s.status = 'AVAILABLE' ORDER BY s.id ASC")
List<ParkingSlot> findAvailableSlotWithLock(Pageable pageable);

// Caller passes PageRequest.of(0, 1) → DB: SELECT ... FOR UPDATE LIMIT 1
// Result: one row locked, one row fetched — nothing more
```

> 💡 **Rule:** If you write a query that returns a `List<T>` but you only ever use `list.get(0)`, that is a signal to add a `Pageable` parameter and pass `PageRequest.of(0, 1)`. It costs nothing in code complexity and saves significant memory and network at scale.

---

## 6. Exception Handling & Validation

### Global Exception Handling

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(LearnerNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ErrorResponse handleNotFound(LearnerNotFoundException ex) {
        return new ErrorResponse(404, ex.getMessage(), Instant.now());
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ErrorResponse handleValidation(MethodArgumentNotValidException ex) {
        List<String> errors = ex.getBindingResult().getFieldErrors()
            .stream().map(FieldError::getDefaultMessage).toList();
        return new ErrorResponse(400, "Validation failed: " + errors, Instant.now());
    }

    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public ErrorResponse handleAll(Exception ex) {
        return new ErrorResponse(500, "Internal server error", Instant.now());
    }
}
```

### Bean Validation Annotations

| Annotation | Validates |
|---|---|
| `@NotNull` | Field is not null |
| `@NotBlank` | String is not null, not empty, not whitespace |
| `@Email` | Valid email format |
| `@Size(min, max)` | String or collection length |
| `@Min` / `@Max` | Numeric range |
| `@Pattern(regexp)` | Regex match |
| `@Future` / `@Past` | Date validation |

### ❌ Critical Trap
```java
// Without @Valid → constraints silently ignored → 500 error
@PostMapping("/learners")
public ResponseEntity<LearnerResponseDTO> create(@RequestBody LearnerRequestDTO dto) { ... }

// With @Valid → constraints enforced → 400 on invalid data
@PostMapping("/learners")
public ResponseEntity<LearnerResponseDTO> create(@Valid @RequestBody LearnerRequestDTO dto) { ... }
```

### 💡 Memory Trick
> `"@Valid validates — without it, Spring ignores all your constraints silently."`  
> `"@ControllerAdvice = Global Try-Catch for your entire application."`

---

## 7. Spring Security — Authentication & Authorization

### Core Concepts

| Concept | Definition | Analogy |
|---|---|---|
| **Authentication** | Verifying WHO the user is | *"Show your ID card"* |
| **Authorization** | Verifying WHAT user can do | *"You have a VIP pass"* |
| **Encoding** | Reversible transformation | *"Scramble, but unscramble-able"* |
| **Encryption** | Reversible with key | *"Locked box — only key holder opens it"* |
| **Hashing** | Irreversible one-way | *"Meat grinder — can't un-grind"* |

### Full JWT Authentication Flow

```
=== REGISTRATION ===
POST /register { username, password }
  → Hash password with BCrypt(11 rounds)
  → Save user to DB
  → Return 201 Created

=== LOGIN ===
POST /login { username, password }
  → UsernamePasswordAuthenticationFilter
  → UserDetailsService.loadUserByUsername()
  → BCrypt.matches(entered, stored) → true/false
  → Generate JWT: Header.Payload.Signature
  → Return token to client

=== SUBSEQUENT REQUESTS ===
GET /learners
Authorization: Bearer eyJhbGci...
  → JwtAuthenticationFilter (OncePerRequestFilter)
  → JwtUtil.verifyToken() → parseSignedClaims()
  → Signature valid? → Populate SecurityContextHolder
  → @PreAuthorize("hasRole('ADMIN')") checked
  → Controller executes
```

### Security Filter Chain Configuration

```java
@Configuration
@EnableMethodSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(csrf -> csrf.disable())           // Safe for stateless JWT APIs
            .sessionManagement(sm -> sm
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/register", "/login", "/verify/**").permitAll()
                .requestMatchers("/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated())
            .addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class)
            .build();
    }
}
```

### JWT Utility

```java
private static final SecretKey KEY =
    Keys.hmacShaKeyFor("mySecretKey32BytesMinimum!!!!!!!!".getBytes(StandardCharsets.UTF_8));

public String generateToken(String username, List<String> roles) {
    return Jwts.builder()
        .subject(username)
        .issuedAt(new Date())
        .expiration(new Date(System.currentTimeMillis() + 8 * 60 * 60 * 1000)) // 8hr
        .claim("roles", roles)
        .signWith(KEY)
        .compact();
}
```

### JWT vs Session — When to Choose

| Factor | JWT (Stateless) | Session (Stateful) |
|---|---|---|
| State | Server stores nothing | Server stores session |
| Scalability | Any server validates JWT | Sticky sessions or Redis required |
| Revocation | Complex — needs token blacklist | Easy — delete from store |
| Use case | Microservices, REST APIs | Banking, government portals |

### Role-Based Authorization

```java
@PreAuthorize("hasRole('ADMIN')")          // ROLE_ADMIN in SecurityContextHolder
@PreAuthorize("hasAnyRole('ADMIN', 'INSTRUCTOR')")
// hasRole("ADMIN") automatically prepends "ROLE_"
// hasAuthority("ROLE_ADMIN") requires the full prefix manually
```

### ⚠️ Production Warnings
> - JWT Secret Key must be stored in **HashiCorp Vault / AWS Secrets Manager** — NEVER hardcoded
> - Set short expiry (15–60 mins) + implement **refresh token rotation**
> - `csrf.disable()` is safe **only** for stateless JWT APIs — never disable CSRF for session-based auth

### 💡 Memory Tricks
> - `"Authentication = Who are you? Authorization = What can you do?"`
> - `"JWT = Header.Payload.Signature — three parts, dot-separated."`
> - `"BCrypt = Salt + Hash + Rounds. Never reversible."`

### 🎯 Interview Questions
<details>
<summary>Click to expand</summary>

**Basic**
- What is the difference between authentication and authorization?
- Why do we use BCrypt for password hashing?
- What are the three components of a JWT token?

**Advanced**
- How do you revoke a JWT token before it expires?
- What is the difference between symmetric and asymmetric JWT signing?
- How does `SecurityContextHolder` work and why is it `ThreadLocal`-based?

</details>

---

## 8. Caching Strategies

### Cache Types

| Type | Location | Example | Use Case |
|---|---|---|---|
| **Centralized** | Shared server | Redis, Memcached | Shared data across multiple app servers |
| **Decentralized** | Each server locally | Caffeine, Ehcache | Server-local, fast, no network hop |
| **CDN / Edge** | Network edge | CloudFront, Cloudflare | Static assets, geographically close to user |
| **Browser** | Client-side | Cookies, SessionStorage | User-specific client state |

### Spring Cache Annotations

```java
@EnableCaching   // Add to main class or config

@Service
public class LearnerService {

    @Cacheable(value = "learners", key = "#id")  // Cache on first call
    public LearnerResponseDTO getLearnerById(Long id) { ... }

    @CachePut(value = "learners", key = "#result.id")  // Update cache after write
    public LearnerResponseDTO updateLearner(Long id, LearnerRequestDTO dto) { ... }

    @CacheEvict(value = "learners", key = "#id")  // Remove from cache on delete
    public void deleteLearner(Long id) { ... }
}
```

### Cache Eviction Policies

| Policy | Evicts | Best For |
|---|---|---|
| **LRU** (Least Recently Used) | Longest-unaccessed entry | General purpose — most common |
| **LFU** (Least Frequently Used) | Lowest access count | Skewed access patterns |
| **FIFO** | Oldest by insertion time | Queue-like / time-series data |
| **TTL** (Time To Live) | Entry exceeding its age limit | Tokens, sessions, product prices |

### Cache Update Patterns

| Pattern | How It Works | Trade-off |
|---|---|---|
| **Write-Through** | Write cache AND DB simultaneously | Consistent, but double write latency |
| **Write-Back** | Write cache first; DB updated async | Fast writes, risk of data loss |
| **Read-Through** | Cache auto-loads from DB on miss | Simple, but first request is slow |
| **Cache-Aside** | App checks cache; populates on miss | Fine-grained control (what `@Cacheable` does) |

### Critical Caching Rules (from Class Notes)
1. ❌ **Do NOT cache collections** — hard to invalidate consistently; cache by ID instead
2. ✅ **Cache on read paths** (`GET by ID`) — use `@Cacheable`
3. ✅ **Evict/update on write paths** — use `@CachePut` and `@CacheEvict`
4. ⚠️ **Redis does not understand Java objects** — serialize to JSON or use `RedisSerializer`

### 💡 Memory Tricks
> - `"Cache Miss = Go to DB. Cache Hit = Instant answer."`
> - `"@Cacheable = Check first. @CachePut = Update after. @CacheEvict = Delete after."`
> - `"LRU = Least Recently Used — the forgotten friend gets evicted."`

---

## 9. Reactive Programming, WebClient & WebFlux

### The Core Problem — Blocking Threads

```
Tomcat thread pool (default 200 threads)
Each thread: ~1MB stack memory
If each request blocks waiting for DB/API: max 200 concurrent requests

Reactor event loop (few threads)
One thread manages thousands of non-blocking I/O callbacks
→ Same hardware handles orders of magnitude more concurrency
```

### RestTemplate vs WebClient

| Feature | RestTemplate | WebClient |
|---|---|---|
| Blocking | ✅ Blocks Tomcat thread | ✅ Frees Tomcat thread immediately |
| Concurrency | ~200 with default pool | Thousands |
| Use case | Legacy / simple apps | Microservices, high-concurrency |
| Streaming | ❌ No | ✅ Yes (Flux) |

### Mono vs Flux

| Type | Represents | Example |
|---|---|---|
| `Mono<T>` | 0 or 1 item | Single product lookup |
| `Flux<T>` | 0 to N items | Server-sent event stream |

### Parallel and Sequential API Call Patterns

```java
// PARALLEL — all at once, wait for all (Mono.zip)
Mono<String> api1 = webClient.get().uri("/api1").retrieve().bodyToMono(String.class);
Mono<String> api2 = webClient.get().uri("/api2").retrieve().bodyToMono(String.class);
Mono<String> api3 = webClient.get().uri("/api3").retrieve().bodyToMono(String.class);

return Mono.zip(api1, api2, api3)
    .map(t -> List.of(t.getT1(), t.getT2(), t.getT3()));

// PARALLEL FASTEST — race: first one wins (Mono.first)
return Mono.first(api1, api2, api3);

// SEQUENTIAL CHAINED — B depends on A's result (flatMap)
return webClient.get().uri("/api1").retrieve().bodyToMono(Result1.class)
    .flatMap(r1 -> webClient.get().uri("/api2?id=" + r1.getId())
        .retrieve().bodyToMono(Result2.class)
        .map(r2 -> List.of(r1, r2)));

// SERVER-SIDE STREAMING (Flux)
Flux.interval(Duration.ofSeconds(4))
    .take(5)
    .flatMap(i -> webClient.get().uri("/products").retrieve().bodyToMono(Product.class));
```

### ❌ The Golden Rule

```java
// NEVER do this inside a WebFlux/reactive chain:
.flatMap(result -> {
    Thread.sleep(1000);  // ❌ Blocks event loop — catastrophic
    return someOperation.block();  // ❌ Deadlock risk
})
```

### Jackson Deserialization Fix (from Class Notes)
```java
// Error: Cannot construct instance of ProductResult (no default constructor)
// Fix: Ensure DTOs have a no-args constructor

@Data
@NoArgsConstructor  // ← Required by Jackson for deserialization
@AllArgsConstructor
public class ProductResult {
    private String name;
    private Double price;
}
```

### 💡 Memory Tricks
> - `"Mono = Maybe one. Flux = Flow of many."`
> - `"Event Loop = Air traffic controller — one controller, thousands of flights, none blocking."`
> - `"RestTemplate blocks like a phone call. WebClient is like sending a text and going about your day."`

### 🎯 Interview Questions
<details>
<summary>Click to expand</summary>

- What is the difference between `Mono.zip` and `Mono.first`?
- Why should you never call `.block()` inside a WebFlux application?
- What is backpressure in reactive programming and why does it matter?
- How would you implement retry with exponential backoff using `WebClient`?

</details>

---

## 10. Multithreading, Concurrency & CompletableFuture

### Concurrency vs Parallelism

| Concept | Description | Analogy |
|---|---|---|
| **Sequential** | One task finishes before next starts | One cashier, one customer |
| **Concurrent** | Tasks make progress by context-switching on one core | One cashier juggling 3 customers |
| **Parallel** | Tasks run simultaneously on multiple cores | Three cashiers at the same time |
| **Concurrent + Parallel** | Multiple cores, each also context-switching | Modern production systems |

### Thread Creation

```java
// Method 1: Extend Thread
class MyThread extends Thread {
    @Override
    public void run() { System.out.println(Thread.currentThread().getName()); }
}

// Method 2: Implement Runnable (PREFERRED — allows multiple inheritance)
Runnable task = () -> System.out.println(Thread.currentThread().getName());
Thread t = new Thread(task);

// KEY DISTINCTION:
t.start(); // ✅ Creates NEW thread → JVM internally calls run()
t.run();   // ❌ NO new thread — runs in current (main) thread
```

### Race Conditions & Fixes

```java
// Problem: count++ is NOT atomic (read → add → write — three steps)
int count = 0;
Runnable increment = () -> { for (int i = 0; i < 1000; i++) count++; }; // Race condition!

// Fix 1: synchronized
synchronized(this) { count++; }

// Fix 2: AtomicInteger (lock-free, fastest)
AtomicInteger count = new AtomicInteger(0);
count.incrementAndGet();

// Fix 3: ReentrantLock (more control)
Lock lock = new ReentrantLock();
lock.lock();
try { count++; } finally { lock.unlock(); }

// Fix 4: Thread-safe collections
Map<String, Integer> map = new ConcurrentHashMap<>();
List<String> list = new CopyOnWriteArrayList<>();
```

### CompletableFuture

```java
// Async computation
CompletableFuture<String> future = CompletableFuture.supplyAsync(() -> callExternalApi());

// Chaining
future.thenApply(String::toUpperCase)
      .thenAccept(result -> log.info("Done: {}", result))
      .exceptionally(ex -> { log.error("Error", ex); return null; });

// Wait for ALL to complete
CompletableFuture<String> f1 = CompletableFuture.supplyAsync(() -> callApi1());
CompletableFuture<String> f2 = CompletableFuture.supplyAsync(() -> callApi2());

CompletableFuture.allOf(f1, f2).thenRun(() -> {
    String r1 = f1.join(); // safe — already completed
    String r2 = f2.join();
});

// Note: CompletableFuture runs on daemon threads
// Main thread may exit before CF completes — use .join() to wait
```

### Best Practices ✅
- Do **not** rely on `setPriority()` for program correctness — scheduling is platform-dependent
- Use `ExecutorService` with a custom thread pool instead of the default `ForkJoinPool` for production
- Always shut down `ExecutorService` gracefully on application exit
- Prefer `AtomicInteger` / `ConcurrentHashMap` over `synchronized` for simple cases

### 💡 Memory Tricks
> - `"start() creates a new thread. run() is just a method call in your current thread."`
> - `"CompletableFuture = A promise in Java."`
> - `"Daemon thread = A ghost thread — dies when the main thread exits."`
> - `"Race condition = Two runners grabbing the same baton — unpredictable result."`

---

## 11. JVM Internals, Memory & Garbage Collection

### JVM Memory Structure

```
JVM Heap
├── Young Generation
│   ├── Eden Space        ← New objects allocated here first
│   ├── Survivor 0 (S0)   ← Objects that survived one GC cycle
│   └── Survivor 1 (S1)   ← Objects bounce between S0 and S1
│
└── Old Generation (Tenured)  ← Long-lived objects promoted from Young Gen

Off-Heap
└── Metaspace  ← Class metadata, loaded classes (replaced PermGen in Java 8+)

Per-Thread
└── Stack  ← Method call frames, local variables (~512KB–1MB per thread)
```

### GC Algorithms

| Algorithm | JVM Flag | Strength | Use Case |
|---|---|---|---|
| Serial GC | `-XX:+UseSerialGC` | Simple, low overhead | Single-core, < 100MB heap |
| Parallel GC | `-XX:+UseParallelGC` | Throughput-focused | Batch jobs |
| **G1 GC** | `-XX:+UseG1GC` | Balanced pause/throughput | **Default Java 9+ — most production apps** |
| **ZGC** | `-XX:+UseZGC` | Sub-millisecond pauses | Low-latency, large heaps (> 16GB) |
| Shenandoah | `-XX:+UseShenandoahGC` | Concurrent compaction | Ultra-low pause |

### Heap Sizing — From Class Notes (Critical)

| Scenario | Problem | Fix |
|---|---|---|
| **Under-provisioned** (HeapMax = 11MB, app uses 10MB) | GC runs constantly, CPU spikes | Increase `-Xmx` |
| **Over-provisioned** (HeapMax = 30GB, app uses 10MB) | GC rarely triggers, sudden long pause | Reduce to 2–3x working set |
| **Moderately provisioned** (2GB) | GC runs at appropriate intervals | ✅ Target this |

```bash
# Useful JVM diagnostic commands
java -XX:+PrintFlagsFinal -version | grep HeapSize    # See all heap flags
java -jar app.jar -Xms512m -Xmx2g                     # Set initial and max heap
java -jar app.jar -XX:+UseZGC                          # Switch GC algorithm

# Heap dump (WARNING: may contain PII — from class notes)
jmap -dump:format=b,file=heap.hprof <pid>
-XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/tmp/

# Thread dump
jstack <pid>

# Run with specific profile
java -jar build/libs/LMS-0.0.1-SNAPSHOT.jar --spring.profiles.active=prod
```

### 💡 Memory Tricks
> - `"Young Gen = Nursery. Old Gen = Retirement home. Metaspace = Blueprint storage."`
> - `"Mark = Paint used furniture. Sweep = Throw away unpainted. Compact = Move remaining to one room."`
> - `"Under-provisioned = GC never stops. Over-provisioned = GC never starts, then explodes."`

---

## 12. Spring Actuator & Production Monitoring

### Key Endpoints

| Endpoint | URL | Purpose |
|---|---|---|
| `health` | `/actuator/health` | App health — used by Kubernetes liveness/readiness probes |
| `metrics` | `/actuator/metrics` | List all metrics (JVM, HTTP, DB pool) |
| `env` | `/actuator/env` | Environment variables and properties |
| `beans` | `/actuator/beans` | All Spring beans in context |
| `loggers` | `/actuator/loggers` | View and **change log levels at runtime** |
| `threaddump` | `/actuator/threaddump` | Current JVM thread dump |
| `heapdump` | `/actuator/heapdump` | Download heap dump (restrict access!) |

### Configuration

```properties
# Expose only specific endpoints (never expose * in production)
management.endpoints.web.exposure.include=health,metrics,info,loggers
management.endpoint.health.show-details=always

# Separate port — firewall from public access
management.server.port=8081
```

### Production Monitoring Stack

```
Spring Actuator ──► Micrometer (metrics facade)
                          │
                          ├── Prometheus (time-series DB, scrapes /actuator/prometheus)
                          │         │
                          │         └── Grafana (visualization dashboards)
                          │
                          └── Datadog / Dynatrace (APM)
```

### ⚠️ Security Warning
> NEVER expose `/actuator/**` publicly.  
> Run on a separate management port and firewall it — allow only internal monitoring tools.

---

## 13. Testing in Spring Boot

### Testing Pyramid

| Layer | Annotation | Loads | Speed | Use For |
|---|---|---|---|---|
| Unit Test | `@ExtendWith(MockitoExtension.class)` | Nothing | ⚡ Fastest | Service logic — mock all deps |
| Controller Slice | `@WebMvcTest` | MVC layer only | 🔵 Fast | Controller + MockMvc |
| Repository Slice | `@DataJpaTest` | JPA + in-memory DB | 🔵 Fast | Repository queries (auto-rollback) |
| Integration Test | `@SpringBootTest` | Full context | 🔴 Slow | End-to-end API tests |

### Controller Test

```java
@WebMvcTest(LearnerController.class)
class LearnerControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean  // Spring Boot 3.4+ (was @MockBean)
    private LearnerManagementService service;

    @Test
    void getLearner_returnsLearner() throws Exception {
        when(service.getLearnerById(1L))
            .thenReturn(new LearnerResponseDTO(1L, "Pawan", "pawan@test.com"));

        mockMvc.perform(get("/learners/1"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.name").value("Pawan"));
    }
}
```

### Repository Test

```java
@DataJpaTest  // Auto-transactional → auto-rollback after each test
class LearnerRepositoryTest {

    @Autowired
    private LearnerRepository learnerRepository;

    @Test
    void findByEmail_returnsLearner() {
        learnerRepository.save(new Learner("Pawan", "pawan@test.com"));
        Optional<Learner> found = learnerRepository.findByLearnerEmail("pawan@test.com");
        assertTrue(found.isPresent());
    }
}
```

### Integration Test

```java
@SpringBootTest
@AutoConfigureMockMvc
class LearnerIntegrationTest {

    @Autowired private MockMvc mockMvc;
    @Autowired private LearnerRepository learnerRepository;

    @AfterEach
    void cleanUp() {
        learnerRepository.deleteAll(); // No auto-rollback in @SpringBootTest!
    }
}
```

### ❌ Critical Trap from Class Notes
> `@DataJpaTest` is `@Transactional` by default → auto-rollback after each test.  
> `@SpringBootTest` is **NOT** transactional → you must manually call `deleteAll()` in `@AfterEach`.

### 💡 Memory Tricks
> - `"@DataJpaTest = Database tests auto-rollback. @SpringBootTest = YOU must clean up."`
> - `"@MockitoBean = Replace real beans with fakes inside the Spring context."`

---

## 14. Master Cheat Sheet — Interview Quick Reference

### Annotations at a Glance

| Annotation | Category | One-Line Purpose |
|---|---|---|
| `@SpringBootApplication` | Core | Entry point — Config + EnableAutoConfig + ComponentScan |
| `@Component` / `@Service` / `@Repository` / `@RestController` | Bean | Spring-managed bean |
| `@Autowired` | DI | Inject dependency — prefer constructor injection |
| `@Qualifier("name")` / `@Primary` | DI | Resolve ambiguity when multiple beans exist |
| `@Transactional` | Data | DB transaction — commit or rollback |
| `@Entity` / `@Table` | JPA | Map Java class to DB table |
| `@ManyToOne` / `@OneToMany` / `@ManyToMany` | JPA | Entity relationships |
| `@JoinColumn` / `@JoinTable` | JPA | FK column or join table |
| `@Lock(LockModeType.PESSIMISTIC_WRITE)` | JPA | Acquire DB row lock on SELECT — generates `SELECT ... FOR UPDATE` |
| `@QueryHints(@QueryHint(name="jakarta.persistence.lock.timeout", value="3000"))` | JPA | Wait up to N ms for a lock; fail fast with `LockTimeoutException` instead of hanging |
| `@Cacheable` / `@CachePut` / `@CacheEvict` | Cache | Cache / update / evict |
| `@Valid` | Validation | Trigger Bean Validation on `@RequestBody` |
| `@RestControllerAdvice` / `@ExceptionHandler` | Exception | Global exception handling |
| `@PreAuthorize` | Security | Method-level authorization |
| `@Profile("prod")` | Config | Environment-specific bean |
| `@PostConstruct` / `@PreDestroy` | Lifecycle | Custom init/destroy logic |
| `@SpringBootTest` / `@WebMvcTest` / `@DataJpaTest` | Testing | Context slice for testing |

### HTTP Status Codes

| Code | Name | When to Use |
|---|---|---|
| `200` | OK | Successful GET, PUT, PATCH |
| `201` | Created | Successful POST |
| `204` | No Content | Successful DELETE, no body |
| `400` | Bad Request | Validation failure |
| `401` | Unauthorized | Missing or invalid token |
| `403` | Forbidden | Authenticated but wrong role |
| `404` | Not Found | Resource doesn't exist |
| `409` | Conflict | Duplicate resource |
| `500` | Internal Server Error | Unexpected server error |

### Top 20 Senior Interview Topics

| # | Topic | Depth |
|---|---|---|
| 1 | How `@ConditionalOn*` drives auto-configuration | Deep |
| 2 | Constructor vs field injection — why always constructor | Medium |
| 3 | `@Transactional` propagation and isolation levels | Deep |
| 4 | N+1 problem — causes and all 3 solutions | Deep |
| 5 | `LAZY` vs `EAGER` and `LazyInitializationException` | Deep |
| 6 | JWT vs Session — architectural trade-offs | Deep |
| 7 | `SecurityFilterChain` and filter ordering | Medium |
| 8 | BCrypt — why hashing, not encryption, for passwords | Medium |
| 9 | Cache eviction strategies and when NOT to cache | Medium |
| 10 | `WebClient` vs `RestTemplate` — event loop internals | Deep |
| 11 | `.block()` in WebFlux — why dangerous | Medium |
| 12 | `CompletableFuture` — `allOf` vs `anyOf` vs `thenCombine` | Deep |
| 13 | Race conditions — `AtomicInteger`, `synchronized`, `Lock` | Deep |
| 14 | JVM heap regions — Young, Old, Metaspace | Medium |
| 15 | G1 vs ZGC — trade-offs | Medium |
| 16 | Pagination — SQL `LIMIT`/`OFFSET` and `Page<T>` metadata | Medium |
| 17 | Specification API — `Root`, `CriteriaBuilder`, `CriteriaQuery` | Deep |
| 18 | DTO vs Entity — always DTOs in API responses | Medium |
| 19 | `@DataJpaTest` rollback vs `@SpringBootTest` manual cleanup | Medium |
| 20 | Spring Actuator — security and Prometheus integration | Medium |
| 21 | `@Lock` pessimistic vs `@Version` optimistic — when each is the right tool | Deep |

---

## 15. Practice Exercises

### 🟢 Beginner
1. Build a `Product` REST API (`GET`, `POST`, `PUT`, `DELETE`) with `@NotBlank`, `@Min(0)` validation — confirm `400` on invalid input.
2. Implement a `GlobalExceptionHandler` with handlers for `NotFoundException` and `MethodArgumentNotValidException`.
3. Add `@OneToMany` between `Category` and `Product`. Ensure the response DTO avoids circular JSON.

### 🟡 Intermediate
4. Implement dynamic `Product` filtering using Specification API — filter by name (contains), price range, category. All filters optional.
5. Add pagination + sorting to `GET /products` — return `Page<ProductResponseDTO>` with full metadata.
6. Implement JWT authentication: registration → login (returns JWT) → secured endpoint requiring `ROLE_ADMIN`.
7. Add Redis caching: `@Cacheable` on `getProductById`, `@CacheEvict` on `updateProduct` / `deleteProduct`.

### 🔴 Advanced
8. Rewrite a product enrichment service using `WebClient`. Call 10 external APIs in parallel with `Mono.zip`. Benchmark vs sequential.
9. Use `CompletableFuture.allOf` to enrich a product list concurrently. Compare throughput with sequential.
10. Write `@WebMvcTest` for `ProductController` (mock all services). Write `@DataJpaTest` for custom repository query methods.

### 🏭 Production Scenarios
11. Design a caching strategy for a 1-million-product catalog. Which endpoints get `@Cacheable`? What TTL? Redis vs Caffeine? Justify.
12. Your API throws `LazyInitializationException` in production on order serialization. Diagnose and fix using 3 different approaches.
13. A PR shows a `@Singleton` service with a `HashMap` field storing per-request data. Explain the race condition and provide the fix.
14. A smart parking system allows 200 concurrent booking requests, but only one available slot exists. Without locking, two users get confirmed bookings for the same spot. Implement `@Lock(PESSIMISTIC_WRITE)` + `PageRequest.of(0,1)` to fix it. Then explain why `lock.timeout = 3000` prevents a thread pile-up, and why the fix must be validated on PostgreSQL, not just H2.

---

<div align="center">

## 🚀 Keep Going

> *"Master the Why. The How will follow. The What is just memory."*

**Good luck with your Senior Engineer & SDET interviews!**

---

⭐ If this helped you — star this repo and share it with your peers!

</div>
