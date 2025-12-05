"""
Content generator for social media posts

Pulls data from database and generates post content using templates.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from .post_template import create_template, PostTemplate
from ..database.schema import get_connection


class ContentGenerator:
    """Generate social media content from database updates"""

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize content generator.

        Args:
            db_path: Path to SQLite database. If None, uses default from schema.
        """
        self.db_path = db_path
        self.conn = get_connection(db_path)

    def get_unprocessed_updates(self, limit: Optional[int] = None,
                               since_date: Optional[str] = None,
                               ignore_processed: bool = False) -> List[Dict]:
        """
        Get updates that haven't been processed for social media yet.

        Args:
            limit: Maximum number of updates to return
            since_date: Only return updates from this date onwards (ISO format: YYYY-MM-DD)
            ignore_processed: If True, include already-processed updates (for dev/testing)

        Returns:
            List of update dictionaries with game information joined
        """
        query = """
            SELECT
                u.id,
                u.game_id,
                u.update_type,
                u.title,
                u.content,
                u.url,
                u.date,
                g.name as game_name,
                g.header_image_url,
                g.screenshot_url,
                g.dimension_1,
                g.dimension_2,
                g.dimension_3,
                g.release_date,
                g.price_usd,
                g.genres,
                g.steam_tags
            FROM updates u
            JOIN games g ON u.game_id = g.id
            WHERE g.is_active = 1
        """

        # Only check processed status if not ignoring it
        if not ignore_processed:
            query += " AND u.processed_for_social = 0"

        params = []

        if since_date:
            query += " AND date(u.date) >= date(?)"
            params.append(since_date)

        query += " ORDER BY u.date DESC"

        if limit:
            query += f" LIMIT {limit}"

        cursor = self.conn.cursor()
        cursor.execute(query, params)

        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))

        return results

    def get_update_by_id(self, update_id: int) -> Optional[Dict]:
        """
        Get a specific update with game information.

        Args:
            update_id: Database ID of the update

        Returns:
            Update dictionary or None if not found
        """
        query = """
            SELECT
                u.id,
                u.game_id,
                u.update_type,
                u.title,
                u.content,
                u.url,
                u.date,
                g.name as game_name,
                g.header_image_url,
                g.screenshot_url,
                g.dimension_1,
                g.dimension_2,
                g.dimension_3,
                g.release_date,
                g.price_usd,
                g.genres,
                g.steam_tags
            FROM updates u
            JOIN games g ON u.game_id = g.id
            WHERE u.id = ?
        """

        cursor = self.conn.cursor()
        cursor.execute(query, (update_id,))
        row = cursor.fetchone()

        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None

    def generate_post(self, update_data: Dict) -> PostTemplate:
        """
        Generate a post template from update data.

        Args:
            update_data: Dictionary with update and game information

        Returns:
            PostTemplate instance ready for image generation and posting
        """
        # Parse date
        date = datetime.fromisoformat(update_data['date'].replace(' ', 'T'))

        # Prefer screenshot (high-res) over header image for Instagram
        image_url = update_data.get('screenshot_url') or update_data['header_image_url']

        # Create template using factory
        template = create_template(
            game_name=update_data['game_name'],
            game_image_url=image_url,
            update_title=update_data['title'],
            update_date=date,
            update_type=update_data['update_type'],
            update_content=update_data.get('content'),
            steam_url=update_data.get('url'),
            game_release_date=update_data.get('release_date'),
            game_price_usd=update_data.get('price_usd'),
            game_genres=update_data.get('genres'),
            game_dimension_1=update_data.get('dimension_1'),
            game_dimension_2=update_data.get('dimension_2'),
            game_dimension_3=update_data.get('dimension_3')
        )

        return template

    def queue_for_social(self, update_id: int, platform: str = 'instagram',
                        scheduled_time: Optional[datetime] = None) -> int:
        """
        Add an update to the social media queue.

        Args:
            update_id: Database ID of the update
            platform: Social media platform ('instagram', 'twitter', etc.)
            scheduled_time: When to post (None = immediate/manual)

        Returns:
            Queue entry ID
        """
        # Get update data
        update_data = self.get_update_by_id(update_id)
        if not update_data:
            raise ValueError(f"Update ID {update_id} not found")

        # Generate post
        template = self.generate_post(update_data)
        post_data = template.to_dict()

        # Insert into social media queue
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO social_media_queue
            (update_id, platform, content_text, scheduled_time, status)
            VALUES (?, ?, ?, ?, 'pending')
        """, (
            update_id,
            platform,
            post_data['caption'],
            scheduled_time.isoformat() if scheduled_time else None
        ))

        self.conn.commit()
        queue_id = cursor.lastrowid

        return queue_id

    def bulk_queue_unprocessed(self, platform: str = 'instagram',
                               limit: Optional[int] = None,
                               update_types: Optional[List[str]] = None,
                               since_date: Optional[str] = None) -> List[int]:
        """
        Queue multiple unprocessed updates for social media.

        Args:
            platform: Social media platform
            limit: Maximum number to queue
            update_types: Filter by update types (e.g., ['patch', 'dlc'])
            since_date: Only queue updates from this date onwards (ISO format: YYYY-MM-DD)

        Returns:
            List of queue entry IDs
        """
        updates = self.get_unprocessed_updates(limit=limit, since_date=since_date)

        # Filter by type if specified
        if update_types:
            updates = [u for u in updates if u['update_type'] in update_types]

        queue_ids = []
        for update in updates:
            try:
                queue_id = self.queue_for_social(update['id'], platform=platform)
                queue_ids.append(queue_id)
            except Exception as e:
                print(f"Error queueing update {update['id']}: {e}")

        return queue_ids

    def get_queue_entries(self, status: str = 'pending',
                         platform: Optional[str] = None,
                         limit: Optional[int] = None) -> List[Dict]:
        """
        Get entries from social media queue.

        Args:
            status: Filter by status ('pending', 'posted', 'failed', 'cancelled')
            platform: Filter by platform
            limit: Maximum number to return

        Returns:
            List of queue entry dictionaries
        """
        query = """
            SELECT
                q.id,
                q.update_id,
                q.platform,
                q.content_text,
                q.image_path,
                q.scheduled_time,
                q.status,
                q.post_id,
                q.error_message,
                q.created_at,
                q.posted_at,
                u.title as update_title,
                g.name as game_name
            FROM social_media_queue q
            LEFT JOIN updates u ON q.update_id = u.id
            LEFT JOIN games g ON u.game_id = g.id
            WHERE q.status = ?
        """

        params = [status]

        if platform:
            query += " AND q.platform = ?"
            params.append(platform)

        query += " ORDER BY q.created_at DESC"

        if limit:
            query += f" LIMIT {limit}"

        cursor = self.conn.cursor()
        cursor.execute(query, params)

        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))

        return results

    def update_queue_status(self, queue_id: int, status: str,
                           post_id: Optional[str] = None,
                           error_message: Optional[str] = None,
                           image_path: Optional[str] = None):
        """
        Update status of a queue entry.

        Args:
            queue_id: Queue entry ID
            status: New status ('pending', 'posted', 'failed', 'cancelled')
            post_id: Platform's post ID (if posted successfully)
            error_message: Error message (if failed)
            image_path: Path to generated image file
        """
        cursor = self.conn.cursor()

        updates = ["status = ?"]
        params = [status]

        if post_id:
            updates.append("post_id = ?")
            params.append(post_id)

        if error_message:
            updates.append("error_message = ?")
            params.append(error_message)

        if image_path:
            updates.append("image_path = ?")
            params.append(image_path)

        if status == 'posted':
            updates.append("posted_at = CURRENT_TIMESTAMP")

        params.append(queue_id)

        query = f"""
            UPDATE social_media_queue
            SET {', '.join(updates)}
            WHERE id = ?
        """

        cursor.execute(query, params)
        self.conn.commit()

        # If successfully posted, mark update as processed
        if status == 'posted':
            cursor.execute("""
                UPDATE updates
                SET processed_for_social = 1, date_posted = CURRENT_TIMESTAMP
                WHERE id = (
                    SELECT update_id FROM social_media_queue WHERE id = ?
                )
            """, (queue_id,))
            self.conn.commit()

    def get_recent_posts(self, platform: str = 'instagram',
                        days: int = 7) -> List[Dict]:
        """
        Get recently posted content.

        Args:
            platform: Filter by platform
            days: Number of days to look back

        Returns:
            List of posted queue entries
        """
        query = """
            SELECT
                q.*,
                u.title as update_title,
                g.name as game_name
            FROM social_media_queue q
            LEFT JOIN updates u ON q.update_id = u.id
            LEFT JOIN games g ON u.game_id = g.id
            WHERE q.status = 'posted'
            AND q.platform = ?
            AND q.posted_at >= datetime('now', '-' || ? || ' days')
            ORDER BY q.posted_at DESC
        """

        cursor = self.conn.cursor()
        cursor.execute(query, (platform, days))

        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))

        return results

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.close()