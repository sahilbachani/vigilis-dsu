from db import get_db_connection

def get_or_create_source(platform: str, source_name: str, url: str):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT source_id FROM sources
        WHERE platform = %s AND source_name = %s
        """,
        (platform, source_name)
    )
    result = cur.fetchone()

    if result:
        source_id = result[0]
    else:
        cur.execute(
            """
            INSERT INTO sources (platform, source_name, url)
            VALUES (%s, %s, %s)
            RETURNING source_id
            """,
            (platform, source_name, url)
        )
        source_id = cur.fetchone()[0]
        conn.commit()

    cur.close()
    conn.close()
    return source_id

def save_post(source_id: int, author: str, text_content: str, url: str, timestamp, confidence_score=None, category=None):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO posts (source_id, author, text_content, url, timestamp, confidence_score, category)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING post_id
        """,
        (source_id, author, text_content, url, timestamp, confidence_score, category)
    )
    post_id = cur.fetchone()[0]
    conn.commit()

    cur.close()
    conn.close()
    return post_id


def save_tags(post_id: int, source_id: int, tags: list):
    conn = get_db_connection()
    cur = conn.cursor()

    for tag in tags:
        if tag:  # Only save non-empty tags
            cur.execute(
                """
                INSERT INTO tags (tag_name, source_id)
                VALUES (%s, %s)
                ON CONFLICT (tag_name, source_id) DO NOTHING
                """,
                (tag.lower(), source_id)
            )
            
            # Get the tag_id
            cur.execute(
                """
                SELECT tag_id FROM tags
                WHERE tag_name = %s AND source_id = %s
                """,
                (tag.lower(), source_id)
            )
            tag_id = cur.fetchone()[0]
            
            # Link tag to post
            cur.execute(
                """
                INSERT INTO post_tags (post_id, tag_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (post_id, tag_id)
            )

    conn.commit()
    cur.close()
    conn.close()