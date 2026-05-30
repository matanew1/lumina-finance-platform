<div dir="rtl">

# Interview Preparation — Lumina Finance Platform

<p dir="rtl">
מסמך הכנה מקיף לראיון על המטלה. עובר על המערכת מקצה לקצה — שורה אחר שורה, החלטה אחר החלטה — ומציין שאלות צפויות, תשובות מומלצות, ונקודות חולשה שכדאי להכיר.
</p>

---

## תוכן עניינים

<div dir="rtl">

1. תמונת על — הארכיטקטורה
2. Entry Point ו-App Factory
3. שכבת ה-DB (SQLAlchemy)
4. המודלים (ORM)
5. Schemas + Protocols — הקסם של structural typing
6. ה-API Routes — שכבת ה-HTTP
7. Flow מלא: POST /upload-transactions
8. Data Ingestion — Pandas + Validation
9. ה-FIFO Engine — הלב הפיננסי
10. P&L — Realized + Unrealized
11. Position Snapshots — הגשר לוויולציות
12. Violations — 4 חוקים, 2 רמות
13. Analytics — 4 חישובים
14. Repositories — שכבת הגישה ל-DB
15. Services — שכבת הלוגיקה
16. Utils — Decimal, Files, Exceptions, Config
17. Tests — מה ולמה
18. Constants — סף ערכים מוסברים
19. AI_USAGE.md — איך לדבר עליו
20. שאלות צפויות + תשובות מומלצות
21. נקודות חולשה — תהיה כן
22. Cheat Sheet — דברים בעל-פה

</div>

---

## 1. תמונת על — הארכיטקטורה

### Stack

<p dir="rtl">
הסטאק כולל:
</p>

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0 (typed Mapped), Pydantic v2, Pydantic Settings, pandas
- **DB:** SQLite (default); כל DB עם SQLAlchemy driver נתמך דרך `DATABASE_URL`
- **Frontend:** React + Vite (לא נסקר במסמך הזה)
- **Tests:** pytest + FastAPI TestClient + StaticPool in-memory SQLite
- **Deploy:** Docker, docker-compose

### Layered Architecture

```
                  ┌──────────────────────────────┐
                  │  api/routes/                 │  HTTP layer
                  │  (transactions, clients,     │  • path/query parsing
                  │   positions, violations,     │  • response models
                  │   analytics)                 │  • status codes
                  └──────────────┬───────────────┘
                                 │
                  ┌──────────────▼───────────────┐
                  │  services/                   │  Business logic
                  │  (transactions, positions,   │  • orchestrates flow
                  │   violations, analytics,     │  • domain rules
                  │   clients)                   │  • NO HTTP / NO SQL
                  └──────────────┬───────────────┘
                                 │
                  ┌──────────────▼───────────────┐
                  │  repositories/               │  Data access
                  │  (transactions, positions,   │  • SQLAlchemy queries
                  │   clients, violations,       │  • NO business rules
                  │   analytics)                 │
                  └──────────────┬───────────────┘
                                 │
                  ┌──────────────▼───────────────┐
                  │  models/  (SQLAlchemy ORM)   │  DB schema
                  │  (Transaction, Position,     │
                  │   Violation)                 │
                  └──────────────────────────────┘

   ┌──────────────────────────────────────────────┐
   │  schemas/  (Pydantic + Protocols)            │  Data contracts
   │  ─ shared.py — TransactionView, PositionView │  (cross-layer)
   │  ─ per-domain response/request schemas       │
   └──────────────────────────────────────────────┘

   ┌──────────────────────────────────────────────┐
   │  utils/                                      │  Pure utilities
   │  config, constants, exceptions, decimal,     │
   │  dataframe, files, sorters                   │
   └──────────────────────────────────────────────┘
```

### עקרונות שמומלץ לציין

<p dir="rtl">
<b>Separation of Concerns</b> — כל שכבה אחראית לדבר אחד.
</p>

<p dir="rtl">
<b>Dependency Inversion</b> — services מקבלים Protocol (interface) של repository, לא class concrete. זה מאפשר mocking קל ובדיקות יציבות.
</p>

<p dir="rtl">
<b>Domain-Driven structure</b> — חלוקה לדומיינים (transactions / positions / violations / analytics), לא לפי שכבות (controllers / services / dao). כל דומיין autonomous.
</p>

<p dir="rtl">
<b>DB-agnostic</b> — DATABASE_URL ב-env. החלפה ל-Postgres = שינוי משתנה.
</p>

<p dir="rtl">
<b>Async only at boundaries</b> — endpoints async (HTTP I/O), הלוגיקה sync. אין async למראית עין.
</p>

---

## 2. Entry Point ו-App Factory

### `backend/main.py`

```python
"""Compatibility entrypoint for existing `uvicorn backend.main:app` commands."""
from backend.app.main import app, create_app
__all__ = ["app", "create_app"]
```

<p dir="rtl">
<b>מטרה:</b> backward compatibility. שתי הצורות יעבדו — <code>uvicorn backend.main:app</code> או <code>uvicorn backend.app.main:app</code>.
</p>

### `backend/app/main.py`

```python
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    if settings.auto_init_db:
        init_schema()
    else:
        logger.info("Database auto-initialization is disabled.")
    yield


def create_app() -> FastAPI:
    configure_logging(settings.log_level)
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
```

### נקודות שמומלץ להבליט

<p dir="rtl">
<b>Factory Pattern</b> (create_app) — מאפשר ליצור instances נפרדים בטסטים, או config שונה לכל סביבה.
</p>

<p dir="rtl">
<b>lifespan context manager</b> — החלף המודרני של startup event שנפסל. עם async generator, מבוצע בעלייה והורדה.
</p>

<p dir="rtl">
<b>auto_init_db flag</b> — כיבוי בטסטים. הם מנהלים את ה-schema בעצמם דרך Base.metadata.create_all על engine ייעודי.
</p>

<p dir="rtl">
<b>CORS</b> מ-env, לא hardcoded — קל לעדכן בלי deploy חדש.
</p>

<p dir="rtl">
<b>register_exception_handlers</b> — טיפול אחיד ב-AppError. JSON response עם status_code ו-detail.
</p>

### שאלות צפויות

<p dir="rtl">
<b>Q: למה lifespan ולא startup event?</b>
</p>

<p dir="rtl">
Startup/shutdown events הוצאו משימוש (deprecated) ב-Starlette. ה-Async context manager מאחד init+teardown במקום אחד, ו-Python מבטיח שה-shutdown יקרה גם אם startup נזרק חצי. גם נקי יותר לטסט.
</p>

<p dir="rtl">
<b>Q: מתי create_app ייקרא מספר פעמים?</b>
</p>

<p dir="rtl">
בטסטים, אם נרצה לבדוק שני app instances עם config שונה. כרגע אני קורא לו פעם אחת בסוף הקובץ, אבל ה-API תומך בכמה.
</p>

---

## 3. שכבת ה-DB (SQLAlchemy)

### `backend/app/db/base.py`

```python
CONSTRAINT_NAMING = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=CONSTRAINT_NAMING)
```

### למה זה חשוב

<p dir="rtl">
SQLAlchemy מייצר שמות אוטומטיים ל-constraints (לדוגמה: pk_positions, uq_positions_client_id_isin). בלי naming_convention, השמות תלויים ב-DB engine, ו-Alembic לא יכול ליצור migrations יציבות.
</p>

<p dir="rtl">
<b>שאלה מסוכנת:</b> "ההסבר טוב, אבל אתה לא משתמש ב-Alembic, אז למה צריך את זה?"
</p>

<p dir="rtl">
<b>תשובה:</b> זה preparation. אם מחר אעבור ל-Alembic, ה-migrations הראשונות לא ייפלו על constraint שמותיו השתנו.
</p>

### `backend/app/db/session.py`

```python
def _sqlite_path(database_url: str) -> Path | None:
    if not database_url.startswith("sqlite"):
        return None
    if database_url in ("sqlite://", "sqlite:///:memory:"):
        return None
    if database_url.startswith("sqlite:///"):
        raw_path = unquote(database_url.removeprefix("sqlite:///"))
        if raw_path in ("", ":memory:"):
            return None
        path = Path(raw_path)
        return path if path.is_absolute() else Path.cwd() / path
    return None


def _engine_kwargs(database_url: str) -> dict[str, object]:
    kwargs: dict[str, object] = {"future": True}
    if database_url.startswith("sqlite"):
        sqlite_path = _sqlite_path(database_url)
        if sqlite_path is not None:
            sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        kwargs["connect_args"] = {"check_same_thread": False}
        return kwargs
    kwargs["pool_pre_ping"] = True
    return kwargs


engine = create_engine(settings.database_url, **_engine_kwargs(settings.database_url))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
_schema_initialized = False


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_schema() -> None:
    global _schema_initialized
    if _schema_initialized:
        return
    import backend.app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _schema_initialized = True
```

### `_sqlite_path` — למה הקוד הזה

<p dir="rtl">
SQLAlchemy לא יוצר תיקיות אבא של קובץ SQLite. אם ה-URL הוא <code>sqlite:///./data/app.db</code> והתיקייה <code>data/</code> לא קיימת — נקבל error. הפונקציה מוציאה את ה-path האמיתי, ו-<code>_engine_kwargs</code> יוצר את התיקייה.
</p>

<p dir="rtl">
המקרים השונים:
</p>

- `sqlite://` (בלי slash) ו-`sqlite:///:memory:` → in-memory, אין קובץ
- `sqlite:///./data/app.db` → relative path מ-CWD
- `sqlite:////absolute/path.db` → absolute path

### `_engine_kwargs` — הבדלים לפי DB

<p dir="rtl">
ההגדרות שונות בין SQLite ל-Postgres:
</p>

- `future=True` — SQLAlchemy 2.0 API מודרני (כל הDBs)
- `check_same_thread=False` — SQLite דורש thread safety מפורש לעבודה עם FastAPI threading
- `pool_pre_ping=True` — בודק connection לפני שימוש (`SELECT 1`); מנקה connections מתים (Postgres / שאר)

### `SessionLocal` — האזטרוטיות

- `autocommit=False` — אנחנו שולטים מתי לעשות commit
- `autoflush=False` — לא לעשות flush אוטומטי לפני queries; נותן שליטה מלאה

### `get_db()` — Dependency injection

<p dir="rtl">
זה generator. FastAPI קורא לו לכל request, יוצר session, מעביר ל-route, ובסוף סוגר. ה-<code>finally</code> שומר שה-session ייסגר גם אם זרק exception.
</p>

### `init_schema` — Idempotent

<p dir="rtl">
ה-flag <code>_schema_initialized</code> מבטיח שלא ניצור schema פעמיים. השורה <code>import backend.app.models</code> חשובה — בלי זה SQLAlchemy לא יודע על המודלים, כי <code>Base.metadata</code> מתמלא רק כשהקבצים נטענים.
</p>

### שאלות צפויות

<p dir="rtl">
<b>Q: למה לא Alembic?</b>
</p>

<p dir="rtl">
המטלה הייתה 3-5 שעות. <code>create_all</code> עובד ל-POC. הייתי מוסיף Alembic כצעד ראשון לפרודקשן — alembic init, revision --autogenerate, ומכאן והלאה כל שינוי במודל הוא revision חדש.
</p>

<p dir="rtl">
<b>Q: מה אם שני workers (gunicorn) ירוצו init_schema במקביל?</b>
</p>

<p dir="rtl">
ה-<code>_schema_initialized</code> הוא local לתהליך. עם <code>create_all</code> של SQLAlchemy זה idempotent (CREATE TABLE IF NOT EXISTS), אז גם אם רץ פעמיים זה לא הורס כלום. ב-Postgres עם Alembic זה היה race condition אמיתי שדורש lock על schema.
</p>

---

## 4. המודלים (ORM)

### `Transaction` ([transaction.py](backend/app/models/transaction.py))

```python
class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("action IN ('buy', 'sell')", name="transaction_action_valid"),
        CheckConstraint("quantity > 0", name="transaction_quantity_positive"),
        CheckConstraint("price > 0", name="transaction_price_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    transaction_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    isin: Mapped[str] = mapped_column(String(12), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=False), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)
```

### החלטות עיצוב — לציין בראיון

<p dir="rtl">
שמירת מחירים וכמויות עם <b>Numeric(18, 6)</b> ולא Float — float ב-IEEE 754 לא יכול לייצג 0.1 במדויק. בכסף זה אסור. 18 ספרות סך הכל, 6 אחרי הנקודה.
</p>

<p dir="rtl">
<b>transaction_id</b> מוגדר כ-unique ב-DB level — אכיפת ייחודיות לא רק באפליקציה. גם אם יש race condition, ה-DB יחזיר IntegrityError.
</p>

<p dir="rtl">
שלוש <b>CheckConstraint</b>s — Defense in depth. גם אם הוולידציה ב-Python נכשלה (bug, malicious input), ה-DB יבלום.
</p>

<p dir="rtl">
<b>Index</b> על client_id, isin, timestamp — כל השאילתות מסננות/ממיינות לפיהם. ה-transaction_id גם indexed (כי unique).
</p>

<p dir="rtl">
<b>String(12)</b> ל-ISIN — ISIN הוא תמיד 12 תווים (תקן ISO 6166).
</p>

<p dir="rtl">
<b>created_at</b> עם server_default=func.now() — ה-DB ממלא את הערך. מקור אמת אחיד, גם אם האפליקציה לא שלחה.
</p>

<p dir="rtl">
<b>DateTime(timezone=False)</b> — תזמן שמרני. אני שומר naive UTC ולא מסתכל על TZ. בפרודקשן זה היה צריך להיות timezone=True.
</p>

### `Position` ([position.py](backend/app/models/position.py))

```python
class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (
        UniqueConstraint("client_id", "isin", name="uq_positions_client_isin"),
        CheckConstraint("quantity >= 0", name="position_quantity_non_negative"),
        CheckConstraint("average_price >= 0", name="position_average_price_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    isin: Mapped[str] = mapped_column(String(12), index=True, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    average_price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    market_price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    unrealized_pnl: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    @property
    def average_cost(self) -> Decimal:
        return self.average_price
```

### החלטות

<p dir="rtl">
<b>UniqueConstraint(client_id, isin)</b> — אי אפשר ששתי שורות פוזיציה יתייחסו לאותו (לקוח, נכס). זה אכיפה לזה ש-FIFO מצרף אותם.
</p>

<p dir="rtl">
realized_pnl ו-unrealized_pnl <b>מאוחסנים</b> ב-DB ולא מחושבים בכל read — בחירה מודעת. ראה AI_USAGE.md "Mistakes And How I Fixed Them" #1.
</p>

<p dir="rtl">
<b>average_cost כ-@property</b> — backward compatibility. ה-API היה צריך average_cost, אבל בעמודה ב-DB יש average_price. ה-property "מתרגם".
</p>

<p dir="rtl">
<b>onupdate=func.now()</b> — ה-DB מעדכן את updated_at כל פעם שיש update.
</p>

### `Violation` ([violation.py](backend/app/models/violation.py))

```python
class Violation(Base):
    __tablename__ = "violations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    transaction_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("transactions.transaction_id"),
        nullable=True,
    )
    violation_type: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), server_default=func.now(), nullable=False)
```

### החלטות

<p dir="rtl">
<b>transaction_id הוא ForeignKey</b> — מקשר ויולציה לטרנזקציה ספציפית.
</p>

<p dir="rtl">
<b>nullable=True</b> — לא לכל ויולציה יש טרנזקציה אחת (למשל, risk_concentration קשורה לכל ה-position, לא לטרנזקציה אחת). הוא קושר לטרנזקציה האחרונה של אותו (client, isin) דרך ה-snapshot.
</p>

<p dir="rtl">
<b>Indexes</b> על violation_type ו-severity — שאילתה כמו <code>GET /violations?severity=error</code> תהיה מהירה.
</p>

<p dir="rtl">
<b>message הוא Text</b> ולא String(N) — כי המסרים יכולים להיות ארוכים.
</p>

### שאלות צפויות

<p dir="rtl">
<b>Q: למה לא להוסיף ForeignKey על client_id?</b>
</p>

<p dir="rtl">
אין clients table. ה-clients שלי נגזרים מ-<code>SELECT DISTINCT client_id FROM transactions</code>. זה מודע — אין כיום לקוח 'יציבה' עם metadata. בפרודקשן אם הוסיפו לקוחות עם פרטי קשר, היה צריך טבלה נפרדת ו-FK.
</p>

<p dir="rtl">
<b>Q: למה לא CASCADE על ForeignKey?</b>
</p>

<p dir="rtl">
אם אמחק טרנזקציה, הייתי רוצה שהוויולציה הקשורה גם תימחק (ON DELETE CASCADE). זו השמטה ששווה לתקן. כרגע המערכת לא מוחקת טרנזקציות, אז זה לא נצרך, אבל זה feature שכדאי להוסיף.
</p>

---

## 5. Schemas + Protocols — הקסם של structural typing

### `backend/app/schemas/shared.py` — המוח של המערכת

```python
@runtime_checkable
class TransactionView(Protocol):
    client_id: str
    transaction_id: str
    isin: str
    action: str
    quantity: Decimal
    price: Decimal
    timestamp: datetime


@runtime_checkable
class PositionView(Protocol):
    client_id: str
    isin: str
    quantity: Decimal
    market_price: Decimal
    transaction_id: Optional[str]
```

### למה זה גאוני

<p dir="rtl">
Services מקבלים TransactionView. כל קוד עם השדות האלה יעבוד:
</p>

```python
# 1. ORM model (SQLAlchemy)
def process(transactions: list[TransactionView]): ...
process(db.query(Transaction).all())  # ✅ עובד

# 2. Pydantic schema
process([TransactionIngested(...), ...])  # ✅ עובד

# 3. dataclass / mock
@dataclass
class Mock: client_id: str; ...
process([Mock(...), ...])  # ✅ עובד
```

<p dir="rtl">
<b>אין צורך בירושה.</b> Python בודק structurally — יש לך את כל השדות? אז אתה תואם.
</p>

### שאלות צפויות

<p dir="rtl">
<b>Q: מה ההבדל בין Protocol ל-ABC?</b>
</p>

| ABC | Protocol |
|---|---|
| דורש `class Foo(ABC)` ו-`class Bar(Foo)` | אין ירושה — שייכות לפי structure |
| nominal typing | structural typing (duck typing מודרני) |
| בדיקה ב-runtime עם `isinstance` תמיד | רק עם `@runtime_checkable` |
| Heavy | Lightweight |

<p dir="rtl">
<b>Q: למה @runtime_checkable?</b>
</p>

<p dir="rtl">
Default Protocol הוא static-only — רק mypy בודק. עם <code>@runtime_checkable</code> אני יכול לכתוב <code>isinstance(x, TransactionView)</code>. במקרה שלי, רוב הוולידציה היא ב-Pydantic או ב-DB, אז זה backup.
</p>

### `backend/app/schemas/positions.py`

```python
class PositionSnapshot(BaseModel):
    client_id: str
    isin: str
    quantity: Decimal
    market_price: Decimal
    transaction_id: str | None = None


class PositionSchema(BaseModel):
    model_config = {"from_attributes": True}
    client_id: str
    isin: str
    quantity: Decimal
    average_cost: Decimal
    market_price: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal


class ClientPositionsResponse(BaseModel):
    model_config = {"from_attributes": True}
    client_id: str
    positions: list[PositionSchema]
    total_realized_pnl: Decimal
    total_unrealized_pnl: Decimal


class OpenLot(BaseModel):
    quantity: Decimal
    unit_cost: Decimal


class PositionState:
    """Mutable state during FIFO replay — NOT a Pydantic model."""
    def __init__(self, *, client_id: str, isin: str) -> None:
        self.client_id = client_id
        self.isin = isin
        self.open_lots: deque[OpenLot] = deque()
        self.realized_pnl = ZERO
        self.market_price = ZERO
        self.total_quantity = ZERO
        self.total_cost_basis = ZERO

    @property
    def quantity(self) -> Decimal:
        return self.total_quantity

    @property
    def average_cost(self) -> Decimal:
        if self.total_quantity == 0:
            return ZERO
        return _quantize_money(self.total_cost_basis / self.total_quantity)

    @property
    def unrealized_pnl(self) -> Decimal:
        return self.market_price * self.total_quantity - self.total_cost_basis

    def as_result(self) -> PositionSchema:
        return PositionSchema(
            client_id=self.client_id,
            isin=self.isin,
            quantity=self.total_quantity,
            average_cost=self.average_cost,
            market_price=self.market_price,
            realized_pnl=_quantize_money(self.realized_pnl),
            unrealized_pnl=_quantize_money(self.unrealized_pnl),
        )
```

### תפקיד של כל אחד

| Class | תפקיד |
|---|---|
| `PositionSnapshot` | קישור ויולציה ל-position (מינימלי — לא צריך P&L) |
| `PositionSchema` | אובייקט יציאה — מה שהאפליקציה מחזירה ושומרת |
| `ClientPositionsResponse` | wrapper של HTTP response עם totals |
| `OpenLot` | lot בודד ב-FIFO queue (quantity + unit_cost) |
| `PositionState` | mutable state בזמן הריצה של ה-FIFO. לא Pydantic — deque, mutation, properties. עובר פעם אחת ב-as_result() ל-Pydantic |

### למה `PositionState` לא Pydantic

<p dir="rtl">
Pydantic immutable by default. deque לא נתמך טוב ב-Pydantic. אנחנו עושים mutation מטורף (total_quantity += ..., open_lots.popleft()). Performance — Pydantic ולידציה בכל update = איטי.
</p>

### שאלה צפויה

<p dir="rtl">
<b>Q: למה unrealized_pnl הוא property ולא field?</b>
</p>

<p dir="rtl">
כדי שלא ייפול out-of-sync. ה-state מתעדכן באלפי עדכונים — אם הייתי שומר unrealized_pnl כ-field, הייתי צריך לעדכן אותו בכל buy/sell. כ-property, הוא מחושב on demand מה-running totals, ולעולם לא משקר.
</p>

---

## 6. ה-API Routes — שכבת ה-HTTP

### `backend/app/api/routes/__init__.py`

```python
router = APIRouter()
router.include_router(transactions_router)
router.include_router(clients_router)
router.include_router(positions_router)
router.include_router(violations_router)
router.include_router(analytics_router)
```

<p dir="rtl">
אגרגציה של כל ה-sub-routers ל-router יחיד ש-main.py רושם.
</p>

### Endpoint #1 — POST /upload-transactions

```python
@router.post("/upload-transactions", response_model=TransactionUploadResponse, status_code=201)
async def upload_transactions(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return await upload_transactions_by_file(file=file, db=db)
```

<p dir="rtl">
מקבל multipart/form-data עם file (File(...) = required). ה-db מוזרק דרך get_db. סטטוס 201 כי אנחנו יוצרים entities חדשים. ה-route דק במיוחד — כל הלוגיקה ב-service.
</p>

### Endpoint #2 — GET /clients

```python
@router.get("/clients", response_model=list[ClientResponse])
def get_clients(db: Session = Depends(get_db)):
    return list_clients(ClientRepository(db))
```

<p dir="rtl">
מחזיר רשימת לקוחות, ממוין אלפבטית. חשוב — קורא מ-<b>transactions</b> ולא מ-positions (פסקה 21 ב-AI_USAGE.md).
</p>

### Endpoint #3 — GET /clients/{client_id}/positions

```python
@router.get("/clients/{client_id}/positions", response_model=ClientPositionsResponse)
def get_client_positions(client_id: str, db: Session = Depends(get_db)):
    return list_positions_by_client(client_id=client_id, repository=PositionRepository(db))
```

<p dir="rtl">
מחזיר את כל הפוזיציות של הלקוח + סכומי P&L.
</p>

### Endpoint #4 — GET /violations

```python
@router.get("/violations", response_model=list[ViolationResponse])
def list_violations(client_id: str | None = Query(default=None), db: Session = Depends(get_db)):
    return list_violations_use_case(repository=ViolationRepository(db), client_id=client_id)
```

<p dir="rtl">
Optional filter ב-<code>?client_id=...</code>. ממוין לפי created_at DESC (חדשות ראשונות).
</p>

### Endpoint #5 — GET /analytics

```python
@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(db: Session = Depends(get_db)):
    return get_analytics_use_case(AnalyticsRepository(db))
```

<p dir="rtl">
כל האנליטיקות — מחושב בזמן הקריאה (לא cached).
</p>

### שאלות צפויות

<p dir="rtl">
<b>Q: למה ה-routes כל כך דקים?</b>
</p>

<p dir="rtl">
עיקרון של clean architecture — ה-routes הם adapters בלבד. הם פותחים את ה-HTTP envelope, קוראים ל-service, וסוגרים אותו. כל הלוגיקה ב-services. כך אני יכול לבדוק את ה-services ב-unit test בלי לעלות את ה-app.
</p>

<p dir="rtl">
<b>Q: למה Repository נוצר בתוך ה-route ולא דרך Depends?</b>
</p>

<p dir="rtl">
אפשר היה לעשות <code>Depends(PositionRepository)</code> עם קצת glue. בחרתי בפשטות — ה-route בונה את ה-repo כי הוא רק wrapper סביב db. ה-cost נמוך, וברור איפה כל repo נוצר.
</p>

<p dir="rtl">
<b>Q: למה את upload_transactions_by_file קוראים async, אבל את שאר ה-services לא?</b>
</p>

<p dir="rtl">
upload_transactions_by_file הוא async כי הוא קורא <code>await file.read()</code> (קריאה אסינכרונית של ה-upload). שאר ה-services לא עושים I/O — הם רק מטפלים בנתונים שכבר ב-RAM. אז sync.
</p>

---

## 7. Flow מלא: POST /upload-transactions

<p dir="rtl">
זהו ה-flow המרכזי. השקע 80% מההכנה בהבנה שלו.
</p>

### Code: [`transactions_service.py:27`](backend/app/services/transactions/transactions_service.py#L27)

```python
async def upload_transactions_by_file(file: UploadFile, db: Session) -> TransactionUploadResponse:
    transactions = TransactionRepository(db)
    positions = PositionRepository(db)
    violations = ViolationRepository(db)

    process_results = await process_transaction_upload(file)
    if process_results.has_errors:
        return failure_response(process_results)

    impacted_client_ids = sorted({record.client_id for record in process_results.records})

    incoming_ids = [record.transaction_id for record in process_results.records]
    has_within_batch_duplicates = len(set(incoming_ids)) != len(incoming_ids)
    if has_within_batch_duplicates or transactions.find_existing_transaction_ids(incoming_ids):
        raise DuplicateTransactionError()

    try:
        transactions.add_records(process_results.records)
        ordered_transactions = transactions.list_for_clients_ordered(impacted_client_ids)

        validate_transactions_can_build_positions(ordered_transactions)

        calculated_positions = calculate_fifo_positions(ordered_transactions)
        positions.update_clients_positions(impacted_client_ids, calculated_positions)

        position_snapshots = build_position_snapshots(ordered_transactions, calculated_positions)
        detected_violations = detect_violations(ordered_transactions, position_snapshots, PERSISTED_RULES)
        violations.update_clients_violations(impacted_client_ids, detected_violations)

        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise PersistenceError("Failed to persist uploaded transactions and positions.") from exc
    except Exception:
        db.rollback()
        raise

    return success_response(process_results)
```

### שלבים מפורטים

#### Step 1: יצירת repositories

```python
transactions = TransactionRepository(db)
positions = PositionRepository(db)
violations = ViolationRepository(db)
```

<p dir="rtl">
שלושה repos על אותו db session — שיתוף transaction (ACID).
</p>

#### Step 2: Parse + Validate

```python
process_results = await process_transaction_upload(file)
if process_results.has_errors:
    return failure_response(process_results)
```

<p dir="rtl">
קורא את ה-file (CSV / XLSX). מנרמל את ה-columns. בודק row-by-row. אם יש errors — חזרה מהירה עם 200 (סטטוס "failed" ב-payload, לא 400). זו החלטה מודעת ל-UX.
</p>

<p dir="rtl">
<b>שים לב:</b> failure_response עדיין עם status_code=201 של ה-route. זה כן באג קל — היה נכון יותר 4xx. שווה לציין אם שואלים.
</p>

#### Step 3: זיהוי לקוחות מושפעים

```python
impacted_client_ids = sorted({record.client_id for record in process_results.records})
```

<p dir="rtl">
set נותן distinct, sorted נותן דטרמיניזם. <b>חשוב:</b> רק הלקוחות שיש להם טרנזקציות בקובץ. אחרים לא מתבזבזים זמן עליהם.
</p>

#### Step 4: Duplicate detection (לפני INSERT)

```python
incoming_ids = [record.transaction_id for record in process_results.records]
has_within_batch_duplicates = len(set(incoming_ids)) != len(incoming_ids)
if has_within_batch_duplicates or transactions.find_existing_transaction_ids(incoming_ids):
    raise DuplicateTransactionError()
```

<p dir="rtl">
שתי בדיקות: בתוך אותו batch, וגם קיים ב-DB. סטטוס 409 Conflict — נכון סמנטית.
</p>

<p dir="rtl">
<b>למה לפני INSERT?</b> כי INSERT עם duplicate יזרוק IntegrityError, אבל אז כל ה-batch ייכשל. כאן אנחנו נכשלים cleanly לפני שמתחילים.
</p>

#### Step 5: Transaction סביב כל הכתיבה

```python
try:
    transactions.add_records(...)
    ordered_transactions = transactions.list_for_clients_ordered(impacted_client_ids)
    validate_transactions_can_build_positions(ordered_transactions)
    calculated_positions = calculate_fifo_positions(ordered_transactions)
    positions.update_clients_positions(...)
    position_snapshots = build_position_snapshots(...)
    detected_violations = detect_violations(...)
    violations.update_clients_violations(...)
    db.commit()
except SQLAlchemyError as exc:
    db.rollback()
    raise PersistenceError(...) from exc
except Exception:
    db.rollback()
    raise
```

##### Step 5a: INSERT transactions

```python
transactions.add_records(process_results.records)
```

<p dir="rtl">
<code>add_all([Transaction(**record.model_dump()) for record in records])</code> ואז flush — שולח ל-DB אבל לא commit.
</p>

##### Step 5b: קריאה מחדש מה-DB

```python
ordered_transactions = transactions.list_for_clients_ordered(impacted_client_ids)
```

<p dir="rtl">
<b>זה הקטע הקריטי.</b> למה לקרוא מחדש? כי ה-FIFO חייב את <b>כל ההיסטוריה</b> של ה-clients, לא רק את ה-batch החדש.
</p>

<p dir="rtl">
דוגמה: לקוח קנה 100 לפני שנה. עכשיו מוכר 50. אם נחשב FIFO רק על ה-batch הנוכחי, ה-sell ייפול (אין buy).
</p>

<p dir="rtl">
ה-flush ב-step 5a העביר את הנתונים ל-DB (זמין ב-SELECT), אבל לא נעשה commit.
</p>

##### Step 5c: Blocking validation

```python
validate_transactions_can_build_positions(ordered_transactions)
```

<p dir="rtl">
מריץ את BLOCKING_RULES (invalid_values, sell_before_buy). אם משהו נתפס — exception → rollback → response 400.
</p>

<p dir="rtl">
<b>למה לפני FIFO?</b> כי FIFO יתפוצץ על sell_before_buy. עדיף לתת error ברור.
</p>

##### Step 5d: FIFO

```python
calculated_positions = calculate_fifo_positions(ordered_transactions)
```

<p dir="rtl">
בונה את ה-state החדש מאפס. מחזיר <code>list[PositionSchema]</code> — מה שיהיה ב-DB.
</p>

##### Step 5e: Update positions

```python
positions.update_clients_positions(impacted_client_ids, calculated_positions)
```

<p dir="rtl">
DELETE של כל ה-positions של ה-impacted clients ואז INSERT של החדשות.
</p>

<p dir="rtl">
<b>למה DELETE+INSERT?</b> כי ה-FIFO החזיר את ה-state הסופי. UPSERT היה דורש לדעת מה השתנה — מורכב יותר ב-edge cases (פוזיציה ירדה ל-0).
</p>

##### Step 5f: Snapshots + Persistent rules

```python
position_snapshots = build_position_snapshots(ordered_transactions, calculated_positions)
detected_violations = detect_violations(ordered_transactions, position_snapshots, PERSISTED_RULES)
violations.update_clients_violations(impacted_client_ids, detected_violations)
```

<p dir="rtl">
בונה snapshots עם קישור לטרנזקציה האחרונה. מריץ persisted rules (day_trading, risk_concentration). מעדכן את violations table (DELETE+INSERT לפי client).
</p>

##### Step 5g: Commit

```python
db.commit()
```

<p dir="rtl">
<b>או הכל או כלום.</b> אם כל ה-block הצליח, commit. אחרת rollback.
</p>

### שני except — למה

```python
except SQLAlchemyError as exc:
    db.rollback()
    raise PersistenceError(...) from exc
except Exception:
    db.rollback()
    raise
```

<p dir="rtl">
<b>SQLAlchemyError</b> נעטף ב-PersistenceError עם הודעה ידידותית למשתמש (500).
</p>

<p dir="rtl">
<b>כל השאר</b> (ValidationAppError, InsufficientQuantityError) נזרק כפי שהוא (400 / 409).
</p>

<p dir="rtl">
בשני המקרים — rollback. בלי זה ה-session נשאר במצב לא תקין.
</p>

### שאלות צפויות

<p dir="rtl">
<b>Q: למה לא לחשב את ה-FIFO רק על ה-impacted ISINs ולא כל ה-(client, isin) pairs?</b>
</p>

<p dir="rtl">
ה-FIFO צריך את כל הטרנזקציות של הלקוח כדי להבין מה הוא מחזיק. אבל אופטימיזציה אפשרית היא לחשב FIFO רק על ה-(client, isin) שמופיעים ב-batch. כרגע אני מחשב לכל ה-clients המושפעים — כי הקוד פשוט יותר. ב-scale גדול היה שווה.
</p>

<p dir="rtl">
<b>Q: מה אם 2 uploads רצים במקביל לאותו client?</b>
</p>

<p dir="rtl">
אין locking. ה-Session של SQLAlchemy לא נועל positions של clients. שני workers יכולים לדרוס אחד את השני. בפרודקשן הייתי שם <code>SELECT ... FOR UPDATE</code> על שורות ה-positions של ה-clients, או — עדיף — מנגנון queue עם key=client_id.
</p>

<p dir="rtl">
<b>Q: למה db.flush() ב-add_records?</b>
</p>

<p dir="rtl">
כדי שה-list_for_clients_ordered שמיד נקרא יוכל לראות את הנתונים החדשים. בלי flush, ה-SQL לא נשלח ל-DB, ה-SELECT לא יראה. flush ≠ commit — flush שולח, commit סוגר את ה-transaction.
</p>

---

## 8. Data Ingestion — Pandas + Validation

### Step 1: [`utils/files.py`](backend/app/utils/files.py) — `read_table_from_file`

```python
async def read_table_from_file(file, allowed_extensions=(".csv", ".xlsx")) -> pd.DataFrame:
    if not has_allowed_extension(file.filename, allowed_extensions):
        raise UnsupportedUploadFileError()
    contents = await file.read()
    if not contents:
        raise EmptyUploadFileError(f"Uploaded file {file.filename} contains no data.")
    try:
        if Path(file.filename or "").suffix.lower() == ".csv":
            dataframe = pd.read_csv(BytesIO(contents), dtype=str)
        else:
            dataframe = pd.read_excel(BytesIO(contents), engine="openpyxl", dtype=str)
    except Exception as exc:
        raise UploadParseError() from exc
    if dataframe.empty:
        raise EmptyUploadFileError(...)
    return dataframe
```

### החלטות

<p dir="rtl">
<b>allowed_extensions</b> — בודק suffix של filename. לא MIME — easy to spoof. זה רק basic check.
</p>

<p dir="rtl">
<b>dtype=str — קריטי!</b> בלי זה pandas יחליט ש-"099" הוא integer ויחסיר את האפס. ה-ISIN נשבר. עם dtype=str הכל נשאר כסטרינג, וה-normalize יעשה את העבודה.
</p>

<p dir="rtl">
<b>BytesIO(contents)</b> — pandas רוצה file-like object. ה-contents הוא bytes. BytesIO עוטף.
</p>

<p dir="rtl">
<b>engine="openpyxl"</b> — לקרוא xlsx. ה-conventional choice.
</p>

### Step 2: [`dataframe.py`](backend/app/services/transactions/helpers/dataframe.py) — `normalize_transaction_dataframe`

```python
def normalize_transaction_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    normalized = dataframe.rename(
        columns=lambda column: COLUMN_ALIASES.get(compact_key(column), str(column))
    ).copy()

    missing = [column for column in REQUIRED_COLUMNS if column not in normalized.columns]
    if missing:
        raise ValidationAppError(f"Missing required transaction columns: {', '.join(missing)}.")

    normalized = normalized.loc[:, list(REQUIRED_COLUMNS)]
    for column in STRING_COLUMNS:
        normalized[column] = normalized[column].apply(normalize_string_cell)

    normalized["action"] = normalized["action"].apply(lambda v: v.lower() if isinstance(v, str) else v)
    normalized["quantity"] = normalized["quantity"].apply(parse_decimal_cell)
    normalized["price"] = normalized["price"].apply(parse_decimal_cell)
    normalized["timestamp"] = pd.to_datetime(normalized["timestamp"], errors="coerce")

    return normalized
```

### Column aliasing — איך זה עובד

```python
# constants.py
COLUMN_ALIASES = {
    "clientid": "client_id",
    "transactionid": "transaction_id",
    "isin": "isin",
    ...
}

# utils/dataframe.py
def compact_key(value: object) -> str:
    return "".join(char for char in str(value).strip().lower() if char.isalnum())
```

<p dir="rtl">
כל aliases לקובץ הם versions של compact key. "Client Id" → "clientid" → "client_id". מקבל גם ClientId, client_id, CLIENT_ID, Client-Id.
</p>

### `errors="coerce"` ב-`pd.to_datetime`

<p dir="rtl">
במקום לזרוק exception על תאריך לא חוקי, מחזיר NaT (Not-a-Time). אחר כך ה-validator בודק <code>pd.isna(row["timestamp"])</code> ומסמן את השורה כשגיאה. <b>למה?</b> כדי לאסוף את כל השגיאות, לא להיכשל על הראשונה.
</p>

### Step 3: `validate_transaction_dataframe`

```python
def validate_transaction_dataframe(dataframe) -> list[TransactionUploadError]:
    errors: list[TransactionUploadError] = []
    for index, row in dataframe.iterrows():
        row_number = int(index) + 2  # +2: header + 0-index

        for column in ("client_id", "transaction_id", "isin"):
            if is_blank_cell(row[column]):
                errors.append(_validation_error(row_number, column, "Value is required.", row[column]))

        if is_blank_cell(row["action"]) or row["action"] not in VALID_ACTIONS:
            errors.append(_validation_error(row_number, "action", "Action must be Buy or Sell.", row["action"]))

        errors.extend(_validate_positive_decimal(row_number, "quantity", "Quantity", row["quantity"]))
        errors.extend(_validate_positive_decimal(row_number, "price", "Price", row["price"]))

        if pd.isna(row["timestamp"]):
            errors.append(_validation_error(row_number, "timestamp", "Timestamp must be a valid date/time.", row["timestamp"]))

    return errors
```

### החלטות

<p dir="rtl">
<b>row_number = index + 2</b> — Excel/CSV מתחיל בשורה 1 (header). DataFrame index הוא 0-based. שורה במציאות = index + 2.
</p>

<p dir="rtl">
<b>אוסף את כל השגיאות, לא מפסיק</b> — UX.
</p>

<p dir="rtl">
<b>is_blank_cell</b> — בודק None, NaN, ו-empty string.
</p>

<p dir="rtl">
<b>_validate_positive_decimal</b> — מחזיר list (לא raise) → אפשר להוסיף בקלות לכל ה-errors.
</p>

### Step 4: `transaction_records_from_dataframe`

```python
def transaction_records_from_dataframe(dataframe) -> list[TransactionIngested]:
    return [
        TransactionIngested(
            client_id=row["client_id"],
            transaction_id=row["transaction_id"],
            isin=row["isin"],
            action=row["action"],
            quantity=row["quantity"],
            price=row["price"],
            timestamp=row["timestamp"].to_pydatetime(),
        )
        for row in dataframe.to_dict("records")
    ]
```

<p dir="rtl">
מ-DataFrame ל-Pydantic models. <code>.to_pydatetime()</code> ממיר pandas Timestamp ל-Python datetime.
</p>

<p dir="rtl">
<b>Pydantic validation שוב!</b> TransactionIngested מוודא <code>quantity > 0, price > 0, action in ['buy','sell']</code>. Defense in depth.
</p>

### שאלות צפויות

<p dir="rtl">
<b>Q: למה לא להשתמש ב-Pydantic ישירות במקום validate_transaction_dataframe?</b>
</p>

<p dir="rtl">
Pydantic נכשל ב-error הראשון של כל instance. אני רוצה לאסוף את כל השגיאות של כל השורות בפעם אחת — חוויית משתמש. אפשר היה לעשות try/except סביב כל Pydantic instantiation, אבל זה ה-anti-pattern של exceptions for flow control.
</p>

<p dir="rtl">
<b>Q: מה אם הקובץ הוא 1GB?</b>
</p>

<p dir="rtl">
כרגע הכל נטען ל-RAM. לסקייל הייתי משתמש ב-<code>pd.read_csv(chunksize=10000)</code> ועובד chunk by chunk. גם ה-validation חייב להיות streaming. ה-FIFO על client בודד יכול להישאר in-memory.
</p>

<p dir="rtl">
<b>Q: מה אם ה-Excel מכיל formula cells?</b>
</p>

<p dir="rtl">
<code>dtype=str</code> לא משפיע על formulas — openpyxl מחזיר את ה-result, לא את הנוסחה עצמה. אם רוצים את הנוסחה: <code>data_only=False</code>. אני לוקח את result כי זה מה שמשתמשים מצפים.
</p>

---

## 9. ה-FIFO Engine — הלב הפיננסי

<p dir="rtl">
מיקום הקובץ: <code>backend/app/services/positions/helpers/fifo_engine.py</code>
</p>

### הקונספט של FIFO

<p dir="rtl">
FIFO = First In, First Out. כשמוכרים, צורכים מה-lot הכי <b>ישן</b> קודם.
</p>

### דוגמה — Walkthrough מלא

| Action | Quantity | Price | State |
|---|---|---|---|
| Buy | 10 | $100 | Lots: [(10, $100)], qty=10, cost_basis=1000 |
| Buy | 10 | $110 | Lots: [(10, $100), (10, $110)], qty=20, cost_basis=2100 |
| Sell | 15 | $120 | (חישוב מטה) |

<p dir="rtl">
<b>חישוב ה-sell:</b>
</p>

<p dir="rtl">
שלב 1 — צריך 15. ה-lot הראשון יש בו 10 → consume 10:
</p>

- `realized_pnl += 10 * (120 - 100) = +200`
- `total_quantity -= 10` → 10
- `total_cost_basis -= 10 * 100 = 1000` → 1100
- `lots.popleft()` (לוט ריק)
- `remaining = 5`

<p dir="rtl">
שלב 2 — ה-lot הראשון (כעת השני המקורי) יש בו 10 → consume 5:
</p>

- `realized_pnl += 5 * (120 - 110) = +50`
- `total_quantity -= 5` → 5
- `total_cost_basis -= 5 * 110 = 550` → 550
- lot.quantity = 5, לא popleft
- `remaining = 0`

<p dir="rtl">
<b>Result:</b>
</p>

- `quantity = 5`
- `average_cost = 550 / 5 = 110`
- `realized_pnl = 250`
- `unrealized_pnl = 120 * 5 - 550 = 600 - 550 = 50`
- `market_price = 120` (last seen)

<p dir="rtl">
זה בדיוק מה שהtest <code>test_fifo_calculates_realized_and_unrealized_pnl</code> מאמת. דע אותו בעל-פה.
</p>

### הקוד שורה אחר שורה

```python
def calculate_fifo_positions(transactions: Iterable[TransactionView]) -> list[PositionSchema]:
    positions: dict[tuple[str, str], PositionState] = {}

    for transaction in sorted(transactions, key=sort_by_timestamp_id_and_transaction_id):
        position = _position_for_transaction(positions, transaction)
        position.market_price = transaction.price

        if transaction.action == "buy":
            _apply_buy(transaction, position)
        elif transaction.action == "sell":
            _apply_sell(transaction, position)
        else:
            raise ValidationAppError(f"Unsupported transaction action: {transaction.action}.")

    return [position.as_result() for position in positions.values()]
```

### `dict[tuple[str, str], PositionState]`

<p dir="rtl">
המפתח הוא (client_id, isin) — כל זוג מקבל state נפרד.
</p>

### `sort_by_timestamp_id_and_transaction_id`

```python
# utils/sorters.py
def sort_by_timestamp_id_and_transaction_id(t):
    return (t.timestamp, getattr(t, "id", 0), t.transaction_id)
```

<p dir="rtl">
שלוש רמות tiebreaker. אם timestamp זהה (יכול לקרות) → לפי id (DB auto-increment, סדר הכנסה). ואם גם id זהה → לפי transaction_id אלפבטית. <b>תוצאה: deterministic ordering.</b>
</p>

### `position.market_price = transaction.price`

<p dir="rtl">
בכל איטרציה, ה-market_price הוא ה-last seen של ה-ISIN. זה לא market data אמיתי — זה רק "המחיר האחרון שראינו בטרנזקציה". בפרודקשן market_price צריך לבוא מ-feed חיצוני.
</p>

### `_apply_buy`

```python
def _apply_buy(transaction, position):
    position.open_lots.append(OpenLot(quantity=transaction.quantity, unit_cost=transaction.price))
    position.total_quantity += transaction.quantity
    position.total_cost_basis += transaction.quantity * transaction.price
```

<p dir="rtl">
מוסיף lot חדש לקצה ה-deque. מעדכן running totals. <b>O(1).</b>
</p>

### `_apply_sell`

```python
def _apply_sell(transaction, position):
    remaining = transaction.quantity
    lots = position.open_lots

    while remaining > 0 and lots:
        oldest_lot = lots[0]
        consumed = min(oldest_lot.quantity, remaining)
        position.realized_pnl += consumed * (transaction.price - oldest_lot.unit_cost)
        position.total_quantity -= consumed
        position.total_cost_basis -= consumed * oldest_lot.unit_cost
        oldest_lot.quantity -= consumed
        remaining -= consumed

        if oldest_lot.quantity == 0:
            lots.popleft()

    if remaining > 0:
        raise InsufficientQuantityError(...)
```

### למה `deque` ולא `list`

<p dir="rtl">
<code>list.pop(0)</code> הוא O(n) — Python צריך להזיז את כל האיברים אחורה. <code>deque.popleft()</code> הוא O(1) — קצה רישום. על קובץ של 100k טרנזקציות עם הרבה sells, ההבדל הוא O(n) מול O(n²). <b>תיקון מוסבר ב-AI_USAGE.md.</b>
</p>

### חישוב `realized_pnl`

```
realized_pnl += consumed * (sell_price - buy_price_of_oldest_lot)
```

<p dir="rtl">
זה הרווח מכל יחידה שנמכרה.
</p>

### Defense-in-depth

```python
if remaining > 0:
    raise InsufficientQuantityError(...)
```

<p dir="rtl">
זה היה צריך להיתפס ב-validate_transactions_can_build_positions למעלה (BLOCKING_RULES → sell_before_buy). ה-comment בקוד מבהיר את זה — "Reaching here means the rule and the engine disagree on what 'available' means — surface it loudly."
</p>

### שאלות צפויות

<p dir="rtl">
<b>Q: מה ההבדל בין FIFO ל-LIFO?</b>
</p>

<p dir="rtl">
LIFO = Last In, First Out. מוכרים מה-lot החדש קודם. בארה"ב יש משמעות מס: FIFO נותן realized P&L גבוה בשוק עולה (קונים זול לפני), LIFO נותן נמוך. רוב המערכות מבוססות FIFO. השאלה כן תלויה בחוק המקומי.
</p>

<p dir="rtl">
<b>Q: מה הסיבוכיות של ה-algorithm?</b>
</p>

<p dir="rtl">
Amortized O(n) — כל טרנזקציה מוסיפה lot אחד (append) ו-sells מוציאים lots (popleft). כל lot נכנס פעם אחת ויוצא פעם אחת לכל היותר. גם המיון הראשוני הוא O(n log n) אבל deterministic.
</p>

<p dir="rtl">
<b>Q: מה אם sell יותר מ-buy total?</b>
</p>

<p dir="rtl">
ה-validate_transactions_can_build_positions יתפוס את זה ויעצור לפני שה-FIFO רץ. ה-InsufficientQuantityError ב-FIFO זה safety net אם הוולידציה לא תפסה — לא אמור לקרות, אבל יותר טוב להתפוצץ loudly מאשר להחזיר state שגוי.
</p>

<p dir="rtl">
<b>Q: למה total_quantity ו-total_cost_basis running?</b>
</p>

<p dir="rtl">
אופטימיזציה. בלי running totals, כל קריאה ל-<code>quantity</code> הייתה דורשת <code>sum(lot.quantity for lot in lots)</code> = O(lots). עם running, זה O(1). חשוב כי unrealized_pnl קורא ל-total_cost_basis בכל read.
</p>

---

## 10. P&L — Realized + Unrealized

### חישוב Realized P&L (ב-`_apply_sell`)

```python
position.realized_pnl += consumed * (transaction.price - oldest_lot.unit_cost)
```

<p dir="rtl">
מצטבר. לעולם לא יורד (אלא אם buy_cost > sell_price → realized הוא שלילי, אבל בידיים נצברנו). הפשט: לכל יחידה שמוכרים, הרווח = price_sold - price_bought.
</p>

### חישוב Unrealized P&L (ב-`PositionState.unrealized_pnl`)

```python
@property
def unrealized_pnl(self) -> Decimal:
    return self.market_price * self.total_quantity - self.total_cost_basis
```

### למה לא `(market_price - average_cost) * quantity`

<p dir="rtl">
average_cost = total_cost_basis / total_quantity — חישוב עם חילוק. חילוק על Decimal יוצר רידוד (לדוגמה: 1000/3 = 333.333333...). אם אז כופלים, ה-rounding מצטבר.
</p>

<p dir="rtl">
הנוסחה הנכונה: <code>market_price * quantity - cost_basis</code> — <b>בלי חילוק עד הסוף.</b>
</p>

### דוגמה ל-rounding drift

<p dir="rtl">
מקרה A — 3 buys: 1 @ $100, 1 @ $200, 1 @ $300. cost_basis = 600, quantity = 3.
</p>

- average_cost = 600/3 = 200 ✅ נקי
- market_price = 200. unrealized = (200-200)*3 = 0 ✅

<p dir="rtl">
מקרה B — 1 @ $1, 1 @ $1, 1 @ $1. average_cost = 1/3 = 0.333333...
</p>

- אם quantize ל-6 ספרות → 0.333333
- unrealized = (1 - 0.333333) * 3 = 2.000001 (drift!)
- הנוסחה הנכונה: 1*3 - 1 = 2 ✅

### Quantization בנקודות יציאה

```python
def as_result(self) -> PositionSchema:
    return PositionSchema(
        ...
        realized_pnl=_quantize_money(self.realized_pnl),
        unrealized_pnl=_quantize_money(self.unrealized_pnl),
    )


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_EVEN)
```

<p dir="rtl">
<code>MONEY_QUANTUM = Decimal("0.000001")</code> — 6 ספרות אחרי הנקודה (תואם Numeric(18,6) ב-DB). ROUND_HALF_EVEN — banker's rounding. מעוגל ל-זוגי הקרוב. מונע bias מצטבר.
</p>

### שאלה צפויה

<p dir="rtl">
<b>Q: מה ההבדל בין ROUND_HALF_UP ל-ROUND_HALF_EVEN?</b>
</p>

- HALF_UP: 0.5 → 1, 1.5 → 2, 2.5 → 3. כל .5 כלפי מעלה. → bias כלפי מעלה
- HALF_EVEN: 0.5 → 0, 1.5 → 2, 2.5 → 2. ל-זוגי הקרוב

<p dir="rtl">
ב-finance — HALF_EVEN הוא הסטנדרט (IEEE 754, GAAP, IFRS). מונע over-statement בסכומים גדולים.
</p>

---

## 11. Position Snapshots — הגשר לוויולציות

<p dir="rtl">
מיקום הקובץ: <code>backend/app/services/positions/helpers/snapshots.py</code>
</p>

```python
def build_position_snapshots(
    transactions: list[TransactionView],
    positions: Iterable[PositionView],
) -> list[PositionSnapshot]:
    latest_transaction_ids = {
        (t.client_id, t.isin): t.transaction_id
        for t in transactions
    }
    return [
        PositionSnapshot(
            client_id=position.client_id,
            isin=position.isin,
            quantity=position.quantity,
            market_price=position.market_price,
            transaction_id=latest_transaction_ids.get((position.client_id, position.isin)),
        )
        for position in positions
        if position.quantity > 0
    ]
```

### מה זה עושה

<p dir="rtl">
בונה מפה של (client, isin) → transaction_id — האחרון יזכה (dict comprehension overwrites). ואז לכל position עם quantity > 0 (לא מחזיק כלום → לא רלוונטי), יוצר snapshot שכולל את transaction_id של הטרנזקציה האחרונה של אותו (client, isin).
</p>

### למה צריך את זה

<p dir="rtl">
ה-Violation table דורש transaction_id (FK). ויולציה של risk_concentration קשורה ל-position שלמה, לא לטרנזקציה אחת. ה-pointer לטרנזקציה האחרונה הוא "best effort" — מציין את ה-trigger.
</p>

### למה `if position.quantity > 0`

<p dir="rtl">
positions עם quantity=0 לא משמעותיות. לא בודקים concentration עליהן.
</p>

### שאלה צפויה

<p dir="rtl">
<b>Q: למה לא לקשור את הויולציה ל-position_id במקום transaction_id?</b>
</p>

<p dir="rtl">
טוב חשבת! זה היה עיצוב נכון יותר — <code>FK(violations.position_id) → positions.id</code>. כרגע אני שומר את transaction_id כי זה Heritage מקריאת הדרישות, ויש שווי מסוים — אם משתמש רוצה לדעת "איזו טרנזקציה גרמה לזה?", יש לו answer. בריפקטור הייתי שוקל.
</p>

---

## 12. Violations — 4 חוקים, 2 רמות

<p dir="rtl">
מיקום: <code>backend/app/services/violations/</code>
</p>

### מבנה ה-rules

```python
# violations_service.py
DEFAULT_RULES: tuple[ViolationRule, ...] = (
    detect_invalid_values,
    detect_sell_before_buy,
    detect_day_trading,
    detect_risk_concentration,
)

BLOCKING_RULES: tuple[ViolationRule, ...] = (
    detect_invalid_values,
    detect_sell_before_buy,
)

PERSISTED_RULES: tuple[ViolationRule, ...] = tuple(
    rule for rule in DEFAULT_RULES if rule not in BLOCKING_RULES
)
```

### למה ההפרדה

<p dir="rtl">
<b>Blocking</b> — ERROR. אסור לעבד. הקובץ נדחה.
</p>

<p dir="rtl">
<b>Persisted</b> — WARNING. מאוחסן ב-DB אבל לא חוסם.
</p>

<p dir="rtl">
<code>PERSISTED = DEFAULT - BLOCKING</code>. אם מוסיפים rule, פשוט להוסיף ל-DEFAULT ולסווג blocking/non.
</p>

### Rules are just functions

```python
ViolationRule = Callable[[ClientContext], list[ViolationDraft]]
```

<p dir="rtl">
אין class hierarchy. אין @abstractmethod. פונקציה פשוטה: ClientContext פנימה, list of drafts החוצה.
</p>

<p dir="rtl">
<b>תועלת:</b> בדיקה פשוטה (<code>detect_day_trading(ctx)</code>), הרכבה פשוטה (<code>for rule in rules: drafts.extend(rule(ctx))</code>).
</p>

<p dir="rtl">
<b>למה לא class?</b> YAGNI. אם מחר נצטרך rule עם state — אז class. כרגע — overkill.
</p>

### `ClientContext` — איך הוא נבנה

```python
def detect_violations(transactions, positions, rules=DEFAULT_RULES) -> list[ViolationDraft]:
    transactions_by_client: dict[str, list[TransactionView]] = defaultdict(list)
    positions_by_client: dict[str, list[PositionSnapshot]] = defaultdict(list)

    for t in transactions:
        transactions_by_client[t.client_id].append(t)
    for p in positions:
        snap = position_snapshot_from(p)
        positions_by_client[snap.client_id].append(snap)

    drafts: list[ViolationDraft] = []
    client_ids = sorted(set(transactions_by_client) | set(positions_by_client))

    for client_id in client_ids:
        ctx = ClientContext(
            client_id=client_id,
            transactions=sorted(transactions_by_client[client_id], key=sort_by_timestamp_and_id),
            positions=positions_by_client[client_id],
        )
        for rule in rules:
            drafts.extend(rule(ctx))

    return drafts
```

<p dir="rtl">
קבוצה את כל הטרנזקציות והפוזיציות לפי client. לכל client → ClientContext עם הכל ממוין. מריץ את כל ה-rules על אותו ctx.
</p>

### Rule #1: `detect_invalid_values`

```python
def detect_invalid_values(ctx: ClientContext) -> list[ViolationDraft]:
    drafts: list[ViolationDraft] = []
    for t in ctx.transactions:
        offenders = []
        if t.quantity < 0:
            offenders.append(f"quantity={t.quantity}")
        if t.price < 0:
            offenders.append(f"price={t.price}")
        if offenders:
            drafts.append(ViolationDraft(
                client_id=ctx.client_id,
                transaction_id=t.transaction_id,
                violation_type=ViolationType.INVALID_VALUES,
                severity=ViolationSeverity.ERROR,
                message=f"Negative value(s): {', '.join(offenders)}.",
            ))
    return drafts
```

<p dir="rtl">
בודק רק שלילי, לא אפס. המטלה הייתה <code>&lt; 0</code>. אם רוצים <code>&lt;= 0</code>, צריך לעדכן. האמת — ה-validate_transaction_dataframe חוסם הכל <code>&lt;= 0</code> באמת. אז כאן זה defense-in-depth.
</p>

### Rule #2: `detect_sell_before_buy`

```python
def detect_sell_before_buy(ctx: ClientContext) -> list[ViolationDraft]:
    running: dict[str, Decimal] = defaultdict(Decimal)
    drafts: list[ViolationDraft] = []
    transactions = sorted(ctx.transactions, key=sort_by_timestamp)

    for transaction in transactions:
        if transaction.action == "buy":
            running[transaction.isin] += transaction.quantity
        elif transaction.action == "sell":
            if transaction.quantity > running[transaction.isin]:
                drafts.append(ViolationDraft(
                    client_id=ctx.client_id,
                    transaction_id=transaction.transaction_id,
                    violation_type=ViolationType.SELL_BEFORE_BUY,
                    severity=ViolationSeverity.ERROR,
                    message=(
                        f"Sell of {transaction.quantity} {transaction.isin} "
                        f"exceeds available position ({running[transaction.isin]})."
                    ),
                ))
            running[transaction.isin] -= transaction.quantity
    return drafts
```

### החלטה: אחרי שגיאה ממשיכים

<p dir="rtl">
ה-running יורד מתחת לאפס. ה-sell הבא יושווה למספר שלילי. אם sell יותר → עוד flag. הבנה: test <code>test_sell_before_buy_rule_flags_uncovered_sell</code> מוכיח שגם T1 וגם T3 נדגלים.
</p>

### Rule #3: `detect_day_trading` — הכי מתוחכם

```python
def detect_day_trading(ctx: ClientContext) -> list[ViolationDraft]:
    transactions_by_isin: dict[str, list[TransactionView]] = defaultdict(list)
    for t in ctx.transactions:
        transactions_by_isin[t.isin].append(t)

    return [
        ViolationDraft(
            client_id=ctx.client_id,
            transaction_id=txns[-1].transaction_id,
            violation_type=ViolationType.DAY_TRADING,
            severity=ViolationSeverity.WARNING,
            message=f"{pairs} buy/sell pairs of {isin} within 24h (threshold: >{DAY_TRADING_PAIR_THRESHOLD}).",
        )
        for isin, txns in transactions_by_isin.items()
        if (pairs := _max_pairs_in_window(txns)) > DAY_TRADING_PAIR_THRESHOLD
    ]
```

### `_max_pairs_in_window` — Sliding window

```python
def _max_pairs_in_window(transactions: list[TransactionView]) -> int:
    buys: deque = deque()
    sells: deque = deque()
    max_pairs = 0

    for transaction in transactions:
        cutoff = transaction.timestamp - DAY_TRADING_WINDOW

        while buys and buys[0] <= cutoff:
            buys.popleft()
        while sells and sells[0] <= cutoff:
            sells.popleft()

        if transaction.action == "buy":
            buys.append(transaction.timestamp)
        else:
            sells.append(transaction.timestamp)

        max_pairs = max(max_pairs, min(len(buys), len(sells)))

    return max_pairs
```

### ההברקה

<p dir="rtl">
"Pair" = buy + sell. מספר ה-pairs בחלון = <code>min(len(buys), len(sells))</code>. אם בשלב כלשהו זה גדול מ-3 → flag.
</p>

### חשוב — boundary `<=`

```python
while buys and buys[0] <= cutoff:
    buys.popleft()
```

<p dir="rtl">
חלון (cutoff, current] — half-open. טרייד <b>בדיוק</b> 24h לאחור הוא <b>מחוץ</b> לחלון. <code>&lt;</code> היה משאיר אותו בפנים — bug. <b>AI_USAGE.md מציין את זה כתיקון!</b>
</p>

### דוגמה

| Time | Action | Buys | Sells | Pairs |
|---|---|---|---|---|
| 00:00 | buy | [0] | [] | 0 |
| 02:00 | sell | [0] | [2] | 1 |
| 04:00 | buy | [0,4] | [2] | 1 |
| 06:00 | sell | [0,4] | [2,6] | 2 |
| 08:00 | buy | [0,4,8] | [2,6] | 2 |
| 10:00 | sell | [0,4,8] | [2,6,10] | 3 |
| 12:00 | buy | [0,4,8,12] | [2,6,10] | 3 |
| 14:00 | sell | [0,4,8,12] | [2,6,10,14] | **4 → FLAG!** |

### Complexity

<p dir="rtl">
O(n) — כל טרנזקציה נכנסת ויוצאת פעם אחת לכל היותר מה-deque. amortized O(1) לכל איטרציה.
</p>

### Rule #4: `detect_risk_concentration`

```python
def detect_risk_concentration(ctx: ClientContext) -> list[ViolationDraft]:
    if not ctx.positions:
        return []

    market_values = [(p, p.quantity * p.market_price) for p in ctx.positions]
    total_market_value = sum((mv for _, mv in market_values), ZERO)

    if total_market_value <= 0:
        return []

    return [
        ViolationDraft(
            client_id=ctx.client_id,
            transaction_id=position.transaction_id,
            violation_type=ViolationType.RISK_CONCENTRATION,
            severity=ViolationSeverity.WARNING,
            message=f"{position.isin} is {percentage(mv, total_market_value)}% of portfolio (threshold: 50%).",
        )
        for position, mv in market_values
        if (mv / total_market_value) > RISK_CONCENTRATION_THRESHOLD
    ]
```

### גישות

<p dir="rtl">
Market value = quantity * market_price לכל position. Total = sum. אם <code>&gt; 50%</code> → WARNING. ה-transaction_id של ה-violation = הטרנזקציה האחרונה של ה-(client, isin) — דרך ה-snapshot.
</p>

### Edge cases מטופלים

- אין positions → `[]`
- `total <= 0` → `[]` (מונע ZeroDivisionError, וגם מקרה non-sensical)

### `validate_transactions_can_build_positions`

```python
def validate_transactions_can_build_positions(transactions: list[TransactionView]) -> None:
    drafts = detect_violations(transactions, [], BLOCKING_RULES)
    if not drafts:
        return

    messages = "; ".join(d.message for d in drafts)
    if any(d.violation_type == ViolationType.SELL_BEFORE_BUY for d in drafts):
        raise InsufficientQuantityError(messages)
    raise ValidationAppError(messages)
```

<p dir="rtl">
מריץ blocking rules על transactions בלבד (בלי positions, כי עוד לא חישבנו). אם משהו נתפס → exception עם כל ההודעות מחוברות. חשוב: SELL_BEFORE_BUY → InsufficientQuantityError (status 400, message ספציפי). אחרים → ValidationAppError.
</p>

### שאלות צפויות

<p dir="rtl">
<b>Q: למה לסדר rules ב-tuples ולא ב-list?</b>
</p>

<p dir="rtl">
Immutability. tuple אומר "זה לא ישתנה בריצה". גם משתמש בו כ-frozen identity. set comparisons (isdisjoint) עובדות.
</p>

<p dir="rtl">
<b>Q: מה אם מוסיפים rule חדש?</b>
</p>

<p dir="rtl">
מוסיפים פונקציה ב-detectors/. מוסיפים ל-DEFAULT_RULES ב-violations_service.py. אם blocking → גם ל-BLOCKING_RULES. ה-test <code>test_persisted_rules_exclude_blocking_rules</code> מוודא שאין overlap.
</p>

<p dir="rtl">
<b>Q: למה day_trading מחזיר רק violation אחת ל-ISIN, גם אם הסף נחצה כמה פעמים?</b>
</p>

<p dir="rtl">
ה-rule מחזיר את ה-max_pairs בחלון, וב-flag אחד. אם רוצים פר event, היה צריך לאסוף בכל חציית סף. החלטה — פחות רעש בטבלה. אם משתמש רוצה לדעת בדיוק מתי, יסתכל בטרנזקציות.
</p>

---

## 13. Analytics — 4 חישובים

<p dir="rtl">
מיקום: <code>backend/app/services/analytics/</code>
</p>

### Calculation #1: Top Traded ISINs

```python
def calculate_top_traded_isins(transactions, limit=TOP_TRADED_LIMIT) -> list[TopTradedIsin]:
    counts = Counter(sorted(t.isin for t in transactions))
    return [
        TopTradedIsin(isin=isin, transaction_count=transaction_count)
        for isin, transaction_count in counts.most_common(limit)
    ]
```

### `sorted` לפני Counter — למה

<p dir="rtl">
<code>Counter.most_common()</code> עם ties (counts זהים) מחזיר ב-insertion order. אם אני רוצה דטרמיניזם — שני ISINs עם 5 trades יוחזרו אלפבטית — מיון לפני בונה את ה-Counter בסדר יציב.
</p>

### `TOP_TRADED_LIMIT = 3`

<p dir="rtl">
מתועד ב-constants — נדרש על-ידי המטלה.
</p>

### Calculation #2: Average Holding Time

### הקונספט

<p dir="rtl">
"כמה זמן בממוצע כל share שנמכר הוחזק"
</p>

### FIFO מקביל אבל לטרגט אחר

```python
def calculate_average_holding_time_per_client(transactions) -> list[ClientAverageHoldingTime]:
    client_ids = sorted({t.client_id for t in transactions})
    holdings_by_asset: dict[tuple[str, str], deque[HoldingLot]] = defaultdict(deque)
    totals_by_client: dict[str, HoldingTimeTotals] = defaultdict(HoldingTimeTotals)

    for transaction in transactions:
        holdings = holdings_by_asset[(transaction.client_id, transaction.isin)]
        if transaction.action == "buy":
            _apply_open_holding(transaction, holdings)
        elif transaction.action == "sell":
            _apply_close_holding(transaction, holdings, totals_by_client[transaction.client_id])
        else:
            raise ValidationAppError(...)

    return [_holding_time_result(client_id, totals_by_client[client_id]) for client_id in client_ids]
```

### `HoldingLot` — בלי מחיר, רק זמן

```python
class HoldingLot(BaseModel):
    quantity: Decimal
    timestamp: datetime
```

### `_apply_close_holding` — צובר את הזמן

```python
while remaining > 0 and holdings:
    oldest_lot = holdings[0]
    closed_quantity = min(oldest_lot.quantity, remaining)
    holding_seconds = Decimal(str((transaction.timestamp - oldest_lot.timestamp).total_seconds()))
    holding_totals.record_closed_holding(holding_seconds, closed_quantity)
    oldest_lot.quantity -= closed_quantity
    remaining -= closed_quantity
    if oldest_lot.quantity == 0:
        holdings.popleft()
```

### `HoldingTimeTotals` — Weighted accumulator

```python
class HoldingTimeTotals(BaseModel):
    quantity_weighted_holding_seconds: Decimal = Decimal("0")
    closed_quantity: Decimal = Decimal("0")

    def record_closed_holding(self, holding_seconds, quantity):
        self.quantity_weighted_holding_seconds += holding_seconds * quantity
        self.closed_quantity += quantity
```

### `_average_holding_seconds`

```python
def _average_holding_seconds(holding_totals):
    if holding_totals.closed_quantity == 0:
        return ZERO
    return (holding_totals.quantity_weighted_holding_seconds / holding_totals.closed_quantity).quantize(CENT)
```

### למה weighted-by-quantity

<p dir="rtl">
דוגמה: קנה 1000 share, החזיק שנייה אחת, מכר. ואז קנה 1 share, החזיק שנה, מכר.
</p>

- ממוצע פשוט = (1 שנייה + 1 שנה) / 2 ≈ חצי שנה. **שקרי.**
- Weighted = (1000 * 1 שנייה + 1 * 31M שנייה) / 1001 ≈ 30 שנייה
- משקף "כמה שיווי הוחזק" — הרבה יותר נכון

### `Decimal(str(...))` — למה

<p dir="rtl">
<code>(t1 - t2).total_seconds()</code> הוא float. <code>Decimal(float)</code> נותן "סיומת ארוכה" עם ספרות שגויות. <code>Decimal(str(float))</code> נכון.
</p>

### Calculation #3: Most Volatile Client

### הקונספט

<p dir="rtl">
"מי הלקוח שערך הפורטפוליו שלו השתנה הכי הרבה"
</p>

### Replay של כל הטרנזקציות

```python
def calculate_most_volatile_client(transactions) -> MostVolatileClient | None:
    candidates = (
        _client_volatility(client_id, client_transactions)
        for client_id, client_transactions in sorted(_transactions_by_client(transactions).items())
    )
    return max(candidates, key=lambda c: c.value_range, default=None)


def _client_volatility(client_id, transactions) -> MostVolatileClient:
    quantities: dict[str, Decimal] = defaultdict(lambda: ZERO)
    prices: dict[str, Decimal] = {}
    min_value: Decimal | None = None
    max_value: Decimal | None = None

    for transaction in transactions:
        if transaction.action == "buy":
            quantities[transaction.isin] += transaction.quantity
        elif transaction.action == "sell":
            quantities[transaction.isin] -= transaction.quantity

        prices[transaction.isin] = transaction.price
        portfolio_value = _portfolio_value(quantities, prices)
        min_value = portfolio_value if min_value is None else min(min_value, portfolio_value)
        max_value = portfolio_value if max_value is None else max(max_value, portfolio_value)

    min_value = min_value or ZERO
    max_value = max_value or ZERO
    return MostVolatileClient(
        client_id=client_id,
        min_portfolio_value=min_value,
        max_portfolio_value=max_value,
        value_range=max_value - min_value,
    )


def _portfolio_value(quantities, prices) -> Decimal:
    return sum(q * prices[isin] for isin, q in quantities.items() if q > 0)
```

### החלטות

<p dir="rtl">
כל טרייד מעדכן את ה-prices של ה-ISIN ("last seen as market price"). מחשב portfolio_value אחרי כל טרייד. עוקב אחרי min/max throughout time. <code>value_range = max - min</code> = volatility metric. <code>max(candidates, key=value_range)</code> → ה-client הכי תנודתי. <code>if quantity &gt; 0</code> ב-_portfolio_value — מתעלם מ-short positions (לא תומכים).
</p>

### Calculation #4: ISIN Concentration

### הקונספט

<p dir="rtl">
"ISINs שמוחזקים על-ידי יותר מ-70% מהלקוחות"
</p>

```python
def calculate_isin_concentration_report(transactions, positions) -> list[IsinConcentrationEntry]:
    total_clients = len({t.client_id for t in transactions})
    if total_clients == 0:
        return []

    report: list[IsinConcentrationEntry] = []
    clients_by_isin: dict[str, set[str]] = defaultdict(set)
    for position in positions:
        if position.quantity > 0:
            clients_by_isin[position.isin].add(position.client_id)

    sorted_clients = sorted(clients_by_isin.items())

    for isin, holders in sorted_clients:
        clients = sorted(holders)
        client_percentage = percentage(Decimal(len(clients)), Decimal(total_clients))
        if client_percentage > ANALYTICS_CONCENTRATION_THRESHOLD:
            report.append(IsinConcentrationEntry(
                isin=isin,
                client_count=len(clients),
                client_percentage=client_percentage,
                clients=clients,
            ))
    return report
```

### `total_clients` מתוך **transactions**, לא positions

<p dir="rtl">
ייתכן שיש לקוח עם 0 positions (קנה ומכר הכל). הוא עדיין לקוח. ה-total_clients כולל אותו.
</p>

### `if position.quantity > 0`

<p dir="rtl">
רק positions שעדיין מוחזקות.
</p>

### sorted clients & sorted_clients

<p dir="rtl">
דטרמיניזם ב-output.
</p>

### שאלה מסוכנת

<p dir="rtl">
<b>Q: מה ההבדל בין detect_risk_concentration (violation) ל-calculate_isin_concentration_report (analytics)?</b>
</p>

| Risk Concentration | ISIN Concentration |
|---|---|
| ISIN > **50%** של ה**פורטפוליו** של לקוח | ISIN ב-> **70%** של ה**לקוחות** |
| Per-client metric | System-wide metric |
| לפי שווי שוק | לפי count |
| WARNING violation | Analytics insight |

<p dir="rtl">
שני concepts שונים שלפעמים מבלבלים. אם תזכור — תרשים על-ידיהם.
</p>

---

## 14. Repositories — שכבת הגישה ל-DB

### `BaseRepository`

```python
class BaseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db
```

<p dir="rtl">
מינימליסטי. רק מחזיק session.
</p>

### `TransactionRepository`

```python
def list_for_clients_ordered(self, client_ids: Iterable[str]) -> list[Transaction]:
    client_id_list = list(client_ids)
    if not client_id_list:
        return []
    statement = (
        select(Transaction)
        .where(Transaction.client_id.in_(client_id_list))
        .order_by(Transaction.timestamp.asc(), Transaction.id.asc())
    )
    return list(self.db.scalars(statement).all())


def find_existing_transaction_ids(self, transaction_ids: Iterable[str]) -> set[str]:
    ids = list(transaction_ids)
    if not ids:
        return set()
    statement = select(Transaction.transaction_id).where(Transaction.transaction_id.in_(ids))
    return set(self.db.scalars(statement).all())


def add_records(self, records: Iterable[TransactionIngested]) -> None:
    transactions = [Transaction(**record.model_dump()) for record in records]
    self.db.add_all(transactions)
    self.db.flush()
```

### החלטות

<p dir="rtl">
<code>if not client_id_list: return []</code> — early return. בלי זה <code>IN ()</code> ב-SQL = invalid syntax בחלק מה-DBs.
</p>

<p dir="rtl">
<code>scalars().all()</code> — SQLAlchemy 2.0 idiom. מחזיר Mapped objects (לא Rows).
</p>

<p dir="rtl">
<code>flush()</code> בלא commit — נכתב למעלה.
</p>

<p dir="rtl">
<code>record.model_dump()</code> — Pydantic v2 (לשעבר <code>.dict()</code>).
</p>

### `PositionRepository`

```python
def update_clients_positions(self, client_ids, positions: list[PositionSchema]) -> None:
    client_id_list = list(client_ids)
    if not client_id_list:
        return

    self.db.execute(delete(Position).where(Position.client_id.in_(client_id_list)))

    position_rows = [
        Position(
            client_id=position.client_id,
            isin=position.isin,
            quantity=position.quantity,
            average_price=position.average_cost,
            market_price=position.market_price,
            realized_pnl=position.realized_pnl,
            unrealized_pnl=position.unrealized_pnl,
        )
        for position in positions
        if position.quantity > 0
    ]

    if position_rows:
        self.db.add_all(position_rows)

    self.db.flush()
```

### דפוס: DELETE + INSERT

<p dir="rtl">
מוחק את כל positions של ה-impacted clients. מכניס חדשות.
</p>

<p dir="rtl">
<b>למה לא UPSERT?</b>
</p>

- DELETE + INSERT פשוט יותר
- אם פוזיציה ירדה ל-0 → UPSERT לא היה מסיר אותה (היה צריך DELETE נפרד)
- DELETE + INSERT עקבי תמיד
- ה-cost נמוך כי impacted_clients מוגבל

### `if position.quantity > 0`

<p dir="rtl">
positions עם 0 לא מאוחסנות. שומר על הטבלה רזה.
</p>

### `ClientRepository`

```python
def list_client_ids(self) -> list[str]:
    statement = select(Transaction.client_id).distinct().order_by(Transaction.client_id)
    return list(self.db.scalars(statement).all())
```

<p dir="rtl">
קורא מ-<b>transactions</b> (לא positions!) — Heritage מתיקון ב-AI_USAGE.md.
</p>

### `ViolationRepository`

```python
def list_violations(self, client_id: Optional[str] = None) -> list[Violation]:
    statement = select(Violation)
    if client_id is not None:
        statement = statement.where(Violation.client_id == client_id)
    statement = statement.order_by(Violation.created_at.desc(), Violation.id.desc())
    return list(self.db.scalars(statement).all())


def update_clients_violations(self, client_ids, drafts) -> None:
    client_id_list = list(client_ids)
    if not client_id_list:
        return

    self.db.execute(delete(Violation).where(Violation.client_id.in_(client_id_list)))
    rows = [
        Violation(
            client_id=draft.client_id,
            transaction_id=draft.transaction_id,
            violation_type=draft.violation_type,
            severity=draft.severity,
            message=draft.message,
        )
        for draft in drafts
    ]
    if rows:
        self.db.add_all(rows)
    self.db.flush()
```

<p dir="rtl">
אותו pattern של DELETE + INSERT. Order by created_at DESC, id DESC — חדשות ראשונות.
</p>

### `AnalyticsRepository`

```python
def list_transactions_ordered(self) -> list[Transaction]:
    statement = select(Transaction).order_by(
        Transaction.timestamp.asc(),
        Transaction.id.asc(),
        Transaction.transaction_id.asc(),
    )
    return list(self.db.scalars(statement).all())


def list_current_positions(self) -> list[Position]:
    statement = (
        select(Position)
        .where(Position.quantity > 0)
        .order_by(Position.isin.asc(), Position.client_id.asc())
    )
    return list(self.db.scalars(statement).all())
```

<p dir="rtl">
שולף הכל. אין pagination. על קובץ ענק זה ייפול. ה-mitigation עתידי: chunking, streaming.
</p>

### שאלה צפויה

<p dir="rtl">
<b>Q: מה אם יש מיליון transactions ב-DB וצריך לחשב analytics?</b>
</p>

<p dir="rtl">
כל ה-/analytics נכשל. הייתי מטמיע cache (Redis) — מחושב ב-background אחרי כל upload. או pre-compute וקריאה מהירה. או הגבלת window זמן (<code>?from=...&amp;to=...</code>).
</p>

---

## 15. Services — שכבת הלוגיקה

### Pattern: Protocol Injection

<p dir="rtl">
ב-analytics_service.py ו-violations_service.py יש Protocols:
</p>

```python
class AnalyticsRepositoryProtocol(Protocol):
    def list_transactions_ordered(self) -> list[TransactionView]: ...
    def list_current_positions(self) -> list[PositionView]: ...
```

### למה

<p dir="rtl">
ה-service לא קשור ל-AnalyticsRepository הספציפי. אפשר ל-mock אותו בטסטים בקלות. structural typing — כל class עם המתודות האלה מתאים.
</p>

<p dir="rtl">
<b>שים לב:</b> לא נאכף ב-Python runtime ללא <code>@runtime_checkable</code>. זה יותר documentation אבל גם type-checker hint.
</p>

### `transactions_service.upload_transactions_by_file`

<p dir="rtl">
ראינו במעמיק בסעיף 7.
</p>

### `positions_service.list_positions_by_client`

```python
def list_positions_by_client(client_id: str, repository: PositionRepository) -> ClientPositionsResponse:
    positions: list[Position] = repository.list_client_positions(client_id)
    return ClientPositionsResponse(
        client_id=client_id,
        positions=positions,
        total_realized_pnl=sum((p.realized_pnl for p in positions), Decimal("0")),
        total_unrealized_pnl=sum((p.unrealized_pnl for p in positions), Decimal("0")),
    )
```

<p dir="rtl">
<code>sum(..., Decimal("0"))</code> — חובה לתת initial. בלי זה sum מתחיל ב-int 0 וזה לא תקין עם Decimal.
</p>

### `violations_service.list_violations`

```python
def list_violations(repository, client_id=None) -> list[ViolationResponse]:
    return [
        ViolationResponse.model_validate(v)
        for v in repository.list_violations(client_id=client_id)
    ]
```

<p dir="rtl">
<code>model_validate</code> עם <code>from_attributes=True</code> — ORM → Pydantic.
</p>

### `clients_service.list_clients`

```python
def list_clients(repository: ClientRepository) -> list[ClientResponse]:
    return [ClientResponse(client_id=cid) for cid in repository.list_client_ids()]
```

### `analytics_service.get_analytics`

```python
def get_analytics(repository) -> AnalyticsResponse:
    transactions = repository.list_transactions_ordered()
    positions = repository.list_current_positions()
    return calculate_analytics(transactions, positions)
```

<p dir="rtl">
כל הלוגיקה ב-calculate_analytics.
</p>

---

## 16. Utils — Decimal, Files, Exceptions, Config

### `utils/decimal_utils.py`

```python
def percentage(part: Decimal, whole: Decimal) -> Decimal:
    if whole == ZERO:
        return ZERO
    return (part / whole * PERCENT).quantize(CENT)
```

<p dir="rtl">
0.5 → 50.00. CENT = Decimal("0.01") → 2 ספרות. Guard נגד ZeroDivisionError.
</p>

### `utils/exceptions.py` — Custom hierarchy

```python
class AppError(Exception):
    status_code = 500
    detail = "Unexpected application error."

class PersistenceError(AppError):
    detail = "Failed to persist changes."

class ValidationAppError(AppError):
    status_code = 400
    detail = "Invalid request."

class UnsupportedUploadFileError(ValidationAppError): ...
class EmptyUploadFileError(ValidationAppError): ...
class UploadParseError(ValidationAppError): ...
class InsufficientQuantityError(ValidationAppError): ...

class DuplicateTransactionError(AppError):
    status_code = 409
```

### למה class-based

<p dir="rtl">
ה-handler (exception_handlers.py) תופס AppError כמסגרת אחת. כל subclass מגדיר status_code ו-detail ברירת מחדל. שורש אחד = JSON אחיד.
</p>

### `utils/exception_handlers.py`

```python
def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)


async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
```

<p dir="rtl">
כל AppError → JSON אחיד.
</p>

### `utils/config.py` — Pydantic Settings

```python
class Settings(BaseSettings):
    app_name: str = Field(validation_alias="APP_NAME")
    debug: bool = Field(validation_alias="APP_DEBUG")
    auto_init_db: bool = Field(validation_alias="AUTO_INIT_DB")
    log_level: str = Field(validation_alias="LOG_LEVEL")
    database_url: str = Field(validation_alias="DATABASE_URL")
    cors_origins: list[str] = Field(validation_alias="CORS_ORIGINS")

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

<p dir="rtl">
<code>lru_cache</code> — singleton effective (Pydantic Settings קוראת מ-env פעם אחת).
</p>

<p dir="rtl">
<code>validation_alias="APP_NAME"</code> — קבועי env בUpper.
</p>

<p dir="rtl">
<code>extra="ignore"</code> — לא לקרוס על שדות נוספים ב-.env.
</p>

<p dir="rtl">
<code>cors_origins: list[str]</code> — pydantic מפענח JSON automatic. ה-env value הוא <code>["http://localhost:5173"]</code>.
</p>

### `utils/sorters.py`

```python
def sort_by_timestamp(t): return t.timestamp
def sort_by_timestamp_and_id(t): return (t.timestamp, getattr(t, "id", 0))
def sort_by_timestamp_id_and_transaction_id(t): return (t.timestamp, getattr(t, "id", 0), t.transaction_id)
```

<p dir="rtl">
<code>getattr(t, "id", 0)</code> — Pydantic models אין להם id. ORM יש. fallback ל-0.
</p>

### `utils/dataframe.py`

```python
def compact_key(value: object) -> str:
    return "".join(char for char in str(value).strip().lower() if char.isalnum())


def normalize_string_cell(value: object) -> str | None:
    if pd.isna(value):
        return None
    normalized = str(value).strip()
    return normalized or None


def is_blank_cell(value: object) -> bool:
    return (
        value is None
        or pd.isna(value)
        or (isinstance(value, str) and not value.strip())
    )


def parse_decimal_cell(value: object) -> Decimal | None:
    if is_blank_cell(value) or pd.isna(value):
        return None
    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None
    return parsed if parsed.is_finite() else None
```

<p dir="rtl">
<code>parse_decimal_cell</code> — handle gracefully בלי לזרוק.
</p>

<p dir="rtl">
<code>.is_finite()</code> — שולל inf ו-NaN.
</p>

---

## 17. Tests — מה ולמה

### `tests/conftest.py`

```python
import os
os.environ.setdefault("APP_NAME", "Lumina Finance Platform Test")
os.environ.setdefault("APP_DEBUG", "false")
os.environ.setdefault("AUTO_INIT_DB", "false")
os.environ.setdefault("LOG_LEVEL", "INFO")
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("CORS_ORIGINS", '["http://localhost:5173"]')

from backend.tests.helpers.api import api_client
```

### החלטה: env vars לפני imports

<p dir="rtl">
Settings() נטענת ברגע ה-import של config.py. חייב להגדיר env לפני שהapp עולה. <code>setdefault</code> — אם ה-developer ירוץ עם משלו, לא לדרוס.
</p>

### `tests/helpers/api.py`

```python
@pytest.fixture
def api_client() -> Generator[tuple[TestClient, SessionFactory], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        session = testing_session_local()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app), testing_session_local
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
```

### `StaticPool` — קריטי!

<p dir="rtl">
<code>sqlite://</code> הוא in-memory. <b>כל connection חדש = DB חדש ריק.</b> ה-test schema נוצר על הראשון, השאלות עם השני ייכשלו. StaticPool מחזיק connection אחד וחולק לכולם. האפליקציה וה-test רואים אותו memory state.
</p>

### `dependency_overrides`

<p dir="rtl">
מחליף את get_db ב-test session. ב-finally מנקה — לא מזיק ל-test הבא.
</p>

### `Base.metadata.drop_all` — cleanup

<p dir="rtl">
חשוב לטסטים בודדים (לא צוברים state).
</p>

### `tests/test_logic.py` — Unit tests

#### Test #1: FIFO correctness

```python
def test_fifo_calculates_realized_and_unrealized_pnl():
    positions = calculate_fifo_positions([
        tx("T1", "buy", "10", "100", row_id=1),
        tx("T2", "buy", "10", "110", minute=10, row_id=2),
        tx("T3", "sell", "15", "120", minute=20, row_id=3),
    ])
    assert positions[0].model_dump() == {
        "client_id": "C001",
        "isin": "US1234567890",
        "quantity": Decimal("5"),
        "average_cost": Decimal("110"),
        "market_price": Decimal("120"),
        "realized_pnl": Decimal("250"),
        "unrealized_pnl": Decimal("50"),
    }
```

<p dir="rtl">
זו הדוגמה הקלאסית שעברנו עליה — תזכור את המספרים בעל-פה.
</p>

#### Test #2: Sell before buy

```python
def test_sell_before_buy_rule_flags_uncovered_sell():
    context = ClientContext(client_id="C001", transactions=[
        tx("T1", "sell", "5"),     # uncovered
        tx("T2", "buy", "2", minute=10),
        tx("T3", "sell", "3", minute=20),  # 2 - 3 = -1, uncovered
    ])
    drafts = detect_sell_before_buy(context)
    assert [d.transaction_id for d in drafts] == ["T1", "T3"]
```

<p dir="rtl">
שתי השגיאות נדגלות, לא רק הראשונה.
</p>

#### Test #3: Validation

```python
def test_upload_position_validation_blocks_invalid_values():
    with pytest.raises(ValidationAppError, match="Negative value"):
        validate_transactions_can_build_positions([tx("T1", "buy", "10", "-1")])
```

<p dir="rtl">
<code>match="Negative value"</code> — pytest מוודא את ההודעה.
</p>

#### Test #4: Rules isolation

```python
def test_persisted_rules_exclude_blocking_rules():
    assert set(PERSISTED_RULES).isdisjoint(BLOCKING_RULES)
    assert {r.__name__ for r in PERSISTED_RULES} == {"detect_day_trading", "detect_risk_concentration"}
```

<p dir="rtl">
Guard test. מוודא שאם מישהו ירפקטר את ה-tuples, התקלה מתפוצצת.
</p>

#### Test #5: Invalid rows

```python
def test_upload_validation_rejects_invalid_rows():
    dataframe = pd.DataFrame([{
        "ClientId": "C001", "TransactionId": "T1001", "ISIN": "US1234567890",
        "Action": "Hold", "Quantity": 0, "Price": -1, "Timestamp": "not-a-date",
    }])
    errors = validate_transaction_dataframe(normalize_transaction_dataframe(dataframe))
    fields = {e.field for e in errors}
    assert {"action", "quantity", "price", "timestamp"}.issubset(fields)
```

<p dir="rtl">
ארבעה errors בפעם אחת. מוודא שהvalidator אוסף את כולן.
</p>

### `tests/test_api.py` — Integration tests

#### Test: 409 on duplicate

```python
def test_upload_transactions_endpoint_returns_409_on_duplicate_transaction_id(api_client):
    client, _ = api_client
    response = upload_csv(client, duplicate_transaction_upload_csv())
    assert response.status_code == 409
    assert response.json() == {"detail": "One or more transactions have duplicate transaction IDs."}
```

#### Test: 400 on missing columns

```python
def test_upload_transactions_endpoint_returns_400_on_invalid_csv(api_client):
    response = upload_csv(client, "not_a_transaction_column\nvalue")
    assert response.status_code == 400
    assert "Missing required transaction columns" in response.json()["detail"]
```

#### Test: Analytics structure

```python
def test_analytics_endpoint_returns_200_with_analytics_from_database_dependency(api_client):
    client, session_factory = api_client
    seed(session_factory, transaction("T001", action="buy", quantity=Decimal("10"), minutes=0), ...)
    response = client.get("/analytics")
    payload = response.json()
    assert payload["top_traded_isins"] == [{"isin": "ISIN001", "transaction_count": 3}]
```

### שאלות צפויות

<p dir="rtl">
<b>Q: למה אין test ל-day_trading?</b>
</p>

<p dir="rtl">
שווה לציין כ-bug — coverage gap. הייתי מוסיף test שיש 4+ pairs ב-24h ובוחן שיש flag, ועוד test שיש 3 pairs ואין flag (edge case).
</p>

<p dir="rtl">
<b>Q: איך תבדוק FIFO על property?</b>
</p>

<p dir="rtl">
Hypothesis library. ייצר random sequences של buys/sells, ושה-<code>realized + unrealized == sum(sells*sell_price) + market_value(remaining) - sum(buys*buy_price)</code> תמיד.
</p>

---

## 18. Constants — סף ערכים מוסברים

```python
# utils/constants.py

# Decimal Defaults
ZERO = Decimal("0")
CENT = Decimal("0.01")
PERCENT = Decimal("100")
MONEY_QUANTUM = Decimal("0.000001")

# Analytics Thresholds
SECONDS_PER_DAY = Decimal("86400")
ANALYTICS_CONCENTRATION_THRESHOLD = Decimal("70.00")  # >70% clients
TOP_TRADED_LIMIT = 3

# Violations Thresholds
DAY_TRADING_PAIR_THRESHOLD = 3
DAY_TRADING_WINDOW = timedelta(hours=24)
RISK_CONCENTRATION_THRESHOLD = Decimal("0.5")  # 50%
```

### דע אותם בעל-פה

| Constant | Value | Meaning |
|---|---|---|
| `MONEY_QUANTUM` | `0.000001` | 6 decimal places (matches DB `Numeric(18,6)`) |
| `ANALYTICS_CONCENTRATION_THRESHOLD` | `70.00` (%) | ISIN > 70% of clients → flag |
| `RISK_CONCENTRATION_THRESHOLD` | `0.5` (ratio) | ISIN > 50% of portfolio → violation |
| `TOP_TRADED_LIMIT` | `3` | Top 3 ISINs by trade count |
| `DAY_TRADING_PAIR_THRESHOLD` | `3` | > 3 pairs in window → flag |
| `DAY_TRADING_WINDOW` | `24h` | Sliding window |

### אי-עקביות שכדאי לציין

<p dir="rtl">
<code>ANALYTICS_CONCENTRATION_THRESHOLD</code> הוא <b>percentage</b> (70.00). <code>RISK_CONCENTRATION_THRESHOLD</code> הוא <b>ratio</b> (0.5). זה inconsistent. הייתי מאחד — או שניהם percentages, או שניהם ratios.
</p>

---

## 19. AI_USAGE.md — איך לדבר עליו

<p dir="rtl">
המסמך הזה הוא חלק חשוב מהציון. תהיה מוכן להגן על כל שורה.
</p>

### Tools — מה ולמה

- **Codex** — לסקלטון ראשוני, scaffolding, plumbing code
- **Claude Code** — reviewer שני ללוגיקה פיננסית, edge cases, performance

### דוגמאות פרומפטים שכדאי לזכור

- "Build a FastAPI + SQLAlchemy backend with routes, services, repositories, and tests..."
- "Add FIFO position math with realized and unrealized P&L."
- "Review the FIFO implementation and identify precision or performance issues."

### Decisions שכדאי להבליט

#### 1. Recompute → Persist

<p dir="rtl">
<b>הבעיה:</b> Codex ייצר קוד שחישב מחדש את כל ה-FIFO על כל read.
</p>

<p dir="rtl">
<b>התיקון:</b> עברתי לחישוב in upload pipeline, persisting ה-results.
</p>

<p dir="rtl">
<b>השפעה:</b> Reads הם O(1) במקום O(n).
</p>

#### 2. list.pop(0) → deque

<p dir="rtl">
<b>הבעיה:</b> O(n²) על FIFO גדול.
</p>

<p dir="rtl">
<b>התיקון:</b> <code>collections.deque</code> עם <code>popleft()</code> O(1).
</p>

#### 3. 24h boundary

<p dir="rtl">
<b>הבעיה:</b> הראשון השתמש ב-<code>&lt;</code> שכלל trades בדיוק 24h ישנים.
</p>

<p dir="rtl">
<b>התיקון:</b> <code>&lt;=</code> בלולאת ה-pop → טריידים בדיוק 24h ישנים מוצאים מהחלון.
</p>

#### 4. GET /clients

<p dir="rtl">
<b>הבעיה:</b> Heritage מקריאה מ-positions. אם לקוח מכר הכל, נעלם.
</p>

<p dir="rtl">
<b>התיקון:</b> Read from transactions directly.
</p>

#### 5. Circular imports

<p dir="rtl">
<b>הבעיה:</b> schemas הסתבכו ב-circular dependencies.
</p>

<p dir="rtl">
<b>התיקון:</b> Protocols ב-shared.py נקי (בלי תלויות פנימה).
</p>

#### 6. P&L precision

<p dir="rtl">
<b>הבעיה:</b> <code>(market - average_cost) * qty</code> עם rounding drift.
</p>

<p dir="rtl">
<b>התיקון:</b> <code>market * qty - cost_basis</code> — בלי חילוק עד הסוף.
</p>

### שאלה הכי קשה

<p dir="rtl">
<b>Q: מה הכי קשה בלעבוד עם AI?</b>
</p>

<p dir="rtl">
תשובה מומלצת: האתגר הוא <b>לא לקבל בלי לבדוק</b>. AI יכול לכתוב קוד שעובד אבל לא מבין למה הוא נכון — או גרוע יותר, קוד שנראה תקין אבל יש בו בעיית-קצה. הדוגמה המובהקת אצלי הייתה boundary של 24h. הוא עבר את הטסטים הראשונים, אבל היה buggy. הלמידה: אני כותב את ה-test-cases של הקצה <b>בעצמי</b>, לפני שאני מאמין ל-AI. ה-AI מאיץ אבל לא מחליף שיקול דעת.
</p>

---

## 20. שאלות צפויות + תשובות מומלצות

### ארכיטקטורה

<p dir="rtl">
<b>Q: למה layered architecture?</b>
</p>

<p dir="rtl">
המטלה דורשת הפרדה בין API, business logic ו-data. layered מבטיח ש-routes לא יודעים על SQL, services לא יודעים על HTTP. זה גם מקל על בדיקות — אני יכול לבדוק business logic ב-unit test בלי לעלות את ה-app.
</p>

<p dir="rtl">
<b>Q: למה לא Hexagonal/Clean Architecture?</b>
</p>

<p dir="rtl">
ל-3-5 שעות זה היה overkill. ה-layers שלי כבר נותנים את עיקר התועלת. אם הקוד היה גדל ל-50 endpoints וכמה DB sources, היה שווה לעבור.
</p>

<p dir="rtl">
<b>Q: למה אין service interfaces (abstract base classes)?</b>
</p>

<p dir="rtl">
Protocols נותנים את כל היתרון של ABCs בלי boilerplate ירושה. structural typing מתאים יותר ל-Python.
</p>

### Database

<p dir="rtl">
<b>Q: למה SQLite?</b>
</p>

<p dir="rtl">
המטלה ביקשה SQLite מינימום. הקוד agnostic — DATABASE_URL ב-env. החלפה ל-Postgres = שינוי env var. השארתי pool_pre_ping=True במצב non-SQLite להתאוששות מ-connections מתים.
</p>

<p dir="rtl">
<b>Q: למה ORM ולא raw SQL?</b>
</p>

<p dir="rtl">
SQLAlchemy 2.0 + typed Mapped נותן type safety, אינטליגנציה ב-IDE, ו-protection מ-SQL injection. למטרה הזו זה הסטנדרט.
</p>

<p dir="rtl">
<b>Q: למה DELETE+INSERT ב-positions, לא UPSERT?</b>
</p>

<p dir="rtl">
פשוט יותר. ה-FIFO החזיר את ה-state הסופי. UPSERT היה דורש לדעת אילו positions ירדו ל-0 ולמחוק אותן בנפרד. ב-impacted_clients המוגבל, ה-cost של DELETE+INSERT נמוך.
</p>

<p dir="rtl">
<b>Q: מה אם 2 uploads רצים במקביל?</b>
</p>

<p dir="rtl">
אין locking. דרישה: בפרודקשן — <code>SELECT ... FOR UPDATE</code> על positions של ה-clients, או queue per-client_id.
</p>

### Business Logic

<p dir="rtl">
<b>Q: הסבר את חישוב realized P&L.</b>
</p>

<p dir="rtl">
ב-FIFO, sell צורך מ-lot הכי ישן. ל-consumed יחידות, ה-realized = <code>consumed * (sell_price - lot.unit_cost)</code>. אם sell חורג מ-lot אחד, ממשיכים ל-lot הבא. הסכום הכולל הוא realized P&L.
</p>

<p dir="rtl">
<b>Q: הסבר את unrealized.</b>
</p>

<p dir="rtl">
Market value של היחידות הנותרות פחות cost basis. אני מחשב <code>market * qty - cost_basis</code> ולא <code>(market - avg) * qty</code> כי החישוב הראשון לא עובר חילוק, שומר precision.
</p>

<p dir="rtl">
<b>Q: למה average_cost שונה מ-cost_basis / quantity?</b>
</p>

<p dir="rtl">
הוא לא — זה בדיוק כך. הסיבה שיש לי running totals זה אופטימיזציה — לא חישוב חוזר בכל read.
</p>

<p dir="rtl">
<b>Q: מה אם sell יותר מ-buy?</b>
</p>

<p dir="rtl">
ה-validate_transactions_can_build_positions יתפוס לפני ה-FIFO. אם איכשהו הגיע, ה-InsufficientQuantityError ב-FIFO תופס כ-safety net.
</p>

### Validation

<p dir="rtl">
<b>Q: למה לא Pydantic על DataFrame?</b>
</p>

<p dir="rtl">
Pydantic נכשל ב-error הראשון של כל instance. אני רוצה לאסוף את כל השגיאות של כל השורות לחזרה אחת — UX.
</p>

<p dir="rtl">
<b>Q: למה duplicate detection נפרד מ-DB constraint?</b>
</p>

<p dir="rtl">
ה-unique constraint יזרוק IntegrityError, אבל אז ה-transaction נכשל ב-flush — קשה לתפוס bookkeeping. בדיקה לפני ה-INSERT נותנת hint ברור למשתמש.
</p>

### Violations

<p dir="rtl">
<b>Q: מה ההפרדה blocking/persisted?</b>
</p>

<p dir="rtl">
Blocking = ERROR — אסור לעבד. Persisted = WARNING — שמורות אבל לא חוסמות. הראשון רץ pre-FIFO, השני post.
</p>

<p dir="rtl">
<b>Q: מה ההבדל בין risk_concentration ל-analytics concentration?</b>
</p>

<p dir="rtl">
Risk = > 50% של פורטפוליו של לקוח (per-client, by value). Analytics = > 70% מהלקוחות (system-wide, by count).
</p>

### Performance

<p dir="rtl">
<b>Q: מה ה-bottleneck?</b>
</p>

<p dir="rtl">
Upload עם קובץ גדול. הכל בזיכרון — pandas DataFrame ב-RAM, ואז ולידציה. בfile של 1GB יקרוס. הייתי עובר ל-chunked reading.
</p>

<p dir="rtl">
<b>Q: O(?) של ה-FIFO?</b>
</p>

<p dir="rtl">
O(n log n) — בעיקר המיון. ה-FIFO עצמו O(n) amortized. כל lot נכנס פעם אחת ויוצא פעם אחת.
</p>

### Edge Cases

<p dir="rtl">
<b>Q: מה אם quantity = 0?</b>
</p>

<p dir="rtl">
ה-validator חוסם (חייב <code>&gt; 0</code>). אם איכשהו עבר, ה-DB CheckConstraint יזרוק. defense-in-depth.
</p>

<p dir="rtl">
<b>Q: מה אם timestamp בעתיד?</b>
</p>

<p dir="rtl">
אין בדיקה. שווה להוסיף — <code>if t.timestamp > now() + tolerance: warning</code>.
</p>

<p dir="rtl">
<b>Q: מה אם action הוא 'BUY' (uppercase)?</b>
</p>

<p dir="rtl">
ה-normalize ממיר ל-lowercase. ה-VALID_ACTIONS הם <code>{'buy', 'sell'}</code> lowercase.
</p>

### AI Usage

<p dir="rtl">
<b>Q: כמה אחוז מהקוד נכתב על-ידי AI?</b>
</p>

<p dir="rtl">
אומדן: 40-50% scaffolding. אבל כל קוד עבר עליי, ופחות מ-20% נשאר בלי שיניתי. ה-key insight הוא ש-AI בא לסיוע, לא להחלפה.
</p>

<p dir="rtl">
<b>Q: איך אתה יודע שה-AI לא עשה לך bug?</b>
</p>

<p dir="rtl">
Tests + manual review. ה-bug של 24h boundary הוא הדוגמה הקלאסית — Test על "within 24h" עבר, אבל edge case (בדיוק 24h) לא נבדק. הוספתי את ה-test לאחר ה-fix.
</p>

---

## 21. נקודות חולשה — תהיה כן

<p dir="rtl">
תשובה כנה ל-"מה היית משפר?" — סופר חשובה.
</p>

### Missing infrastructure

- אין Alembic — `create_all` עובד רק בפעם הראשונה
- אין auth — כל endpoint פתוח לעולם
- אין rate limiting — DoS easy
- אין structured logging — אין correlation IDs, אין request tracing
- אין metrics / health endpoint — `/healthz` היה pico-cost
- אין error tracking — Sentry או דומה

### Scalability

- אין pagination — `/violations`, `/analytics` יחזירו הכל. מיליון rows = OOM
- All in-memory — Upload של 1GB יקרוס
- אין caching — Analytics מחושבות מאפס בכל קריאה. Redis עם invalidation היה עוזר
- אין connection pooling tuned — pool_size default

### Concurrency

- אין locking — שני uploads concurrent יכולים לקלקל
- אין idempotency — upload פעמיים של אותו קובץ יזרוק 409, אבל אם זה chunked — בעיה

### Code Quality

- `detect_invalid_values` כפול — גם dataframe validator וגם ה-rule. defense in depth אבל redundant
- Inconsistent thresholds — `ANALYTICS_CONCENTRATION_THRESHOLD = 70.00` (percentage), `RISK_CONCENTRATION_THRESHOLD = 0.5` (ratio)
- Docstrings מתורגמים מאנגלית — חלקם מסורבלים. הייתי מצמצם
- Comments מסבירים WHAT — `# Iterate over each transaction`. צריך WHY

### Functional gaps

- אין short positions — `_portfolio_value` מתעלם מ-`quantity <= 0`
- Market price = last trade — לא market data אמיתי
- אין timezone handling — `DateTime(timezone=False)`
- אין partial commits — אם upload נכשל באמצע, הכל נדחה

### Testing

- אין test ל-day_trading — coverage gap
- אין property-based tests — Hypothesis היה מצוין ל-FIFO
- אין load tests — אין benchmark על 100k rows

---

## 22. Cheat Sheet — דברים בעל-פה

### Numbers to memorize

| Item | Value |
|---|---|
| Day trading threshold | > 3 pairs in 24h |
| Risk concentration | > 50% of portfolio |
| Analytics concentration | > 70% of clients |
| Top traded limit | 3 |
| MONEY_QUANTUM | 0.000001 (6 decimal places) |

### Status codes

| Endpoint | Success | Error cases |
|---|---|---|
| POST /upload-transactions | 201 | 400 (validation), 409 (duplicate), 500 (persistence) |
| GET /clients | 200 | — |
| GET /clients/{id}/positions | 200 | — |
| GET /violations | 200 | — |
| GET /analytics | 200 | — |

### File flow

```
UploadFile
  → read_table_from_file        (CSV/XLSX → DataFrame)
  → normalize_transaction_df    (rename + types)
  → validate_transaction_df     (collect ALL errors)
  → transaction_records_from_df (DataFrame → Pydantic)
  → TransactionIngestionResult
```

### Upload flow

```
parse → validate → check duplicates → INSERT transactions
  → SELECT impacted clients → blocking rules
  → FIFO → DELETE+INSERT positions
  → snapshots → persisted rules → DELETE+INSERT violations
  → COMMIT
```

### FIFO state

```
PositionState:
  - open_lots: deque[OpenLot(quantity, unit_cost)]
  - total_quantity (running)
  - total_cost_basis (running)
  - realized_pnl (running)
  - market_price (last seen)

  properties:
    quantity = total_quantity
    average_cost = total_cost_basis / total_quantity (quantized)
    unrealized_pnl = market_price * total_quantity - total_cost_basis
```

### Rules tuples

```
DEFAULT  = (invalid_values, sell_before_buy, day_trading, risk_concentration)
BLOCKING = (invalid_values, sell_before_buy)
PERSISTED = DEFAULT - BLOCKING = (day_trading, risk_concentration)
```

### Exception hierarchy

```
AppError (500)
├── PersistenceError (500)
├── DuplicateTransactionError (409)
└── ValidationAppError (400)
    ├── UnsupportedUploadFileError
    ├── EmptyUploadFileError
    ├── UploadParseError
    └── InsufficientQuantityError
```

### Key files for the interview

| File | Purpose |
|---|---|
| `transactions_service.py` | The upload flow — the heart |
| `fifo_engine.py` | FIFO P&L calculation |
| `violations_service.py` | Rules orchestration |
| `day_trading.py` | Sliding window algorithm |
| `risk_concentration.py` | Per-portfolio concentration |
| `holding_time.py` | Weighted average algorithm |
| `volatility.py` | Replay-based volatility |
| `concentration.py` | System-wide concentration |
| `shared.py` (schemas) | Protocols — the binding glue |
| `positions.py` (schemas) | PositionState — the running calc |
| `constants.py` | All thresholds in one place |

---

## Final preparation routine

<p dir="rtl">
שגרת הכנה אחרונה:
</p>

1. הרץ את כל הטסטים: `pytest backend/tests/` — תוודא שהם עוברים
2. הפעל את ה-app: `uvicorn backend.app.main:app --reload`
3. פתח את `/docs` — עבור על כל endpoint, דע מה הוא מחזיר
4. קרא שוב את AI_USAGE.md — תהיה מוכן להגן על כל שורה
5. תרגל הסבר על דוגמת ה-FIFO — בלי להסתכל
6. תרגל הסבר על ה-upload flow — בלי להסתכל
7. קרא את המסמך הזה מהקצה לקצה בבוקר של הראיון

<p dir="rtl">
בהצלחה!
</p>

</div>
