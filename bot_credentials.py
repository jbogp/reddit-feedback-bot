from dataclasses import dataclass
import config

@dataclass
class BotCredentials:
  ''' Class to store all the login/auth needed for the bot '''
  client_id: str # Reddit application client_id
  client_secret: str # Reddit application client_secret
  user_agent: str # Reddit application user_agent

  bot_username: str # Username associated with the bot and the application
  bot_password: str # Password for the bot's reddit account

  subreddit: str # Subreddit to moderate

  @classmethod
  def from_config(cls, file='./config/credentials.cfg'):
    credentials_cfg = config.Config(file)
    return cls(
      credentials_cfg['client_id'],
      credentials_cfg['client_secret'],
      credentials_cfg['user_agent'],
      credentials_cfg['bot_username'],
      credentials_cfg['bot_password'],
      credentials_cfg['subreddit']
    )
