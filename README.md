# News Application — Capstone Project

A Django + Django REST Framework news platform where publishers, independent
journalists and editors manage articles and newsletters, and readers
subscribe to the content they care about.

---

## 1. Design

### 1.1 Functional requirements

| # | Requirement |
|---|---|
| F1 | Readers can view approved articles and newsletters. |
| F2 | Readers can subscribe to publishers and/or individual journalists. |
| F3 | Journalists can write articles (independently or for a publisher) and submit them for review. |
| F4 | Journalists and editors can create and edit newsletters (curated collections of approved articles). |
| F5 | Editors can review, approve or reject pending articles. |
| F6 | On approval, subscribers are notified by email and the approval is logged via an internal REST endpoint. |
| F7 | A third-party client can authenticate (JWT) and consume articles via a REST API, including a feed scoped to a reader's subscriptions. |
| F8 | Access to every view/endpoint is restricted according to the user's role (Reader / Editor / Journalist). |

### 1.2 Non-functional requirements

| # | Requirement |
|---|---|
| N1 | **Security** — role-based authorization enforced at both the web-view layer (Django groups/permissions) and the API layer (DRF permission classes); JWT-based stateless auth for the API. |
| N2 | **Data integrity** — the schema is normalised (see §1.4) to avoid duplicated/inconsistent data; foreign keys enforce referential integrity. |
| N3 | **Extensibility** — role logic is centralised (one `role` field + Django Groups) so new roles/permissions can be added without touching every view. |
| N4 | **Testability** — business logic (approval side-effects) is isolated in a signal so it can be unit-tested and mocked independently of the view layer. |
| N5 | **Portability** — the project runs on SQLite out of the box for development/testing and switches to MariaDB via a single environment variable for production (see §4). |
| N6 | **Usability** — server-rendered templates for the editorial workflow are simple, responsive-enough HTML with clear status badges (pending/approved) and inline messages. |

### 1.3 Entity-Relationship overview

```
 CustomUser (role: READER | EDITOR | JOURNALIST)
   ├── subscriptions_publishers  M2M──► Publisher            (Reader only)
   ├── subscriptions_journalists M2M──► CustomUser (self, journalists) (Reader only)
   ├── authored_articles     1:M◄── Article.author            (Journalist)
   ├── authored_newsletters  1:M◄── Newsletter.author          (Journalist/Editor)
   ├── approved_articles     1:M◄── Article.approved_by        (Editor)
   ├── editor_publishers     M2M──► Publisher.editors
   └── journalist_publishers M2M──► Publisher.journalists

 Publisher
   ├── editors      M2M──► CustomUser (role=EDITOR)
   └── journalists  M2M──► CustomUser (role=JOURNALIST)

 Article
   ├── author      FK──► CustomUser   (required; must be a journalist)
   ├── publisher   FK──► Publisher    (nullable: NULL = independent article)
   ├── approved_by FK──► CustomUser   (nullable; the approving editor)
   └── approved, approved_at, created_at, updated_at

 Newsletter
   ├── author    FK──► CustomUser
   └── articles  M2M──► Article
```

**Article ↔ Publisher/Journalist rule**: an article always has an `author`
(a journalist). If `publisher` is `NULL`, the article is *independent*
content; if `publisher` is set, it is *publisher* content written by one of
that publisher's journalists (`ArticleSerializer.validate_publisher`
enforces this). This satisfies "an article must be associated either with a
journalist or a publisher" without needing two separate article tables.

### 1.4 Normalisation

- **1NF** — every field holds a single, atomic value (e.g. no comma-separated
  lists of authors); repeating relationships (a publisher's many editors, a
  newsletter's many articles) are modelled with `ManyToManyField`, which
  Django resolves into a proper junction table (`Publisher_editors`,
  `Newsletter_articles`, etc.) rather than a repeating column.
- **2NF** — every non-key column depends on the *whole* primary key. Since
  every table here uses a single-column surrogate primary key (`id`), this
  is automatically satisfied — there are no composite keys with partial
  dependencies.
- **3NF** — non-key columns depend only on the primary key, not on each
  other. For example, `Article` stores a `publisher_id` (FK) rather than
  the publisher's name — the name lives only in `Publisher.name`, so a
  rename never causes an inconsistency. Likewise `Article.author` stores a
  FK to `CustomUser`, not a duplicated username/email string.
- Junction tables created by Django for the M2M fields (`Publisher↔editors`,
  `Publisher↔journalists`, `Newsletter↔Article`,
  `CustomUser↔subscriptions_publishers`,
  `CustomUser↔subscriptions_journalists`) are themselves in 3NF: each row is
  just a pair of foreign keys.

### 1.5 Roles, groups & permissions

Implemented as **Django Groups** named `Reader`, `Editor`, `Journalist`,
created and populated by `python manage.py setup_groups`
(`accounts/management/commands/setup_groups.py`). A `post_save` signal on
`CustomUser` (`accounts/signals.py`) keeps a user's group membership in
sync with their `role` field automatically, and clears the reader-only
subscription fields whenever the role is not `READER` (per the brief's "the
program should assign the fields for the reader a value of 'None', and vice
versa" — enforced by clearing the M2M relations rather than leaving stale
data).

| Role | Articles | Newsletters |
|---|---|---|
| Reader | view only | view only |
| Editor | view, change, delete, **approve** (`can_approve_article`) | view, change, delete |
| Journalist | add, view, change, delete (own) | add, view, change, delete |

### 1.6 Front end / UX plan

Server-rendered Django templates (`templates/`, `articles/templates/articles/`)
provide the editorial workflow:

- **Article list** — public-ish feed showing approved articles (plus a
  journalist's own pending drafts), with a status badge.
- **Article detail** — full article view.
- **Submit article form** — journalists only; on submit the article enters
  the editorial queue as `approved=False`.
- **Editorial queue** (`/pending/`) — editors only (`EditorRequiredMixin`);
  lists every unapproved article with **Review & approve** / **Reject**
  actions.
- **Approve/Reject confirmation pages** — a deliberate confirmation step
  before the irreversible action, explaining that approval will notify
  subscribers.
- **Newsletter list/detail/create** — journalists and editors can curate
  newsletters from already-approved articles (`NewsletterForm` restricts
  the `articles` choices to `approved=True`).
- A shared `base.html` provides navigation (role-aware — the editorial
  queue link only appears for staff-like users) and Django `messages`
  feedback banners for success/error states.
- Minimal inline CSS keeps the UI clean without extra front-end tooling,
  appropriate for the scope of this capstone.

---

## 2. Project layout

```
news_project/
├── accounts/            # CustomUser, roles, group-sync signal, setup_groups command
├── articles/             # Publisher, Article, Newsletter models, editorial views/templates, approval signal
├── api/                  # DRF serializers, permissions, viewsets, /api/approved/ log endpoint, tests/
├── templates/             # base.html, registration/login.html
├── news_project/          # settings.py, urls.py
├── manage.py
└── requirements.txt
```

## 3. Approval workflow (Option 1 — Django Signals)

1. A journalist submits an article via the web form (`articles.views.create_article`)
   or `POST /api/articles/` — it is created with `approved=False`.
2. An editor reviews it at `/pending/` and clicks **Review & approve**, which
   calls `articles.views.approve_article` (web) or `POST /api/articles/<id>/approve/`
   (API). Both call the model helper `Article.approve(editor)`, which sets
   `approved=True`, `approved_by`, `approved_at` and saves.
3. The `post_save` signal `articles.signals.notify_on_approval` fires and:
   - Emails every **Reader** subscribed to the article's publisher and/or
     its journalist author (`django.core.mail.send_mail`, console backend
     in development).
   - `POST`s a JSON summary of the article to this project's own
     `/api/approved/` endpoint using the `requests` library, which stores
     it in `ApprovedArticleLog` (`api/models.py`) — simulating external
     sharing while keeping everything inside the project.
   - Both side effects fail *silently* (logged, not raised) if email or the
     HTTP call cannot complete, so a network hiccup never blocks the
     editor's approval action.

## 4. REST API

Base URL: `/api/`

| Method | Endpoint | Access |
|---|---|---|
| POST | `/api/token/` | Obtain a JWT access/refresh pair |
| POST | `/api/token/refresh/` | Refresh an access token |
| GET | `/api/articles/` | Any authenticated user — approved articles (+ a journalist's own pending ones) |
| GET | `/api/articles/subscribed/` | Reader — approved articles from subscribed publishers/journalists only |
| GET | `/api/articles/<id>/` | Any authenticated user (subject to visibility rules) |
| POST | `/api/articles/` | Journalists only |
| PUT/PATCH | `/api/articles/<id>/` | Editors, or the owning journalist |
| DELETE | `/api/articles/<id>/` | Editors, or the owning journalist |
| POST | `/api/articles/<id>/approve/` | Editors only |
| GET/POST/PUT/DELETE | `/api/newsletters/...` | View: anyone authenticated. Create: journalists **and** editors. Update/Delete: editors or the owning author. |
| GET | `/api/publishers/` | Any authenticated user |
| POST/GET | `/api/approved/` | Internal — used by the approval signal |

Authorization is enforced with custom DRF permission classes
(`api/permissions.py`): `IsJournalistToCreate`, `IsJournalistOrEditorToCreate`,
`IsEditorOrOwnerJournalistForWrite`, `IsEditor`.

## 5. Running the project

```bash
python -m venv venv && source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt

python manage.py migrate
python manage.py setup_groups        # creates Reader/Editor/Journalist groups + permissions
python manage.py createsuperuser     # create an admin to manage users/publishers

python manage.py runserver
```

Then create a few users via `/admin/` (or the Django shell), assign a
`role`, and add journalists/editors to a `Publisher`.


### Registering and testing the three account types

The web application now includes self-service registration at `/accounts/register/`.
An assessor can create a **Reader**, **Journalist**, or **Editor** account from the
registration form. After registration (or a normal login), the user is automatically
routed to the dashboard for that role.

Suggested assessor test flow:

1. Open `/accounts/register/` and create a Reader account. Confirm it opens the Reader dashboard.
2. Log out, register a Journalist account, then use **Submit Article** to create a pending article.
3. Log out, register an Editor account, open **Editorial Queue**, and review the pending article.
4. Confirm each role only sees navigation and dashboards appropriate to that role.

Before testing, initialise the role groups and permissions with:

```bash
python manage.py migrate
python manage.py setup_groups
```

### Running the automated tests

```bash
python manage.py test
```

52 tests across `accounts`, `articles`, and `api/tests/` cover: role→group
sync, editorial-view access control, JWT auth, role-based CRUD on the API,
reader-subscription filtering, and the approval signal (email + internal
API POST), using `unittest.mock.patch` to isolate external calls.

## 6. Migrating to MariaDB

The project defaults to SQLite for zero-friction local development and CI.
To point it at MariaDB instead:

1. Install the MariaDB server and create a database + user:
   ```sql
   CREATE DATABASE news_db CHARACTER SET utf8mb4;
   CREATE USER 'news_user'@'localhost' IDENTIFIED BY 'yourpassword';
   GRANT ALL PRIVILEGES ON news_db.* TO 'news_user'@'localhost';
   FLUSH PRIVILEGES;
   ```
2. Install the MySQL/MariaDB Python driver on the host (needs MariaDB's dev
   headers, e.g. `libmariadb-dev` on Debian/Ubuntu):
   ```bash
   pip install mysqlclient
   ```
3. Set environment variables and re-run migrations:
   ```bash
   export USE_MARIADB=1
   export DB_NAME=news_db DB_USER=news_user DB_PASSWORD=yourpassword DB_HOST=127.0.0.1 DB_PORT=3306
   python manage.py migrate
   python manage.py setup_groups
   ```
`news_project/settings.py` reads `USE_MARIADB` and switches the `DATABASES`
engine to `django.db.backends.mysql` (Django's MariaDB-compatible backend)
automatically — no code changes required.

## 7. Design decisions worth noting

- **Single CustomUser + role field**, rather than three separate user
  models — simpler auth, one login table, and role changes are a single
  field update (with the group-sync signal handling the rest).
- **Journalist "published" fields are reverse relations**, not duplicate
  FKs on `CustomUser` — `user.independent_articles` /
  `user.independent_newsletters` read from `Article.author` /
  `Newsletter.author` via `related_name`, avoiding data duplication while
  still satisfying "ForeignKey or Reverse relation" from the brief.
- **`get_object` bypasses list-level filtering** for retrieve/update/delete
  on the API so that permission violations return `403 Forbidden` (a
  meaningful signal) rather than a misleading `404 Not Found`, while `list()`
  still only shows what a role should see.
- **Approval side effects never block approval** — both the email send and
  the internal API POST are wrapped so a transient failure is logged, not
  raised, keeping the editor's workflow reliable.
