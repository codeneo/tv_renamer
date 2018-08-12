# encoding: utf-8
import inspect, os, sys, re, requests, json
from collections import defaultdict
reload(sys) 
sys.setdefaultencoding('utf8')


def display_debug(expression, indent = "  ", debug = False):
   if not debug:
      return
   caller = inspect.stack()[1][3]
   print("{}[DEBUG] : [{}] : {}".format(indent, caller, expression))


def display_error(expression, indent = "  ", debug = False):
   if not debug:
      return
   caller = inspect.stack()[1][3]
   print("{}[ERROR] : [{}] : {}".format(indent, caller, expression))


def parse_local_episode_name(name, regex_list, debug = False):
   # season and episode
   rgx_match = None
   season = None
   episode = None
   for rgx in regex_list:
      rgx_match = rgx.match(name)
      if(rgx_match):
         display_debug("Local episode: [{}] matched with regex pattern: [{}]".format(name, rgx.pattern), debug=debug)
         season = int(rgx_match.group(1))
         episode = int(rgx_match.group(2))
         break
   if rgx_match is None:
      display_error("None of the regex in regex_list matched with local episode: [{}]. Please add a new regex.".format(name), debug=debug)
   
   if season is None:
      display_error("FAILED to find season for local episode: [{}]".format(name), debug=debug)
   else:
      display_debug("Found season: [{}] for local episode: [{}]".format(season, name), debug=debug)
   if episode is None:
      display_error("FAILED to find episode for local episode: [{}]".format(name), debug=debug)
   else:
      display_debug("Found episode: [{}] for local episode: [{}]".format(episode, name), debug=debug)

   # source
   sources = ["webrip", "web-rip", "web-dl", "web", "hdtv"]
   source = [src.upper() for src in sources if src in name.lower()]
   source = None if len(source) == 0 else source[0]
   if source is not None:      
      display_debug("Found source: [{}] for local episode: [{}]".format(source, name), debug=debug)

   return { "season" : season, "episode" : episode, "source" : source }

def get_local_episodes(series_path, debug = False):
   local_episodes = []
   valid_extensions = ('.mkv', '.mp4', '.m4v', '.srt', '.sub')
   _sddedd = re.compile('.*[sS]([0-9]?[0-9])[eE]([0-9]?[0-9]).*')
   _ddxdd = re.compile('.*([0-9]?[0-9])[xX]([0-9]?[0-9]).*')
   compiled_regex_list = [ _sddedd, _ddxdd ]
   series_path = os.path.abspath(series_path)
   display_debug("Crawling series_path: [{}]".format(series_path), debug=debug)
   for directory_path, sub_directories, files in os.walk(series_path):
      display_debug("Current directory: [{}]".format(directory_path), debug=debug)
      for file in files:
         if file.lower().endswith(valid_extensions):
            (basename, extension) = os.path.splitext(file)
            additional_information = parse_local_episode_name(name=basename, regex_list=compiled_regex_list, debug=debug)
            local_episode = {
               "directory_path" : directory_path,
               "basename" : basename,
               "extension" : extension,
               "season" : additional_information.get("season"),
               "episode" : additional_information.get("episode"),
               "source" : additional_information.get("source")
            }
            local_episodes.append(local_episode)

   display_debug("Successfully found [{}] local episodes plus subtitles to rename.".format(len(local_episodes)), debug=debug)
   return local_episodes


def get_remote_episodes(series_id, debug = False):
   remote_episodes = defaultdict(dict)
   url = "http://api.tvmaze.com/shows/{}/episodes".format(series_id)
   display_debug("[GET] {}".format(url), debug=debug)
   r = requests.get(url)
   episodes = json.loads(r.content)

   seasons = list(set([ ep.get("season") for ep in episodes]))
   display_debug("Found [{}] seasons and [{}] episodes for series_id: [{}]".format(len(seasons), len(episodes), series_id))

   for episode in episodes:
      remote_episodes[episode.get("season")][episode.get("number")] = episode.get("name")

   return remote_episodes


def rename_episodes(local_episodes, remote_episodes, interactive = True, debug = False):
   renamed_file_count = 0
   for local_episode in local_episodes:
      season = local_episode.get("season")
      episode = local_episode.get("episode")
      source = local_episode.get("source")
      directory_path = local_episode.get("directory_path")
      local_episode_basename = local_episode.get("basename")
      local_episode_extension = local_episode.get("extension")
      remote_episode_name = remote_episodes.get(season).get(episode)
      remote_episode_extension = local_episode_extension.lower()

      # Remove special characters from remote_episode_name
      remote_episode_name = remote_episode_name.replace('?', '') \
                                               .replace('!', '') \
                                               .replace('…', '') \
                                               .replace('–', '-') \
                                               .replace(':', ' -') \
                                               .replace('&', 'and')
      # Add season and episode to remote_episode_name
      remote_episode_name = "S{}E{} - {}".format(str(season).zfill(2), str(episode).zfill(2), remote_episode_name)

      # Add source if present
      if source is not None:
         remote_episode_name = "{} [{}]".format(remote_episode_name, source)

      # Join the extension
      local_episode_file = "".join( (local_episode_basename, local_episode_extension) )
      remote_episode_file = "".join( (remote_episode_name, remote_episode_extension) )
      
      # If interactive, confirm before renaming
      if interactive:
         question = "  RENAME  {} \n    TO    {} \n  [Y/n]   ".format(local_episode_file, remote_episode_file)
         option = raw_input(question)
         if option == 'n' or option == 'N':
            continue
      
      # Rename after joining the directory_path
      local_episode_file = os.path.join(directory_path, local_episode_file)
      remote_episode_file = os.path.join(directory_path, remote_episode_file)
      try:
         display_debug("RENAMING [{}] to [{}]".format(local_episode_file, remote_episode_file), debug=debug)
         if remote_episode_file != local_episode_file:
            os.rename(local_episode_file, remote_episode_file)
            renamed_file_count += 1
      except:
         display_error("FAILED to RENAME [{}] to [{}]".format(name), debug=debug)
         pass

   return (renamed_file_count, len(local_episodes))


def main():
   import argparse
   parser = argparse.ArgumentParser(description="Rename TV show episodes.")
   required_arguments = parser.add_argument_group('required arguments')
   required_arguments.add_argument("-p", "--path", help="the top level directory where the episodes are present", dest="path", required=True)
   required_arguments.add_argument("-mid", "--maze-id", help="the TVmaze id of the TV show", dest="maze_id", required=True)
   parser.add_argument("-ni", "--non-interactive", help="do not confirm before renaming", dest="non_interactive", action="store_false")
   parser.add_argument("-d", "--debug", help="display debug information", dest="debug", action="store_true")
   args = parser.parse_args()
   
   local_episodes = get_local_episodes(series_path=args.path, debug=args.debug)
   # print(json.dumps(local_episodes, indent=3, sort_keys=True))
   remote_episodes = get_remote_episodes(series_id=args.maze_id, debug=args.debug)
   # print(json.dumps(remote_episodes, indent=3, sort_keys=True))
   (renamed, total) = rename_episodes(local_episodes=local_episodes, remote_episodes=remote_episodes, interactive=args.non_interactive, debug=args.debug)
   print("\n\t{} out of {} files renamed successfully.".format(renamed, total))
   
   return


if __name__ == "__main__":
   main()

