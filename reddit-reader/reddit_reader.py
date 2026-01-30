#!/usr/bin/env python3
"""
reddit_reader.py - Simple Reddit API reader for research purposes.
Read-only access to public subreddit data.

Usage:
    python reddit_reader.py --subreddit LocalLLaMA --sort hot --limit 10
    python reddit_reader.py --subreddit artificial --sort top --time week
"""

import argparse
import requests
import json
import os
from datetime import datetime

class RedditReader:
    def __init__(self, client_id=None, client_secret=None, user_agent=None):
        self.client_id = client_id or os.getenv('REDDIT_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('REDDIT_CLIENT_SECRET')
        self.user_agent = user_agent or os.getenv('REDDIT_USER_AGENT', 'reddit-reader:v1.0')
        self.access_token = None
        self.base_url = 'https://oauth.reddit.com'
    
    def authenticate(self):
        """Get OAuth access token for API access."""
        if not self.client_id or not self.client_secret:
            raise ValueError("REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET must be set")
        
        auth = requests.auth.HTTPBasicAuth(self.client_id, self.client_secret)
        data = {'grant_type': 'client_credentials'}
        headers = {'User-Agent': self.user_agent}
        
        response = requests.post(
            'https://www.reddit.com/api/v1/access_token',
            auth=auth,
            data=data,
            headers=headers
        )
        response.raise_for_status()
        self.access_token = response.json()['access_token']
        return self.access_token
    
    def get_posts(self, subreddit, sort='hot', limit=25, time='day'):
        """
        Fetch posts from a subreddit.
        
        Args:
            subreddit: Subreddit name (without r/)
            sort: hot, new, top, rising
            limit: Number of posts (max 100)
            time: For 'top' sort: hour, day, week, month, year, all
        """
        if not self.access_token:
            self.authenticate()
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'User-Agent': self.user_agent
        }
        
        params = {'limit': min(limit, 100)}
        if sort == 'top':
            params['t'] = time
        
        url = f'{self.base_url}/r/{subreddit}/{sort}'
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        return self._parse_posts(response.json())
    
    def _parse_posts(self, data):
        """Extract relevant fields from Reddit API response."""
        posts = []
        for child in data.get('data', {}).get('children', []):
            post = child.get('data', {})
            posts.append({
                'title': post.get('title'),
                'author': post.get('author'),
                'score': post.get('score'),
                'url': post.get('url'),
                'permalink': f"https://reddit.com{post.get('permalink')}",
                'num_comments': post.get('num_comments'),
                'created_utc': datetime.fromtimestamp(post.get('created_utc', 0)).isoformat(),
                'selftext': post.get('selftext', '')[:500],  # Truncate long text
                'subreddit': post.get('subreddit'),
                'is_self': post.get('is_self'),
            })
        return posts
    
    def search(self, query, subreddit=None, sort='relevance', limit=25):
        """
        Search Reddit posts.
        
        Args:
            query: Search query
            subreddit: Optional - limit to specific subreddit
            sort: relevance, hot, top, new, comments
            limit: Number of results
        """
        if not self.access_token:
            self.authenticate()
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'User-Agent': self.user_agent
        }
        
        params = {
            'q': query,
            'sort': sort,
            'limit': min(limit, 100)
        }
        
        if subreddit:
            url = f'{self.base_url}/r/{subreddit}/search'
            params['restrict_sr'] = True
        else:
            url = f'{self.base_url}/search'
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        return self._parse_posts(response.json())


def main():
    parser = argparse.ArgumentParser(description='Read Reddit posts for research')
    parser.add_argument('--subreddit', '-s', default='all', help='Subreddit to read')
    parser.add_argument('--sort', choices=['hot', 'new', 'top', 'rising'], default='hot')
    parser.add_argument('--limit', '-n', type=int, default=10, help='Number of posts')
    parser.add_argument('--time', '-t', default='day', help='Time filter for top (hour/day/week/month/year/all)')
    parser.add_argument('--search', '-q', help='Search query')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    reader = RedditReader()
    
    try:
        if args.search:
            posts = reader.search(args.search, subreddit=args.subreddit if args.subreddit != 'all' else None, limit=args.limit)
        else:
            posts = reader.get_posts(args.subreddit, sort=args.sort, limit=args.limit, time=args.time)
        
        if args.json:
            print(json.dumps(posts, indent=2))
        else:
            for i, post in enumerate(posts, 1):
                print(f"\n{i}. [{post['score']:>5}] {post['title']}")
                print(f"   r/{post['subreddit']} | {post['num_comments']} comments | {post['author']}")
                print(f"   {post['permalink']}")
    
    except ValueError as e:
        print(f"Error: {e}")
        print("\nSet environment variables:")
        print("  export REDDIT_CLIENT_ID='your_client_id'")
        print("  export REDDIT_CLIENT_SECRET='your_client_secret'")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
