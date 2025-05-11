name: Hollywood NewsBot

on:
  workflow_dispatch: # Allows manual triggering
  schedule:
    # Runs every hour, on the hour
    - cron: "0 * * * *"
    # You can adjust the schedule:
    # e.g., every 6 hours: "0 */6 * * *"
    # e.g., once a day at midnight UTC: "0 0 * * *"

jobs:
  build-and-post:
    runs-on: ubuntu-latest
    permissions:
      contents: write # Required to commit Hugo posts back to the repo

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          submodules: 'recursive' # To fetch your Hugo theme if it's a submodule
          token: ${{ secrets.GITHUB_TOKEN }} # Use default GITHUB_TOKEN for checkout

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11' # Or your preferred Python version

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Setup Hugo
        uses: peaceiris/actions-hugo@v3
        with:
          hugo-version: 'latest' # or a specific version e.g., '0.125.0'
          # extended: true # Uncomment if your theme requires the Hugo extended version

      - name: Run bot (write post + tweet)
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
          HF_MODEL: ${{ secrets.HF_MODEL }}
          X_CONSUMER_KEY: ${{ secrets.X_CONSUMER_KEY }}
          X_CONSUMER_SECRET: ${{ secrets.X_CONSUMER_SECRET }}
          X_ACCESS_TOKEN: ${{ secrets.X_ACCESS_TOKEN }}
          X_ACCESS_SECRET: ${{ secrets.X_ACCESS_SECRET }}
          FEED_URL: ${{ secrets.FEED_URL }}
          HUGO_CONTENT_DIR: "content/posts" # Make sure this matches your Hugo setup
          PROCESSED_POSTS_FILE: "processed_posts.log"
          MAX_POSTS_PER_RUN: "1" # How many new feed items to process each time the Action runs
        run: python scripts/make_post.py

      - name: Build Hugo site
        run: hugo --minify # The --minify flag is optional

      - name: Deploy to GitHub Pages (or commit changes)
        # This step commits the new Hugo posts and the processed_posts.log back to your repo.
        # If you are deploying to GitHub Pages, you would use a different action here like peaceiris/actions-gh-pages.
        # For now, this just commits the changes.
        run: |
          git config --global user.name 'github-actions[bot]'
          git config --global user.email 'github-actions[bot]@users.noreply.github.com'
          git add content/posts/ # Add new posts
          git add processed_posts.log # Add the log file
          # Check if there are changes to commit
          if ! git diff --staged --quiet; then
            git commit -m "Automated: Add new news post(s) and update processed log by bot"
            git push
          else
            echo "No changes to commit."
          fi
