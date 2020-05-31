# Reddit Feedback Bot
Reddit bot used for (r/IndieMusicFeedback)[https://www.reddit.com/r/IndieMusicFeedback/] which allows an automatic comments/post ratio for users to be enforced

# Getting started

To use the bot on your subreddit:

- Clone the repository on a computer/server where the bot will run

- The bot requires python > 3.6 and a few pip packages to be installed, you can install them by running `pip install -r requirements.txt` from the root of the repository

- Update the `config/credentials-sample.cfg` file with the proper credentials from you bot account and application authentication and rename the file to `config/credentials.cfg`

- Update the `config/config.cfg` file with values that will fit your use case (needed score to post, minimum comment length...)

- Update in the `feedback_bot.py` the various messages the bot sends to users (about removal reasons and so on) so that the bot output fits you use case (this steps requires a bit a coding knowledge...)

- Run `python3 feedback_bot.py`, the first run will not moderate anything just register the current posts and comments, so it can have a base of moderation starting on the second run

- After the first run you can check the newly created `users.json` and `posts.json` files in the root of the repo which will be the bot's databases (which also means these files will grow over time and the bot will slow down if your subreddit has a very high activity, if that's a case you should think about creating a script to cleanup these files or actually use a real db for better scaling, don't hesitate to submit a Pull Request !)

- To get the bot to run regularly the easiest way is to setup a cron job (on unix systems) by typing `crontab -e` (if that doesn't work, you probably need to setup crontab on you machine) and adding a new job: `*/3 * * * * cd [ABSOLUTE_PATH_TO_THE_REPO] && python3 feedback_bot.py`
