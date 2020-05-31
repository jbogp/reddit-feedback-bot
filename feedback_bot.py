import json
import praw
import re
import fcntl
import config
import time
import sys
import logging
from pathlib import Path
from bot_credentials import BotCredentials
from bot_config import BotConfig
from praw.models import Message
from json.decoder import JSONDecodeError

def create_file_if_not_exit(filename):
  filename = Path(filename)
  filename.touch(exist_ok=True)

def do_all():
  ''' Main moderation method '''

  def save_changes(post_file, posts, users_file, users):
    ''' Save user and post files between runs '''
    posts_file.seek(0)
    json.dump(posts, posts_file)
    posts_file.truncate()
    users_file.seek(0)
    json.dump(users, users_file)
    users_file.truncate()

  logger = logging.getLogger('feedback_bot')
  logger.setLevel(logging.DEBUG)

  ch = logging.StreamHandler()
  ch.setLevel(logging.DEBUG)

  formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

  ch.setFormatter(formatter)

  logger.addHandler(ch)

  credentials = BotCredentials.from_config() # Loading credentials
  botConfig = BotConfig.from_config() # Loading configuration

  ''' Creating reddit praw client '''
  reddit = praw.Reddit(client_id=credentials.client_id,
                     client_secret=credentials.client_secret,
                     user_agent=credentials.user_agent,
                     username=credentials.bot_username,
                     password=credentials.bot_password)

  ''' Requesting target subreddit '''
  subreddit = reddit.subreddit(credentials.subreddit)

  logger.info('Starting moderation !')

  create_file_if_not_exit('users.json')
  create_file_if_not_exit('posts.json')

  with open('users.json', 'r+') as users_file, open('posts.json', 'r+') as posts_file:
    try:
      users = json.load(users_file)
    except JSONDecodeError:
      users = {}
    try:
      posts = json.load(posts_file)
    except JSONDecodeError:
      posts = {}
    if (not users) and (not posts) :
      firstRun = True
    else:
      firstRun = False

    submissions = []

    # Getting all the considered posts and storing them
    for temp_submission in subreddit.new(limit=botConfig.look_back_posts):
      submissions.append(temp_submission)

    # We iterate through the post in reverse chronological order so the score are up to date for new posts
    for submission in reversed(submissions):
      try:
        submission_author = submission.author.name
        logger.info("looking at submission {} from {}".format(submission.id, submission_author))
        if not submission.id in posts:
          remove = False
          remove_reason = ""
          posts[submission.id] = {}
          posts[submission.id]["feedbacks"] = []
          logger.info('New post found {}'.format(submission.id))
          if not submission_author in users:
            remove = True
            remove_reason = "lowScore"
            users[submission_author] = {}
            users[submission_author]["posts"] = 0
            users[submission_author]["feedbacks"] = 0
            author_history = users[submission_author]
          else:
            author_history = users[submission_author]
            compiled_regex = map(lambda x: re.compile(x), botConfig.filter_regex)

            if (author_history["posts"] + 1) * botConfig.score_needed > author_history["feedbacks"]:
              remove = True
              remove_reason = "lowScore"
            elif (any(map(lambda x: x.match(submission.url), compiled_regex))):
              logger.info(submission.url + 'Should be removed for matching forbidden regex')
              remove = True
              remove_reason = "forbidden_regex"
            else:
              author_history["posts"] = author_history["posts"] + 1
              users[submission_author] = author_history

          if firstRun:
            logger.info('recording the post for the first run')
            author_history["posts"] = author_history["posts"] + 1
            users[submission_author] = author_history
          elif remove:
            logger.info('Removing {} because {}'.format(submission.id, remove_reason))
            submission.mod.remove()
            if remove_reason == "lowScore":
              message = """
              Bleep bloop I'm a bot.\n
              Sorry your submission was removed.\n
              Your score is only {} and you need at least {} to post.\n
              You need to give feedback on at least {} track(s) and try again !\n
              *If you just gave enough feedback but your score wasn't credited, try again in a few minutes, the score update takes a little time*\n
              You can know your score at anytime by Direct Messaging me (the bot) with the word "SCORE" as a subject.\n
              Please repost your song once you have a score of {}.
              """.format(
                author_history["feedbacks"] - (author_history["posts"]) * botConfig.score_needed ,
                botConfig.score_needed,
                botConfig.score_needed - (author_history["feedbacks"] - (author_history["posts"]) * botConfig.score_needed),
                botConfig.score_needed
              )
            elif remove_reason == "forbidden_regex":
              message = """
              Bleep bloop I'm a bot.\n
              Sorry your submission was removed.\n
              I detected that you were linking to a playlist... we only allow you to post one song at a time.\n
              Playlists are difficult to give feedback on, and this goes against the 1 song - {} comment system\n
              Please repost your music one song at a time and try again !
              """.format(botConfig.score_needed)
            message = re.sub('\t', '',message)
            submission.mod.send_removal_message(message, title='submission removed', type='public')
          else:
            logger.info('Validating post {}'.format(submission.id))
            message = """
            Bleep bloop I'm a bot.\n
            Your submission was approved u/{}, thank you for posting !\n
            You can know your score at anytime by Direct Messaging me (the bot) with the word "SCORE" as a subject.
            """.format(submission_author)
            message = re.sub('\t', '',message)
            submission.reply(message)

        # Looking at comments from post to register potential new feedback
        comments = submission.comments.list()
        submission_feedbackers = posts[submission.id]["feedbacks"]
        for comment in comments:
          try:
            comment_author = comment.author.name
            if not comment_author == submission_author:
              if not comment_author in users:
                users[comment_author] = {}
                users[comment_author]["posts"] = 0
                users[comment_author]["feedbacks"] = 0
              if not comment_author in submission_feedbackers and comment.banned_by == None:
                logger.info("new feedback from {} registered on {}".format(comment_author, submission.id))
                if len(comment.body) < botConfig.minimum_comment_length:
                  logger.info("new feedback is too short to be good")
                  comment.reply_sort = 'new'
                  comment.refresh()
                  replies_authors = list(map(lambda x: x.author.name,comment.replies))
                  if not "IndieFeedbackBot" in replies_authors:
                    logger.info("first time seen, commenting to let the author know")
                    msg_comment = """
                    Bleep bloop I'm a bot.\n
                    Sorry, this comment won't count in your score, because it's not at least {} characters long :/\n
                    """.format(minimum_comment_length)
                    msg_comment = re.sub('\t', '', msg_comment)
                    comment.reply(msg_comment)
                else:
                  submission_feedbackers.append(comment_author)
                  users[comment_author]["feedbacks"] = users[comment_author]["feedbacks"] + 1
            feedbackers_set = set(submission_feedbackers)
            posts[submission.id]["feedbacks"] = list(feedbackers_set)
          except:
            logger.warning("comment registering went wrong {}".format(str(comment)))
      except Exception as e:
        logger.warning("submission registering went wrong {} {}".format(str(submission), e))

      save_changes(posts_file, posts, users_file, users)


    # Replying to DMs asking for score
    for message in reddit.inbox.unread(mark_read=True, limit=None):
      if isinstance(message, Message):
        message.mark_read()
        if message.subject.lower() == "score" or message.body.lower() == "score":
          dm_author = message.author
          print('Sending score DM to {}'.format(dm_author.name))
          if dm_author.name in users:
            dm_author_posts = users[dm_author.name]["posts"]
            dm_author_feedbacks = users[dm_author.name]["feedbacks"]
            message.reply('Your score currently is {}'.format(dm_author_feedbacks - dm_author_posts * botConfig.score_needed))
          else:
            pass
            message.reply('Your score currently is 0')

# Main execution, will check for a lock file to avoid concurrent bot execution which would be very bad
if __name__ == '__main__':
  logger = logging.getLogger('feedback_bot.main')
  logger.setLevel(logging.INFO)
  f = open ('lock', 'w')
  try: fcntl.lockf (f, fcntl.LOCK_EX | fcntl.LOCK_NB)
  except:
    print('[%s] Script already running.\n' % time.strftime ('%c') )
    sys.exit (-1)
  do_all()
