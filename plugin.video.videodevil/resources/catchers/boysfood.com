########################################################
#                Boysfood VideoCatcher                 #
########################################################
url=%s
########################################################
target=href="([^"]+)"> mp4</a>
extension=wmv
quality=standard
########################################################
target=file: '(http[^']+)'
extension=wmv
quality=standard
########################################################
target=<div id="xmoov-flv-player_va">\s+<iframe(?:[^"]+"){0,4}\s*src="([^"]+)"
forward=True
########################################################
url=%s
########################################################
target=file: '([^']+)'
extension=wmv
quality=fallback
########################################################
target=flashvars.quality_180p = "([^"]+180p[^"]+mp4[^"]+)";\s+(?=flashvars.(?:r|quality_\d+p) = ")
actions=unquote(match)
extension=mp4
info=180p
quality=low
########################################################
target=flashvars.quality_240p = "([^"]+240p[^"]+mp4[^"]+)";\s+(?=flashvars.(?:r|quality_\d+p) = ")
actions=unquote(match)
extension=mp4
info=240p
quality=low
########################################################
target=flashvars.quality_480p = "([^"]+480p[^"]+mp4[^"]+)";\s+(?=flashvars.(?:r|quality_\d+p) = ")
actions=unquote(match)
extension=mp4
info=480p
quality=standard
########################################################
target=flashvars.quality_720p = "([^"]+720p[^"]+mp4[^"]+)";\s+(?=flashvars.(?:r|quality_\d+p) = ")
actions=unquote(match)
extension=mp4
info=720p
quality=high
########################################################
target=flashvars.quality_1080p = "([^"]+1080p[^"]+mp4[^"]+)";\s+(?=flashvars.(?:r|quality_\d+p) = ")
actions=unquote(match)
extension=mp4
info=1080p
quality=high
########################################################
target=<param name="flashvars" value="main_url=([^&]+.html)%3Fembed%3Dview&
actions=unquote(match)
forward=True
########################################################
url=%s
########################################################
target=srv': '([^']+)',\s+'file': '([^']+flv)',
actions=join(/key=, match, group2)
quality=standard
########################################################
target=file': '([^']+.flv[^']+)'
actions=unquote(match)
quality=standard
########################################################
build=%s
########################################################
