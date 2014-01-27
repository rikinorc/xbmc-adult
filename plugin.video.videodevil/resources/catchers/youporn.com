########################################################
#                 Youporn VideoCatcher                 #
########################################################
url=%s
target=var\s+encryptedQuality240URL\s+=\s+'([^']+)';
dkey=video_title'\s+:\s+"([^"]+)",
dkey_actions=replace(match, &amp;, &)|unquote(match)
info=240p
quality=low
########################################################
target=var\s+encryptedQuality480URL\s+=\s+'([^']+)';
dkey=video_title'\s+:\s+"([^"]+)",
dkey_actions=replace(match, &amp;, &)|unquote(match)
info=480p
quality=standard
########################################################
target=var\s+encryptedQuality720URL\s+=\s+'([^']+)';
dkey=video_title'\s+:\s+"([^"]+)",
dkey_actions=replace(match, &amp;, &)|unquote(match)
info=720p
quality=high
build=%s
########################################################
