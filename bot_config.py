from dataclasses import dataclass
from typing import List
import config

@dataclass
class BotConfig:
  ''' Class to store all bot applicationconfiguration '''
  score_needed: int # Score needed to be able to post
  look_back_posts: int # Number of posts to look back each time the bot runs
  minimum_comment_length: int
  filter_regex: List[str] # List of regex that if matched with the submission URL, will be filtered by the bot

  @classmethod
  def from_config(cls, file='./config/config.cfg'):
    cfg = config.Config(file)
    return cls(
      cfg['score_needed'],
      cfg['look_back_posts'],
      cfg['minimum_comment_length'],
      cfg['filter_regex']
    )
