# Reddit Reader

Simple read-only Reddit API client for research purposes.

## Purpose

Personal research tool to:
- Monitor trending topics in tech/AI communities
- Discover discussions and community interests
- Gather inspiration for content creation

**Read-only** - no posting, commenting, or voting. Just reading public data.

## Setup

1. Create a Reddit app at https://www.reddit.com/prefs/apps (type: script)
2. Set environment variables:
   ```bash
   export REDDIT_CLIENT_ID='your_client_id'
   export REDDIT_CLIENT_SECRET='your_client_secret'
   ```

## Usage

```bash
# Hot posts from a subreddit
python reddit_reader.py --subreddit LocalLLaMA --limit 10

# Top posts this week
python reddit_reader.py --subreddit artificial --sort top --time week

# Search across Reddit
python reddit_reader.py --search "AI agents" --limit 20

# Output as JSON
python reddit_reader.py --subreddit programming --json
```

## Requirements

```bash
pip install requests
```

## License

MIT
