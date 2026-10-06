-- Google Play review workflow: baseline PostgreSQL 15+ schema.
-- See google_play_database_schema.md for field mappings and design rationale.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE apps (
    app_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source varchar(50) NOT NULL DEFAULT 'google_play',
    package_name varchar(255) NOT NULL,
    display_name text NOT NULL,
    category_name varchar(100),
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT apps_source_package_uq UNIQUE (source, package_name)
);

CREATE TABLE collection_runs (
    collection_run_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source varchar(50) NOT NULL DEFAULT 'google_play',
    collection_method varchar(100) NOT NULL,
    collector_name varchar(100) NOT NULL,
    collector_version varchar(50),
    official_api boolean NOT NULL DEFAULT false,
    started_at timestamptz NOT NULL,
    finished_at timestamptz,
    requested_language varchar(10) NOT NULL,
    requested_country char(2) NOT NULL,
    sort_order varchar(30) NOT NULL,
    reviews_requested_per_app integer NOT NULL,
    target_app_count integer NOT NULL,
    delay_seconds numeric(8,3),
    status varchar(20) NOT NULL DEFAULT 'running',
    error_message text,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT collection_runs_finished_ck
        CHECK (finished_at IS NULL OR finished_at >= started_at),
    CONSTRAINT collection_runs_review_limit_ck
        CHECK (reviews_requested_per_app > 0),
    CONSTRAINT collection_runs_target_count_ck CHECK (target_app_count >= 0),
    CONSTRAINT collection_runs_delay_ck
        CHECK (delay_seconds IS NULL OR delay_seconds >= 0),
    CONSTRAINT collection_runs_status_ck
        CHECK (status IN ('running', 'completed', 'partial', 'failed'))
);

CREATE TABLE collection_targets (
    collection_run_id uuid NOT NULL
        REFERENCES collection_runs(collection_run_id) ON DELETE CASCADE,
    app_id bigint NOT NULL REFERENCES apps(app_id),
    status varchar(30) NOT NULL,
    records_collected integer NOT NULL DEFAULT 0,
    unique_review_ids integer NOT NULL DEFAULT 0,
    continuation_available boolean,
    elapsed_seconds numeric(12,3),
    oldest_review_at timestamptz,
    newest_review_at timestamptz,
    observed_window_days numeric(12,4),
    error_type varchar(100),
    error_message text,
    PRIMARY KEY (collection_run_id, app_id),
    CONSTRAINT collection_targets_status_ck
        CHECK (status IN ('success', 'no_records_returned', 'failed')),
    CONSTRAINT collection_targets_counts_ck
        CHECK (
            records_collected >= 0
            AND unique_review_ids >= 0
            AND unique_review_ids <= records_collected
        ),
    CONSTRAINT collection_targets_elapsed_ck
        CHECK (elapsed_seconds IS NULL OR elapsed_seconds >= 0),
    CONSTRAINT collection_targets_window_order_ck
        CHECK (
            oldest_review_at IS NULL
            OR newest_review_at IS NULL
            OR newest_review_at >= oldest_review_at
        ),
    CONSTRAINT collection_targets_window_days_ck
        CHECK (observed_window_days IS NULL OR observed_window_days >= 0)
);

CREATE TABLE app_snapshots (
    app_snapshot_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    collection_run_id uuid NOT NULL,
    app_id bigint NOT NULL,
    captured_at timestamptz NOT NULL,
    store_title text,
    store_genre varchar(100),
    store_genre_id varchar(100),
    store_score numeric(8,6),
    ratings_count bigint,
    reviews_count bigint,
    installs_label varchar(50),
    minimum_installs bigint,
    real_installs bigint,
    price_amount numeric(12,2),
    is_free boolean,
    currency_code char(3),
    developer_name text,
    released_on date,
    store_updated_at timestamptz,
    version_name text,
    content_rating varchar(100),
    ad_supported boolean,
    contains_ads boolean,
    offers_iap boolean,
    CONSTRAINT app_snapshots_run_app_uq UNIQUE (collection_run_id, app_id),
    CONSTRAINT app_snapshots_target_fk
        FOREIGN KEY (collection_run_id, app_id)
        REFERENCES collection_targets(collection_run_id, app_id)
        ON DELETE CASCADE,
    CONSTRAINT app_snapshots_score_ck
        CHECK (store_score IS NULL OR store_score BETWEEN 0 AND 5),
    CONSTRAINT app_snapshots_counts_ck
        CHECK (
            (ratings_count IS NULL OR ratings_count >= 0)
            AND (reviews_count IS NULL OR reviews_count >= 0)
            AND (minimum_installs IS NULL OR minimum_installs >= 0)
            AND (real_installs IS NULL OR real_installs >= 0)
            AND (price_amount IS NULL OR price_amount >= 0)
        ),
    CONSTRAINT app_snapshots_currency_ck
        CHECK (currency_code IS NULL OR currency_code = upper(currency_code))
);

CREATE TABLE reviews (
    review_pk bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    app_id bigint NOT NULL REFERENCES apps(app_id),
    source_review_id text NOT NULL,
    review_text text NOT NULL,
    star_rating smallint NOT NULL,
    review_version text,
    reviewed_at timestamptz NOT NULL,
    first_seen_at timestamptz NOT NULL,
    last_seen_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT reviews_app_source_id_uq UNIQUE (app_id, source_review_id),
    CONSTRAINT reviews_pk_app_uq UNIQUE (review_pk, app_id),
    CONSTRAINT reviews_rating_ck CHECK (star_rating BETWEEN 1 AND 5),
    CONSTRAINT reviews_seen_order_ck CHECK (last_seen_at >= first_seen_at)
);

CREATE TABLE review_observations (
    collection_run_id uuid NOT NULL,
    review_pk bigint NOT NULL,
    app_id bigint NOT NULL,
    observed_at timestamptz NOT NULL,
    helpful_count integer NOT NULL,
    developer_reply_present boolean NOT NULL,
    content_hash char(64),
    PRIMARY KEY (collection_run_id, review_pk),
    CONSTRAINT review_observations_target_fk
        FOREIGN KEY (collection_run_id, app_id)
        REFERENCES collection_targets(collection_run_id, app_id)
        ON DELETE CASCADE,
    CONSTRAINT review_observations_review_fk
        FOREIGN KEY (review_pk, app_id)
        REFERENCES reviews(review_pk, app_id)
        ON DELETE CASCADE,
    CONSTRAINT review_observations_helpful_ck CHECK (helpful_count >= 0),
    CONSTRAINT review_observations_hash_ck
        CHECK (content_hash IS NULL OR content_hash ~ '^[0-9a-f]{64}$')
);

CREATE TABLE developer_replies (
    developer_reply_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_pk bigint NOT NULL UNIQUE
        REFERENCES reviews(review_pk) ON DELETE CASCADE,
    reply_text text NOT NULL,
    replied_at timestamptz,
    first_seen_at timestamptz NOT NULL,
    last_seen_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT developer_replies_seen_order_ck
        CHECK (last_seen_at >= first_seen_at)
);

CREATE INDEX collection_targets_app_run_idx
    ON collection_targets (app_id, collection_run_id);

CREATE INDEX app_snapshots_app_captured_idx
    ON app_snapshots (app_id, captured_at DESC);

CREATE INDEX reviews_app_reviewed_idx
    ON reviews (app_id, reviewed_at DESC);

CREATE INDEX reviews_star_rating_idx
    ON reviews (star_rating);

CREATE INDEX review_observations_app_observed_idx
    ON review_observations (app_id, observed_at DESC);
