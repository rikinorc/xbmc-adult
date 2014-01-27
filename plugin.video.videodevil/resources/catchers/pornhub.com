########################################################
#                 Pornhub VideoCatcher                 #
########################################################
url=%s
target=quality_180p":"([^"]+)"
actions=unquote(match)
dkey=video_title":"([^"]+)"
dkey_actions=replace(match, +,  )|unquote(match)
info=180p
quality=low
########################################################
target=quality_240p":"([^"]+)"
actions=unquote(match)
dkey=video_title":"([^"]+)"
dkey_actions=replace(match, +,  )|unquote(match)
info=240p
quality=low
########################################################
target=quality_360p":"([^"]+)"
actions=unquote(match)
dkey=video_title":"([^"]+)"
dkey_actions=replace(match, +,  )|unquote(match)
info=360p
quality=standard
########################################################
target=quality_480p":"([^"]+)"
actions=unquote(match)
dkey=video_title":"([^"]+)"
dkey_actions=replace(match, +,  )|unquote(match)
info=480p
quality=standard
########################################################
target=quality_720p":"([^"]+)"
actions=unquote(match)
dkey=video_title":"([^"]+)"
dkey_actions=replace(match, +,  )|unquote(match)
info=720p
quality=high
########################################################
target=quality_1080p":"([^"]+)"
actions=unquote(match)
dkey=video_title":"([^"]+)"
dkey_actions=replace(match, +,  )|unquote(match)
info=1080p
quality=high
build=%s
########################################################
