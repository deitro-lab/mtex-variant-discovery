import os
import configparser

def parse_config(config_path, config_defaults = None):
  config = configparser.ConfigParser()
  config['DEFAULT'] = dict()
  config_set = {}
  if config_defaults is not None:
    config.update(config_defaults)

  if os.path.exists(config_path):
    config.read(config_path)
    for sec in config.sections():
      config_set.update({sec: dict(config.items(sec))})
  else:
    print(f"Config file in {config_path} not found.")

  return config_set

def init_project(folders):
  for folder in folders:
    if not os.path.isdir(folder):
      print('initialize...')
      os.mkdir(folder)