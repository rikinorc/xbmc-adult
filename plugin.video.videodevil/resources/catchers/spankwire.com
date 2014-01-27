########################################################
#                Spankwire VideoCatcher                #
########################################################
url=%s
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
build=%s
########################################################
