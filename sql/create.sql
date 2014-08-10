CREATE TABLE IF NOT EXISTS message (
    sid BIGINT,
    topic INTEGER,
    topic_position INTEGER,
    member INTEGER,
    post_time TIMESTAMP,
    subject TEXT,
    link TEXT,
    content TEXT,
    content_no_html TEXT,
    content_no_quote TEXT,
    content_no_quote_no_html TEXT,
    db_update_time TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    PRIMARY KEY (sid)
);
CREATE INDEX ON message (topic, topic_position);
CREATE INDEX ON message (topic, member);
CREATE INDEX ON message (member, topic);
CREATE INDEX ON message (post_time);

CREATE TABLE IF NOT EXISTS topic (
    sid INTEGER,
    name VARCHAR(255),
    board INTEGER,
    num_pages INTEGER,
    count_read INTEGER,
    db_update_time TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    PRIMARY KEY (sid)
);
CREATE INDEX ON topic (name);
CREATE INDEX ON topic (board);

CREATE TABLE IF NOT EXISTS board (
    sid INTEGER,
    name VARCHAR(255),
    parent INTEGER,
    container VARCHAR(255),
    num_pages INTEGER,
    db_update_time TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    PRIMARY KEY(sid)
);
CREATE INDEX ON board (name);

CREATE TABLE IF NOT EXISTS member (
    sid INTEGER,
    name VARCHAR(255),
    position VARCHAR(255),
    date_registered TIMESTAMP,
    last_active TIMESTAMP,
    email VARCHAR(255),
    website_name TEXT,
    website_link TEXT,
    bitcoin_address VARCHAR(50),
    other_contact_info TEXT,
    signature TEXT,
    db_update_time TIMESTAMP WITH TIME ZONE DEFAULT current_timestamp,
    PRIMARY KEY(sid)
);
CREATE INDEX ON member (name);
CREATE INDEX ON member (bitcoin_address);