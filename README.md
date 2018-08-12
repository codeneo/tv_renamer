# TV Renamer

## Overview

A script to rename TV show episodes using [TVmaze API](https://www.tvmaze.com/api).

## Dependencies

This project is built in Python 2.7 however it should run in Python 3.x as well with a few minor tweaks. Apart from **requests** all the libraries used are part of the default python environment.

## Running the script

In a terminal or command window, execute:

```tv_renamer.py --path=top_level_directory_where_tv_show_is_present --maze-id=tv_maze_id_of_the_show```

For disabling interactive mode, use option `-ni or --non-interactive`, however this is not recommended. To display debug information, use option `-d or --debug`.

The script crawls the top directory and renames only video and subtitle files.
